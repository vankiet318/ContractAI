import dataclasses
import json
import logging
from typing import Any, Callable, Iterator, Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.messages.service import ChatMessageService, MessageNotFoundError
from app.query.use_case import (
    AnswerDelta,
    AnswerStarted,
    NoReadyDocumentsError,
    QueryEvent,
    QuerySessionUseCase,
)
from app.sessions.models import ChatSession
from app.sessions.title_service import SessionTitleService


MAX_QUESTION_LENGTH = 2000


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=MAX_QUESTION_LENGTH)
    top_k: int = Field(default=5, ge=1, le=20)


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
    answer: str
    citations: list[CitationResponse]
    created_at: str
    feedback: Literal["like", "dislike"] | None = None


class FeedbackRequest(BaseModel):
    feedback: Literal["like", "dislike"] | None = None


logger = logging.getLogger(__name__)

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

    # Headers are already sent once streaming starts, so failures are
    # reported as an "error" event instead of an HTTP status.
    try:
        for event in events:
            yield format_query_event(event)
    except Exception:
        logger.exception("Query stream failed")
        yield format_sse("error", {"detail": "Query failed"})
        return

    title = generate_title()

    if title:
        yield format_sse("title", {"title": title})


def create_query_router(
    query_use_case: QuerySessionUseCase,
    message_service: ChatMessageService,
    title_service: SessionTitleService,
    get_owned_session: Callable[..., ChatSession],
    query_rate_limit: Callable[..., None],
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
            events = query_use_case.stream(
                session_id=session_id,
                question=request.question,
                top_k=request.top_k,
            )
        except NoReadyDocumentsError:
            raise HTTPException(
                status_code=409,
                detail="No ready documents in this session.",
            )

        return StreamingResponse(
            stream_query_events(
                events=events,
                generate_title=lambda: title_service.maybe_generate_title(
                    session=session,
                    question=request.question,
                ),
            ),
            media_type="text/event-stream",
            headers=SSE_HEADERS,
        )

    return router
