from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.query import create_query_router
from app.generation.registry import LLMProvider, LLMRegistry
from app.query.use_case import (
    AnswerCompleted,
    AnswerDelta,
    AnswerStarted,
    NoReadyDocumentsError,
)


class FakeUseCase:

    def __init__(self, has_documents: bool):
        self.has_documents = has_documents
        self.llm = None

    def stream(self, session_id, question, top_k, llm=None):
        self.llm = llm

        if not self.has_documents:
            raise NoReadyDocumentsError(session_id)

        return iter([
            AnswerStarted(citations=[]),
            AnswerDelta(text="Trả lời"),
            AnswerCompleted(message_id="m1"),
        ])


GEMINI_LLM = object()
GROQ_LLM = object()


def build_client(
    has_documents: bool,
    use_case: FakeUseCase | None = None,
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
            get_owned_session=lambda: SimpleNamespace(session_id="s"),
            query_rate_limit=lambda: None,
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
