import dataclasses
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Iterator, Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.generation.errors import LLMError
from app.generation.registry import LLMRegistry, UnknownProviderError
from app.messages.models import MessageStatus
from app.messages.service import ChatMessageService, MessageNotFoundError
from app.query.background import BackgroundStreamRunner
from app.query.use_case import (
    UNEXPECTED_ERROR_MESSAGE,
    AnswerDelta,
    AnswerInProgressError,
    AnswerStarted,
    NoReadyDocumentsError,
    QueryEvent,
    QuerySessionUseCase,
)
from app.sessions.models import ChatSession
from app.sessions.title_service import SessionTitleService
from app.usage.service import UsageService


MAX_QUESTION_LENGTH = 2000


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=MAX_QUESTION_LENGTH)
    top_k: int = Field(default=5, ge=1, le=20)
    # Id from GET /llm/providers; the server default when omitted.
    provider: str | None = None


class CitationResponse(BaseModel):
    source_id: str
    chunk_id: str
    document_id: str

    page_start: int
    page_end: int

    section_number: str | None
    section_title: str | None
    text_snippet: str


class ChatMessageResponse(BaseModel):
    message_id: str
    question: str
    # For a pending message: the text generated so far.
    answer: str
    citations: list[CitationResponse]
    created_at: str
    feedback: Literal["like", "dislike"] | None = None
    status: MessageStatus = "done"
    error_message: str | None = None


class FeedbackRequest(BaseModel):
    feedback: Literal["like", "dislike"] | None = None


logger = logging.getLogger(__name__)

# Session titles, generated next to the answer (one short LLM call each).
_title_executor = ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix="title",
)

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
}


def format_sse(event: str, data: dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def format_query_event(event: QueryEvent) -> str:

    if isinstance(event, AnswerStarted):
        return format_sse("citations", {
            "citations": [
                dataclasses.asdict(citation)
                for citation in event.citations
            ],
        })

    if isinstance(event, AnswerDelta):
        return format_sse("delta", {"text": event.text})

    return format_sse("done", {"message_id": event.message_id})


def stream_query_events(
    events: Iterator[QueryEvent],
    generate_title: Callable[[], str | None],
) -> Iterator[str]:

    # The title needs only the question, so it is generated while the
    # answer is retrieved. It is then saved before the answer finishes,
    # which a client polling for the answer relies on to see both.
    title = _title_executor.submit(generate_title)

    # Headers are already sent once streaming starts, so failures are
    # reported as an "error" event instead of an HTTP status.
    try:
        for event in events:
            yield format_query_event(event)
    except LLMError as error:
        logger.warning(
            "LLM call failed: %s %s",
            error.provider,
            error.code,
            exc_info=error.__cause__ or error,
        )
        yield format_sse("error", {
            "code": error.code,
            "detail": error.user_message,
        })
        return
    except Exception:
        logger.exception("Query stream failed")
        yield format_sse("error", {
            "code": "internal_error",
            "detail": UNEXPECTED_ERROR_MESSAGE,
        })
        return

    generated_title = title.result()

    if generated_title:
        yield format_sse("title", {"title": generated_title})


def create_query_router(
    query_use_case: QuerySessionUseCase,
    llm_registry: LLMRegistry,
    message_service: ChatMessageService,
    title_service: SessionTitleService,
    get_owned_session: Callable[..., ChatSession],
    query_rate_limit: Callable[..., None],
    answer_runner: BackgroundStreamRunner,
    usage_service: UsageService,
) -> APIRouter:

    router = APIRouter()

    @router.get(
        "/{session_id}/messages",
        response_model=list[ChatMessageResponse],
    )
    def list_messages(
        session_id: str,
        session: ChatSession = Depends(get_owned_session),
    ):
        messages = message_service.list_by_session(session_id)

        return [
            ChatMessageResponse(
                message_id=message.message_id,
                question=message.question,
                answer=message.answer,
                citations=[
                    CitationResponse(**citation)
                    for citation in message.citations
                ],
                created_at=message.created_at.isoformat(),
                feedback=message.feedback,
                status=message.status,
                error_message=message.error_message,
            )
            for message in messages
        ]

    @router.patch(
        "/{session_id}/messages/{message_id}/feedback",
        status_code=204,
    )
    def set_message_feedback(
        session_id: str,
        message_id: str,
        request: FeedbackRequest,
        session: ChatSession = Depends(get_owned_session),
    ):
        try:
            message_service.set_feedback(
                session_id=session_id,
                message_id=message_id,
                feedback=request.feedback,
            )
        except MessageNotFoundError:
            raise HTTPException(
                status_code=404,
                detail="Message not found",
            )

    @router.post(
        "/{session_id}/query",
        dependencies=[Depends(query_rate_limit)],
    )
    def query_session(
        session_id: str,
        request: QueryRequest,
        session: ChatSession = Depends(get_owned_session),
    ) -> StreamingResponse:
        try:
            llm = llm_registry.get(request.provider).llm
        except UnknownProviderError:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Model provider '{request.provider}' is not available. "
                    "Please choose another model."
                ),
            )

        try:
            message = query_use_case.start(
                session_id=session_id,
                question=request.question,
            )
        except NoReadyDocumentsError:
            raise HTTPException(
                status_code=409,
                detail="No ready documents in this session.",
            )
        except AnswerInProgressError:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Câu hỏi trước trong đoạn chat này vẫn đang được trả lời. "
                    "Vui lòng đợi rồi hỏi tiếp."
                ),
            )

        usage_service.record(session.user_id, "query")

        events = query_use_case.stream(
            message=message,
            top_k=request.top_k,
            llm=llm,
        )

        # The answer (and title) are produced in the background so they
        # are saved even if the client disconnects before the end.
        return StreamingResponse(
            answer_runner.run(
                stream_query_events(
                    events=events,
                    generate_title=lambda: title_service.maybe_generate_title(
                        session=session,
                        question=request.question,
                        llm=llm,
                    ),
                )
            ),
            media_type="text/event-stream",
            headers=SSE_HEADERS,
        )

    return router
