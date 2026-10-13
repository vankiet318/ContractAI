from types import SimpleNamespace

import pytest

from app.documents.models import DocumentStatus
from app.generation.citation_builder import CitationBuilder
from app.generation.context_builder import ContextBuilder
from app.generation.errors import LLMError, LLMErrorCode
from app.generation.prompt_builder import PromptBuilder
from app.messages.service import INTERRUPTED_MESSAGE
from app.query.background import BackgroundStreamRunner
from app.query.use_case import AnswerInProgressError, QuerySessionUseCase
from app.retrieval.models import RetrievalResult

RESULT = RetrievalResult(
    chunk_id="c0",
    document_id="doc",
    text="Điều 1\n\nNội dung",
    score=0.9,
    page_start=1,
    page_end=1,
    section_number="1",
    section_title="Điều 1",
    metadata={},
)


class ScriptedLLM:

    def __init__(self, parts=("Xin ", "chào"), error=None):
        self.parts = parts
        self.error = error
        self.histories = []

    def generate_stream(self, prompt, history=None):
        self.histories.append(history)
        yield from self.parts

        if self.error:
            raise self.error


def build_use_case(message_service, llm) -> QuerySessionUseCase:
    return QuerySessionUseCase(
        document_service=SimpleNamespace(
            list_by_session=lambda session_id: [
                SimpleNamespace(status=DocumentStatus.READY)
            ],
        ),
        message_service=message_service,
        hybrid_retriever=SimpleNamespace(retrieve=lambda **kwargs: [RESULT]),
        reranking_service=SimpleNamespace(rerank=lambda **kwargs: [RESULT]),
        context_builder=ContextBuilder(),
        prompt_builder=PromptBuilder(),
        llm=llm,
        citation_builder=CitationBuilder(),
        candidate_limit=20,
        limit=20,
        min_relevance_score=0.05,
    )


def answer(use_case, question):
    return use_case.stream(
        message=use_case.start(session_id="s", question=question),
        top_k=5,
    )


def only_message(message_service):
    [message] = message_service.list_by_session("s")
    return message


def test_question_is_saved_as_pending_before_any_answer(message_service):
    use_case = build_use_case(message_service, ScriptedLLM())

    use_case.start(session_id="s", question="Phạt?")

    message = only_message(message_service)
    assert message.status == "pending"
    assert message.question == "Phạt?"


def test_pending_message_shows_the_answer_so_far(message_service):
    events = answer(build_use_case(message_service, ScriptedLLM()), "Phạt?")

    # Citations, then the first answer chunk.
    next(events)
    next(events)

    message = only_message(message_service)
    assert message.status == "pending"
    assert message.answer == "Xin "
    assert [citation["chunk_id"] for citation in message.citations] == ["c0"]


def test_second_question_waits_for_the_pending_answer(message_service):
    use_case = build_use_case(message_service, ScriptedLLM())
    use_case.start(session_id="s", question="Câu 1")

    with pytest.raises(AnswerInProgressError):
        use_case.start(session_id="s", question="Câu 2")


def test_llm_failure_marks_the_message_failed(message_service):
    error = LLMError("Groq", LLMErrorCode.RATE_LIMITED)
    events = answer(build_use_case(message_service, ScriptedLLM(error=error)), "Phạt?")

    with pytest.raises(LLMError):
        list(events)

    saved = only_message(message_service)
    assert saved.status == "failed"
    assert saved.error_message == error.user_message


def test_stream_closed_early_marks_the_message_interrupted(message_service):
    events = answer(build_use_case(message_service, ScriptedLLM()), "Phạt?")

    next(events)
    events.close()

    saved = only_message(message_service)
    assert saved.status == "failed"
    assert saved.error_message == INTERRUPTED_MESSAGE


def test_history_skips_failed_and_pending_messages(message_service):
    failing = build_use_case(
        message_service,
        ScriptedLLM(error=LLMError("Groq", LLMErrorCode.TIMEOUT)),
    )

    with pytest.raises(LLMError):
        list(answer(failing, "Lỗi"))

    llm = ScriptedLLM()
    use_case = build_use_case(message_service, llm)
    list(answer(use_case, "Câu 1"))
    list(answer(use_case, "Câu 2"))

    # The second answer sees only the first finished turn: not the failed
    # one, nor its own pending question.
    assert [turn.question for turn in llm.histories[-1]] == ["Câu 1"]


def test_restart_fails_answers_left_pending(message_service):
    build_use_case(message_service, ScriptedLLM()).start(
        session_id="s", question="Phạt?"
    )

    assert message_service.fail_interrupted() == 1
    assert only_message(message_service).status == "failed"


def test_answer_is_saved_after_the_client_disconnects(message_service):
    events = answer(build_use_case(message_service, ScriptedLLM()), "Phạt?")
    runner = BackgroundStreamRunner(max_workers=1)

    # The client reads one event, then goes away.
    received = runner.run(events)
    next(received)
    received.close()

    runner.executor.shutdown(wait=True)

    saved = only_message(message_service)
    assert saved.status == "done"
    assert saved.answer == "Xin chào"
