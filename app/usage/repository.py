from datetime import datetime

from sqlalchemy import func

from app.db.models import UsageEventORM
from app.db.session import get_db_session
from app.usage.models import UsageEvent, UserUsageTotals


class UsageRepository:

    def create(self, event: UsageEvent) -> None:
        with get_db_session() as db:
            db.add(
                UsageEventORM(
                    id=event.event_id,
                    user_id=event.user_id,
                    kind=event.kind,
                    created_at=event.created_at,
                )
            )

    def list_since(
        self,
        since: datetime,
        user_id: str | None = None,
    ) -> list[UsageEvent]:
        with get_db_session() as db:
            query = db.query(UsageEventORM).filter(
                UsageEventORM.created_at >= since,
            )

            if user_id is not None:
                query = query.filter(UsageEventORM.user_id == user_id)

            return [self._to_domain(row) for row in query.all()]

    def totals_by_user(self) -> dict[str, UserUsageTotals]:
        """All-time counts per user, counted by the database."""
        with get_db_session() as db:
            rows = (
                db.query(
                    UsageEventORM.user_id,
                    UsageEventORM.kind,
                    func.count(),
                    func.max(UsageEventORM.created_at),
                )
                .group_by(UsageEventORM.user_id, UsageEventORM.kind)
                .all()
            )

        totals: dict[str, UserUsageTotals] = {}

        for user_id, kind, count, last_at in rows:
            user_totals = totals.setdefault(user_id, UserUsageTotals())

            if kind == "query":
                user_totals.queries = count
            else:
                user_totals.uploads = count

            if (
                user_totals.last_active_at is None
                or last_at > user_totals.last_active_at
            ):
                user_totals.last_active_at = last_at

        return totals

    @staticmethod
    def _to_domain(row: UsageEventORM) -> UsageEvent:
        return UsageEvent(
            event_id=row.id,
            user_id=row.user_id,
            kind=row.kind,
            created_at=row.created_at,
        )
