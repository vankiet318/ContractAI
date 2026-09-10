import dataclasses
from dataclasses import dataclass

from app.documents.models import DocumentStatus
from app.documents.service import DocumentService
from app.generation.base import LLM, ConversationTurn
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
    message_id: str
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
        max_history_turns: int = 5,
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
        self.max_history_turns = max_history_turns

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

        saved_message = self.message_service.create(
            session_id=session_id,
            question=question,
            answer=answer.answer,
            citations=[
                dataclasses.asdict(citation)
                for citation in answer.citations
            ],
        )

        answer.message_id = saved_message.message_id

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
            return QueryAnswer(
                message_id="",
                answer=NO_ANSWER_MESSAGE,
                citations=[],
            )

        results = self.reranking_service.rerank(
            query=question,
            results=candidates,
            limit=top_k,
        )

        if not results:
            return QueryAnswer(
                message_id="",
                answer=NO_ANSWER_MESSAGE,
                citations=[],
            )

        context_items = self.context_builder.build(results)
        context = self.context_builder.format(context_items)

        prompt = self.prompt_builder.build(
            question=question,
            context=context,
        )

        history = self._load_history(session_id)

        answer = self.llm.generate(prompt, history=history)

        citations = self.citation_builder.build(results)

        return QueryAnswer(message_id="", answer=answer, citations=citations)

    def _load_history(self, session_id: str) -> list[ConversationTurn]:
        past_messages = self.message_service.list_by_session(session_id)

        recent_messages = past_messages[-self.max_history_turns:]

        return [
            ConversationTurn(question=message.question, answer=message.answer)
            for message in recent_messages
        ]

    def _ensure_has_ready_document(self, session_id: str) -> None:
        documents = self.document_service.list_by_session(session_id)

        has_ready_document = any(
            document.status == DocumentStatus.READY
            for document in documents
        )

        if not has_ready_document:
            raise NoReadyDocumentsError(session_id)
