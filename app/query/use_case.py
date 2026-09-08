import dataclasses
from dataclasses import dataclass

from app.documents.models import DocumentStatus
from app.documents.service import DocumentService
from app.generation.base import LLM
from app.generation.citation_builder import Citation, CitationBuilder
from app.generation.context_builder import ContextBuilder
from app.generation.prompt_builder import PromptBuilder
from app.messages.service import ChatMessageService
from app.reranking.service import RerankingService
from app.retrieval.hybrid_retriever import HybridRetriever

NO_ANSWER_MESSAGE = (
    "The document does not contain enough "
    "information to answer this question."
)


class NoReadyDocumentsError(Exception):

    def __init__(self, session_id: str):
        super().__init__(
            f"No ready documents in session: {session_id}"
        )
        self.session_id = session_id


@dataclass
class QueryAnswer:
    answer: str
    citations: list[Citation]


class QuerySessionUseCase:

    def __init__(
        self,
        document_service: DocumentService,
        message_service: ChatMessageService,
        hybrid_retriever: HybridRetriever,
        reranking_service: RerankingService,
        context_builder: ContextBuilder,
        prompt_builder: PromptBuilder,
        llm: LLM,
        citation_builder: CitationBuilder,
        candidate_limit: int,
        limit: int,
    ):
        self.document_service = document_service
        self.message_service = message_service
        self.hybrid_retriever = hybrid_retriever
        self.reranking_service = reranking_service
        self.context_builder = context_builder
        self.prompt_builder = prompt_builder
        self.llm = llm
        self.citation_builder = citation_builder
        self.candidate_limit = candidate_limit
        self.limit = limit

    def execute(
        self,
        session_id: str,
        question: str,
        top_k: int,
    ) -> QueryAnswer:

        self._ensure_has_ready_document(session_id)

        answer = self._build_answer(
            session_id=session_id,
            question=question,
            top_k=top_k,
        )

        self.message_service.create(
            session_id=session_id,
            question=question,
            answer=answer.answer,
            citations=[
                dataclasses.asdict(citation)
                for citation in answer.citations
            ],
        )

        return answer

    def _build_answer(
        self,
        session_id: str,
        question: str,
        top_k: int,
    ) -> QueryAnswer:

        candidates = self.hybrid_retriever.retrieve(
            query=question,
            session_id=session_id,
            candidate_limit=self.candidate_limit,
            limit=self.limit,
        )

        if not candidates:
            return QueryAnswer(answer=NO_ANSWER_MESSAGE, citations=[])

        results = self.reranking_service.rerank(
            query=question,
            results=candidates,
            limit=top_k,
        )

        if not results:
            return QueryAnswer(answer=NO_ANSWER_MESSAGE, citations=[])

        context_items = self.context_builder.build(results)
        context = self.context_builder.format(context_items)

        prompt = self.prompt_builder.build(
            question=question,
            context=context,
        )

        answer = self.llm.generate(prompt)

        citations = self.citation_builder.build(results)

        return QueryAnswer(answer=answer, citations=citations)

    def _ensure_has_ready_document(self, session_id: str) -> None:
        documents = self.document_service.list_by_session(session_id)

        has_ready_document = any(
            document.status == DocumentStatus.READY
            for document in documents
        )

        if not has_ready_document:
            raise NoReadyDocumentsError(session_id)
