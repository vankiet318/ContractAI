import json

from app.api.query import stream_query_events
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

    titles_requested = []

    stream = stream_query_events(
        failing_events(),
        generate_title=lambda: titles_requested.append(1),
    )

    assert [name for name, _ in parse(list(stream))] == ["citations", "error"]
    assert titles_requested == []
