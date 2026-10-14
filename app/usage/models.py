from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

# query: a question sent to the chatbot. upload: a document uploaded.
UsageKind = Literal["query", "upload"]


@dataclass(frozen=True)
class UsageEvent:
    event_id: str
    user_id: str
    kind: UsageKind
    created_at: datetime


@dataclass
class UsageCounts:
    queries: int = 0
    uploads: int = 0

    def add(self, kind: UsageKind) -> None:
        if kind == "query":
            self.queries += 1
        else:
            self.uploads += 1


@dataclass
class DailyUsage:
    date: date
    queries: int = 0
    uploads: int = 0


@dataclass
class UserUsageTotals:
    queries: int = 0
    uploads: int = 0
    last_active_at: datetime | None = None
