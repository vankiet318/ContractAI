import json
import time

from app.api.query import UNEXPECTED_ERROR_MESSAGE, stream_query_events
from app.generation.errors import LLMError, LLMErrorCode
from app.query.use_case import AnswerCompleted, AnswerDelta, AnswerStarted


def parse(raw_events: list[str]) -> list[tuple[str, dict]]:
    parsed = []

    for raw in raw_events:
        event_line, data_line = raw.strip().split("\n")
        parsed.append((
            event_line.removeprefix("event: "),
            json.loads(data_line.removeprefix("data: ")),
        ))

    return parsed


def test_events_are_sent_in_order_with_title_last():

    events = iter([
        AnswerStarted(citations=[]),
        AnswerDelta(text="Xin "),
        AnswerDelta(text="chào"),
        AnswerCompleted(message_id="m1"),
    ])

    stream = stream_query_events(events, generate_title=lambda: "Phạt vi phạm")

    assert parse(list(stream)) == [
        ("citations", {"citations": []}),
        ("delta", {"text": "Xin "}),
        ("delta", {"text": "chào"}),
        ("done", {"message_id": "m1"}),
        ("title", {"title": "Phạt vi phạm"}),
    ]


def test_failure_mid_stream_becomes_error_event_without_title():

    def failing_events():
        yield AnswerStarted(citations=[])
        raise RuntimeError("Gemini down")

    stream = stream_query_events(
        failing_events(),
        generate_title=lambda: "Phạt vi phạm",
    )

    assert [name for name, _ in parse(list(stream))] == ["citations", "error"]


def test_title_is_generated_while_the_answer_is_retrieved():

    title_started = []

    def generate_title():
        title_started.append(True)
        return "Phạt vi phạm"

    def events():
        # Give the title thread a moment to pick the job up.
        for _ in range(100):
            if title_started:
                break
            time.sleep(0.01)

        assert title_started, "title should start before the answer ends"
        yield AnswerStarted(citations=[])
        yield AnswerCompleted(message_id="m1")

    stream = stream_query_events(events(), generate_title=generate_title)

    assert parse(list(stream))[-1] == ("title", {"title": "Phạt vi phạm"})


def test_llm_error_is_reported_with_its_own_message():

    def failing_events():
        yield AnswerStarted(citations=[])
        raise LLMError("Gemini", LLMErrorCode.RATE_LIMITED)

    stream = stream_query_events(failing_events(), generate_title=lambda: None)

    name, data = parse(list(stream))[-1]

    assert name == "error"
    assert data["code"] == "rate_limited"
    assert data["detail"].startswith("Gemini has run out of requests")


def test_unexpected_error_gets_a_generic_message():

    def failing_events():
        raise RuntimeError("Qdrant down")
        yield

    stream = stream_query_events(failing_events(), generate_title=lambda: None)

    assert parse(list(stream)) == [
        ("error", {"code": "internal_error", "detail": UNEXPECTED_ERROR_MESSAGE}),
    ]
