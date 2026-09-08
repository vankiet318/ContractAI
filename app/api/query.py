from typing import Callable

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.messages.service import ChatMessageService
from app.query.use_case import NoReadyDocumentsError, QuerySessionUseCase
from app.sessions.models import ChatSession
from app.sessions.title_service import SessionTitleService


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
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


class QueryResponse(BaseModel):
    question: str
    answer: str
    citations: list[CitationResponse]
    session_title: str | None = None


class ChatMessageResponse(BaseModel):
    message_id: str
    question: str
    answer: str
    citations: list[CitationResponse]
    created_at: str


def create_query_router(
    query_use_case: QuerySessionUseCase,
    message_service: ChatMessageService,
    title_service: SessionTitleService,
    get_owned_session: Callable[..., ChatSession],
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
            )
            for message in messages
        ]

    @router.post(
        "/{session_id}/query",
        response_model=QueryResponse,
    )
    def query_session(
        session_id: str,
        request: QueryRequest,
        session: ChatSession = Depends(get_owned_session),
    ):
        try:
            result = query_use_case.execute(
                session_id=session_id,
                question=request.question,
                top_k=request.top_k,
            )
        except NoReadyDocumentsError:
            raise HTTPException(
                status_code=409,
                detail="No ready documents in this session.",
            )

        generated_title = title_service.maybe_generate_title(
            session=session,
            question=request.question,
        )

        citation_response = [
            CitationResponse(
                source_id=citation.source_id,
                chunk_id=citation.chunk_id,
                document_id=citation.document_id,
                page_start=citation.page_start,
                page_end=citation.page_end,
                section_number=citation.section_number,
                section_title=citation.section_title,
                text_snippet=citation.text_snippet,
            )
            for citation in result.citations
        ]

        return QueryResponse(
            question=request.question,
            answer=result.answer,
            citations=citation_response,
            session_title=generated_title,
        )

    return router
