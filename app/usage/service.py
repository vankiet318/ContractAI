import logging
from datetime import date, datetime, time, timedelta, tzinfo
from typing import Callable
from uuid import uuid4

from app.usage.models import (
    DailyUsage,
    UsageCounts,
    UsageEvent,
    UsageKind,
    UserUsageTotals,
)
from app.usage.repository import UsageRepository

logger = logging.getLogger(__name__)


class UsageService:
    """
    Records what each user does and counts it per day.

    Timestamps are stored like the rest of the app: naive, in the server's
    local time (UTC in Docker). Days are counted in `timezone` instead, so
    a question asked at 06:00 in Vietnam is not counted on the day before.
    """

    def __init__(
        self,
        repository: UsageRepository,
        timezone: tzinfo,
        clock: Callable[[], datetime] = datetime.now,
    ):
        self.repository = repository
        self.timezone = timezone
        self.clock = clock

    def record(self, user_id: str, kind: UsageKind) -> None:
        """Best-effort: a failed write must not fail the user's request."""
        try:
            self.repository.create(
                UsageEvent(
                    event_id=str(uuid4()),
                    user_id=user_id,
                    kind=kind,
                    created_at=self.clock(),
                )
            )
        except Exception:
            logger.exception("Could not record %s usage for %s", kind, user_id)

    def window_start(self, days: int) -> datetime:
        """
        Server-local time at which the window of the last `days` days
        (today included) starts.
        """
        first_day = self._today() - timedelta(days=days - 1)

        start = datetime.combine(first_day, time(), tzinfo=self.timezone)

        return start.astimezone().replace(tzinfo=None)

    def daily(
        self,
        days: int,
        user_id: str | None = None,
    ) -> list[DailyUsage]:
        """One entry per day of the window, oldest first, zeros included."""
        today = self._today()

        series = {
            day: DailyUsage(date=day)
            for day in (
                today - timedelta(days=offset)
                for offset in range(days - 1, -1, -1)
            )
        }

        for event in self.repository.list_since(
            self.window_start(days),
            user_id=user_id,
        ):
            entry = series.get(self.local_date(event.created_at))

            if entry is None:
                continue

            if event.kind == "query":
                entry.queries += 1
            else:
                entry.uploads += 1

        return list(series.values())

    def counts_by_user(self, days: int) -> dict[str, UsageCounts]:
        counts: dict[str, UsageCounts] = {}

        for event in self.repository.list_since(self.window_start(days)):
            counts.setdefault(event.user_id, UsageCounts()).add(event.kind)

        return counts

    def totals_by_user(self) -> dict[str, UserUsageTotals]:
        return self.repository.totals_by_user()

    def local_date(self, server_time: datetime) -> date:
        # A naive datetime is taken as server-local by astimezone().
        return server_time.astimezone(self.timezone).date()

    def _today(self) -> date:
        return self.local_date(self.clock())
