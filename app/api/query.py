from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.documents.models import DocumentStatus
from app.documents.repository import DocumentRepository
from app.retrieval.hybrid_retriever import HybridRetriever
from app.reranking.service import RerankingService
from app.generation.context_builder import ContextBuilder
from app.generation.prompt_builder import PromptBuilder
from app.generation.base import LLM
from app.generation.citation_builder import CitationBuilder


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class CitationResponse(BaseModel):
    source_id: str
    chunk_id: str

    page_start: int
    page_end: int

    section_number: str | None
    section_title: str | None


class QueryResponse(BaseModel):
    question: str
    answer: str
    citations: list[CitationResponse]


def create_query_router(
    document_repository: DocumentRepository,
    hybrid_retriever: HybridRetriever,
    reranking_service: RerankingService,
    context_builder: ContextBuilder,
    prompt_builder: PromptBuilder,
    llm: LLM,
    citation_builder: CitationBuilder,
) -> APIRouter:

    router = APIRouter()

    @router.post(
        "/{document_id}/query",
        response_model=QueryResponse,
    )
    def query_document(
        document_id: str,
        request: QueryRequest,
    ):

        # --------------------------------
        # 1. Check document
        # --------------------------------

        document = document_repository.get(document_id)

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="Document not found.",
            )

        if document.status != DocumentStatus.READY:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Document is not ready. "
                    f"Current status: {document.status.value}"
                ),
            )

        # --------------------------------
        # 2. Hybrid retrieval
        # --------------------------------

        candidates = hybrid_retriever.retrieve(
            query=request.question,
            document_id=document_id,
            candidate_limit=20,
            limit=20,
        )

        if not candidates:
            return QueryResponse(
                question=request.question,
                answer=(
                    "The document does not contain enough "
                    "information to answer this question."
                ),
                citations=[],
            )

        # --------------------------------
        # 3. Reranking
        # --------------------------------

        results = reranking_service.rerank(
            query=request.question,
            results=candidates,
            limit=request.top_k,
        )

        if not results:
            return QueryResponse(
                question=request.question,
                answer=(
                    "The document does not contain enough "
                    "information to answer this question."
                ),
                citations=[],
            )

        # --------------------------------
        # 4. Build context
        # --------------------------------

        context_items = context_builder.build(results)

        context = context_builder.format(context_items)

        # --------------------------------
        # 5. Build prompt
        # --------------------------------

        prompt = prompt_builder.build(
            question=request.question,
            context=context,
        )

        # --------------------------------
        # 6. Generate answer
        # --------------------------------

        answer = llm.generate(prompt)

        # --------------------------------
        # 7. Build citations
        # --------------------------------

        citations = citation_builder.build(results)

        citation_response = [
            CitationResponse(
                source_id=citation.source_id,
                chunk_id=citation.chunk_id,
                page_start=citation.page_start,
                page_end=citation.page_end,
                section_number=citation.section_number,
                section_title=citation.section_title,
            )
            for citation in citations
        ]

        return QueryResponse(
            question=request.question,
            answer=answer,
            citations=citation_response,
        )

    return router