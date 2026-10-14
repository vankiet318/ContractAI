from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.query import create_query_router
from app.generation.registry import LLMProvider, LLMRegistry
from app.query.background import BackgroundStreamRunner
from app.query.use_case import (
    AnswerCompleted,
    AnswerDelta,
    AnswerInProgressError,
    AnswerStarted,
    NoReadyDocumentsError,
)


class FakeUseCase:

    def __init__(self, has_documents: bool, answer_in_progress: bool = False):
        self.has_documents = has_documents
        self.answer_in_progress = answer_in_progress
        self.llm = None

    def start(self, session_id, question):
        if not self.has_documents:
            raise NoReadyDocumentsError(session_id)

        if self.answer_in_progress:
            raise AnswerInProgressError(session_id)

        return SimpleNamespace(message_id="m1", session_id=session_id)

    def stream(self, message, top_k, llm=None):
        self.llm = llm

        return iter([
            AnswerStarted(citations=[]),
            AnswerDelta(text="Trả lời"),
            AnswerCompleted(message_id=message.message_id),
        ])


GEMINI_LLM = object()
GROQ_LLM = object()


class FakeUsageService:

    def __init__(self):
        self.recorded = []

    def record(self, user_id, kind):
        self.recorded.append((user_id, kind))


def build_client(
    has_documents: bool,
    use_case: FakeUseCase | None = None,
    usage_service: FakeUsageService | None = None,
) -> TestClient:
    app = FastAPI()

    registry = LLMRegistry(
        providers=[
            LLMProvider("gemini", "Gemini", "gemini-x", GEMINI_LLM),
            LLMProvider("groq", "Groq", "openai/gpt-oss-120b", GROQ_LLM),
        ],
        default_id="gemini",
    )

    app.include_router(
        create_query_router(
            query_use_case=use_case or FakeUseCase(has_documents),
            llm_registry=registry,
            message_service=SimpleNamespace(),
            title_service=SimpleNamespace(maybe_generate_title=lambda **kwargs: None),
            get_owned_session=lambda: SimpleNamespace(session_id="s", user_id="u"),
            query_rate_limit=lambda: None,
            answer_runner=BackgroundStreamRunner(max_workers=2),
            usage_service=usage_service or FakeUsageService(),
        ),
        prefix="/sessions",
    )

    return TestClient(app)


def test_query_streams_server_sent_events():
    response = build_client(has_documents=True).post(
        "/sessions/s/query",
        json={"question": "Phạt vi phạm?"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.text.count("event: ") == 3
    assert 'event: done\ndata: {"message_id": "m1"}' in response.text


def test_query_without_ready_documents_is_rejected_before_streaming():
    response = build_client(has_documents=False).post(
        "/sessions/s/query",
        json={"question": "Phạt vi phạm?"},
    )

    assert response.status_code == 409


def test_query_while_previous_answer_is_pending_is_rejected():
    use_case = FakeUseCase(has_documents=True, answer_in_progress=True)

    response = build_client(has_documents=True, use_case=use_case).post(
        "/sessions/s/query",
        json={"question": "Phạt vi phạm?"},
    )

    assert response.status_code == 409
    assert "đang được trả lời" in response.json()["detail"]


def test_query_uses_the_chosen_provider():
    use_case = FakeUseCase(has_documents=True)

    build_client(has_documents=True, use_case=use_case).post(
        "/sessions/s/query",
        json={"question": "Phạt vi phạm?", "provider": "groq"},
    )

    assert use_case.llm is GROQ_LLM


def test_query_without_provider_uses_the_default():
    use_case = FakeUseCase(has_documents=True)

    build_client(has_documents=True, use_case=use_case).post(
        "/sessions/s/query",
        json={"question": "Phạt vi phạm?"},
    )

    assert use_case.llm is GEMINI_LLM


def test_query_with_unknown_provider_is_rejected():
    response = build_client(has_documents=True).post(
        "/sessions/s/query",
        json={"question": "Phạt vi phạm?", "provider": "openai"},
    )

    assert response.status_code == 400


def test_accepted_query_is_counted_as_usage_of_the_session_owner():
    usage = FakeUsageService()

    build_client(has_documents=True, usage_service=usage).post(
        "/sessions/s/query",
        json={"question": "Phạt vi phạm?"},
    )

    assert usage.recorded == [("u", "query")]


def test_rejected_query_is_not_counted_as_usage():
    usage = FakeUsageService()

    build_client(has_documents=False, usage_service=usage).post(
        "/sessions/s/query",
        json={"question": "Phạt vi phạm?"},
    )

    assert usage.recorded == []
