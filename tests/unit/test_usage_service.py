from datetime import date, datetime, timedelta, timezone

from app.usage.models import UsageEvent
from app.usage.service import UsageService

VIETNAM = timezone(timedelta(hours=7))


def server_time(aware: datetime) -> datetime:
    """The naive server-local time the app would store for `aware`."""
    return aware.astimezone().replace(tzinfo=None)


class InMemoryUsageRepository:

    def __init__(self, events=()):
        self.events = list(events)

    def create(self, event):
        self.events.append(event)

    def list_since(self, since, user_id=None):
        return [
            event
            for event in self.events
            if event.created_at >= since
            and (user_id is None or event.user_id == user_id)
        ]


def event(user_id, kind, aware_time):
    return UsageEvent(
        event_id=f"{user_id}-{kind}-{aware_time.isoformat()}",
        user_id=user_id,
        kind=kind,
        created_at=server_time(aware_time),
    )


NOW = datetime(2026, 10, 14, 15, 0, tzinfo=VIETNAM)


def build(events=()):
    return UsageService(
        repository=InMemoryUsageRepository(events),
        timezone=VIETNAM,
        clock=lambda: server_time(NOW),
    )


def test_daily_covers_every_day_of_the_window_oldest_first():
    daily = build().daily(days=3)

    assert [day.date for day in daily] == [
        date(2026, 10, 12),
        date(2026, 10, 13),
        date(2026, 10, 14),
    ]
    assert all(day.queries == 0 and day.uploads == 0 for day in daily)


def test_daily_counts_queries_and_uploads_per_day():
    service = build([
        event("u1", "query", datetime(2026, 10, 13, 9, tzinfo=VIETNAM)),
        event("u1", "query", datetime(2026, 10, 14, 9, tzinfo=VIETNAM)),
        event("u2", "query", datetime(2026, 10, 14, 10, tzinfo=VIETNAM)),
        event("u2", "upload", datetime(2026, 10, 14, 11, tzinfo=VIETNAM)),
    ])

    daily = service.daily(days=2)

    assert (daily[0].queries, daily[0].uploads) == (1, 0)
    assert (daily[1].queries, daily[1].uploads) == (2, 1)


def test_days_are_counted_in_the_configured_time_zone():
    # 06:00 in Vietnam is still the previous day in UTC.
    service = build([
        event("u1", "query", datetime(2026, 10, 14, 6, tzinfo=VIETNAM)),
    ])

    daily = service.daily(days=2)

    assert daily[1].date == date(2026, 10, 14)
    assert daily[1].queries == 1


def test_events_before_the_window_are_ignored():
    service = build([
        event("u1", "query", datetime(2026, 10, 12, 23, 59, tzinfo=VIETNAM)),
        event("u1", "query", datetime(2026, 10, 13, 0, 0, tzinfo=VIETNAM)),
    ])

    assert sum(day.queries for day in service.daily(days=2)) == 1


def test_daily_for_one_user_ignores_other_users():
    service = build([
        event("u1", "query", datetime(2026, 10, 14, 9, tzinfo=VIETNAM)),
        event("u2", "query", datetime(2026, 10, 14, 9, tzinfo=VIETNAM)),
    ])

    assert service.daily(days=1, user_id="u1")[0].queries == 1


def test_counts_by_user():
    service = build([
        event("u1", "query", datetime(2026, 10, 14, 9, tzinfo=VIETNAM)),
        event("u1", "upload", datetime(2026, 10, 14, 9, tzinfo=VIETNAM)),
        event("u1", "upload", datetime(2026, 10, 14, 10, tzinfo=VIETNAM)),
        event("u2", "query", datetime(2026, 10, 14, 9, tzinfo=VIETNAM)),
    ])

    counts = service.counts_by_user(days=1)

    assert (counts["u1"].queries, counts["u1"].uploads) == (1, 2)
    assert (counts["u2"].queries, counts["u2"].uploads) == (1, 0)


def test_record_stores_an_event():
    service = build()

    service.record("u1", "upload")

    assert [(e.user_id, e.kind) for e in service.repository.events] == [
        ("u1", "upload"),
    ]


def test_record_failure_does_not_raise():
    service = build()

    def broken_create(event):
        raise RuntimeError("database down")

    service.repository.create = broken_create

    service.record("u1", "query")
