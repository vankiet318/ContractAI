import dataclasses
from dataclasses import dataclass
from typing import Iterator

from app.documents.models import DocumentStatus
from app.documents.service import DocumentService
from app.generation.base import LLM, ConversationTurn
from app.generation.citation_builder import Citation, CitationBuilder
from app.generation.context_builder import ContextBuilder
from app.generation.errors import LLMError
from app.generation.prompt_builder import PromptBuilder
from app.messages.models import ChatMessage
from app.messages.service import INTERRUPTED_MESSAGE, ChatMessageService
from app.reranking.service import RerankingService
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.models import RetrievalResult

NO_ANSWER_MESSAGE = (
    "Mình không tìm thấy nội dung liên quan trong tài liệu để trả lời "
    "câu hỏi này. Bạn hãy hỏi về các điều khoản, nghĩa vụ, thời hạn "
    "hoặc thông tin khác có trong hợp đồng."
)

UNEXPECTED_ERROR_MESSAGE = (
    "Something went wrong while answering your question. Please try again."
)


class NoReadyDocumentsError(Exception):

    def __init__(self, session_id: str):
        super().__init__(
            f"No ready documents in session: {session_id}"
        )
        self.session_id = session_id


class AnswerInProgressError(Exception):

    def __init__(self, session_id: str):
        super().__init__(
            f"An answer is still being generated in session: {session_id}"
        )
        self.session_id = session_id


@dataclass
class AnswerStarted:
    citations: list[Citation]


@dataclass
class AnswerDelta:
    text: str


@dataclass
class AnswerCompleted:
    message_id: str


QueryEvent = AnswerStarted | AnswerDelta | AnswerCompleted


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
        min_relevance_score: float,
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
        self.min_relevance_score = min_relevance_score
        self.max_history_turns = max_history_turns

    def start(self, session_id: str, question: str) -> ChatMessage:
        """
        Saves the question as a pending message. Runs before streaming so
        the caller can still reject the request with a normal error
        response.
        """

        self._ensure_has_ready_document(session_id)

        # One answer at a time per session: the next one's history must
        # include this one.
        if self.message_service.has_pending(session_id):
            raise AnswerInProgressError(session_id)

        return self.message_service.start(
            session_id=session_id,
            question=question,
        )

    def stream(
        self,
        message: ChatMessage,
        top_k: int,
        llm: LLM | None = None,
    ) -> Iterator[QueryEvent]:
        """
        Answers a message from start(). The message always ends done or
        failed, whichever way the stream ends. llm overrides the default
        model for this query (the user's pick).
        """

        message_id = message.message_id

        try:
            yield from self._stream_answer(
                message=message,
                top_k=top_k,
                llm=llm or self.llm,
            )
        except LLMError as error:
            self.message_service.fail(message_id, error.user_message)
            raise
        except Exception:
            self.message_service.fail(message_id, UNEXPECTED_ERROR_MESSAGE)
            raise
        finally:
            # Covers a stream closed before it finished; no-op otherwise.
            self.message_service.fail(message_id, INTERRUPTED_MESSAGE)

    def _stream_answer(
        self,
        message: ChatMessage,
        top_k: int,
        llm: LLM,
    ) -> Iterator[QueryEvent]:

        session_id = message.session_id
        message_id = message.message_id

        results = self._find_relevant_results(
            session_id=session_id,
            question=message.question,
            top_k=top_k,
        )

        citations = self.citation_builder.build(results)
        citation_dicts = [
            dataclasses.asdict(citation)
            for citation in citations
        ]

        self.message_service.set_citations(message_id, citation_dicts)

        yield AnswerStarted(citations=citations)

        answer_parts = []

        for text in self._generate_answer(
            session_id, message.question, results, llm
        ):
            answer_parts.append(text)
            self.message_service.append_answer(message_id, text)
            yield AnswerDelta(text=text)

        self.message_service.complete(
            message_id=message_id,
            answer="".join(answer_parts),
            citations=citation_dicts,
        )

        yield AnswerCompleted(message_id=message_id)

    def _generate_answer(
        self,
        session_id: str,
        question: str,
        results: list[RetrievalResult],
        llm: LLM,
    ) -> Iterator[str]:

        # Off-topic questions end here: no LLM call and no citations
        # pointing at unrelated chunks.
        if not results:
            yield NO_ANSWER_MESSAGE
            return

        context_items = self.context_builder.build(results)

        prompt = self.prompt_builder.build(
            question=question,
            context=self.context_builder.format(context_items),
        )

        yield from llm.generate_stream(
            prompt,
            history=self._load_history(session_id),
        )

    def _find_relevant_results(
        self,
        session_id: str,
        question: str,
        top_k: int,
    ) -> list[RetrievalResult]:

        candidates = self.hybrid_retriever.retrieve(
            query=question,
            session_id=session_id,
            candidate_limit=self.candidate_limit,
            limit=self.limit,
        )

        reranked = self.reranking_service.rerank(
            query=question,
            results=candidates,
            limit=top_k,
        )

        return [
            result
            for result in reranked
            if result.score >= self.min_relevance_score
        ]

    def _load_history(self, session_id: str) -> list[ConversationTurn]:
        # Only finished answers: not the pending question being answered
        # now, nor failed ones.
        past_messages = [
            message
            for message in self.message_service.list_by_session(session_id)
            if message.status == "done"
        ]

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
