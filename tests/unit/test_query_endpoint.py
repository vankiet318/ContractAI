from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.query import create_query_router
from app.query.use_case import (
    AnswerCompleted,
    AnswerDelta,
    AnswerStarted,
    NoReadyDocumentsError,
)


class FakeUseCase:

    def __init__(self, has_documents: bool):
        self.has_documents = has_documents

    def stream(self, session_id, question, top_k):
        if not self.has_documents:
            raise NoReadyDocumentsError(session_id)

        return iter([
            AnswerStarted(citations=[]),
            AnswerDelta(text="Trả lời"),
            AnswerCompleted(message_id="m1"),
        ])


def build_client(has_documents: bool) -> TestClient:
    app = FastAPI()

    app.include_router(
        create_query_router(
            query_use_case=FakeUseCase(has_documents),
            message_service=SimpleNamespace(),
            title_service=SimpleNamespace(maybe_generate_title=lambda **kwargs: None),
            get_owned_session=lambda: SimpleNamespace(session_id="s"),
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
