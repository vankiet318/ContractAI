from types import SimpleNamespace

from app.documents.models import DocumentStatus
from app.generation.citation_builder import CitationBuilder
from app.generation.context_builder import ContextBuilder
from app.generation.prompt_builder import PromptBuilder
from app.query.use_case import (
    NO_ANSWER_MESSAGE,
    AnswerCompleted,
    AnswerDelta,
    AnswerStarted,
    QuerySessionUseCase,
)
from app.retrieval.models import RetrievalResult

MIN_SCORE = 0.05


def make_result(chunk_id: str, score: float) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk_id,
        document_id="doc",
        text=f"Điều 1\n\nNội dung {chunk_id}",
        score=score,
        page_start=1,
        page_end=1,
        section_number="1",
        section_title="Điều 1",
        metadata={},
    )


class FakeLLM:

    def __init__(self):
        self.calls = 0

    def generate_stream(self, prompt, history=None):
        self.calls += 1
        yield "Phạt "
        yield "0,05%"


def build_use_case(rerank_scores: list[float], llm: FakeLLM) -> QuerySessionUseCase:

    results = [
        make_result(f"c{index}", score)
        for index, score in enumerate(rerank_scores)
    ]

    return QuerySessionUseCase(
        document_service=SimpleNamespace(
            list_by_session=lambda session_id: [
                SimpleNamespace(status=DocumentStatus.READY)
            ],
        ),
        message_service=SimpleNamespace(
            list_by_session=lambda session_id: [],
            create=lambda **kwargs: SimpleNamespace(message_id="m1", **kwargs),
        ),
        hybrid_retriever=SimpleNamespace(retrieve=lambda **kwargs: results),
        reranking_service=SimpleNamespace(rerank=lambda **kwargs: results),
        context_builder=ContextBuilder(),
        prompt_builder=PromptBuilder(),
        llm=llm,
        citation_builder=CitationBuilder(),
        candidate_limit=20,
        limit=20,
        min_relevance_score=MIN_SCORE,
    )


def collect(use_case: QuerySessionUseCase, question: str):
    events = list(use_case.stream(session_id="s", question=question, top_k=5))

    started = events[0]
    text = "".join(event.text for event in events if isinstance(event, AnswerDelta))
    completed = events[-1]

    assert isinstance(started, AnswerStarted)
    assert isinstance(completed, AnswerCompleted)

    return started.citations, text, completed


def test_off_topic_question_skips_llm_and_citations():

    llm = FakeLLM()
    use_case = build_use_case([0.01, 0.002], llm)

    citations, text, _ = collect(use_case, "Thời tiết hôm nay?")

    assert text == NO_ANSWER_MESSAGE
    assert citations == []
    assert llm.calls == 0


def test_only_relevant_chunks_are_cited():

    llm = FakeLLM()
    use_case = build_use_case([0.9, 0.3, 0.01], llm)

    citations, text, completed = collect(use_case, "Phạt chậm thanh toán?")

    assert llm.calls == 1
    assert text == "Phạt 0,05%"
    assert completed.message_id == "m1"
    assert [citation.chunk_id for citation in citations] == ["c0", "c1"]
