from dataclasses import dataclass
from datetime import datetime

from app.auth.models import User, UserRole
from app.auth.repository import UserRepository
from app.messages.repository import ChatMessageRepository
from app.usage.models import DailyUsage, UsageCounts, UserUsageTotals
from app.usage.service import UsageService


class UserNotFoundError(Exception):
    pass


class CannotChangeOwnRoleError(Exception):
    """An admin removing their own role could leave no admin at all."""


@dataclass
class AdminOverview:
    total_users: int
    new_users: int
    active_users: int
    queries: int
    uploads: int
    likes: int
    dislikes: int
    daily: list[DailyUsage]


@dataclass
class UserUsageSummary:
    user: User
    # Within the requested window.
    window: UsageCounts
    # Since the account was created.
    totals: UserUsageTotals


class AdminService:

    def __init__(
        self,
        user_repository: UserRepository,
        message_repository: ChatMessageRepository,
        usage_service: UsageService,
        clock=datetime.now,
    ):
        self.user_repository = user_repository
        self.message_repository = message_repository
        self.usage_service = usage_service
        self.clock = clock

    def overview(self, days: int) -> AdminOverview:
        since = self.usage_service.window_start(days)
        users = self.user_repository.list_all()
        daily = self.usage_service.daily(days)
        feedback = self.message_repository.count_feedback_since(since)

        return AdminOverview(
            total_users=len(users),
            new_users=sum(1 for user in users if user.created_at >= since),
            active_users=len(self.usage_service.counts_by_user(days)),
            queries=sum(day.queries for day in daily),
            uploads=sum(day.uploads for day in daily),
            likes=feedback.get("like", 0),
            dislikes=feedback.get("dislike", 0),
            daily=daily,
        )

    def list_users(self, days: int) -> list[UserUsageSummary]:
        window = self.usage_service.counts_by_user(days)
        totals = self.usage_service.totals_by_user()

        return [
            UserUsageSummary(
                user=user,
                window=window.get(user.user_id, UsageCounts()),
                totals=totals.get(user.user_id, UserUsageTotals()),
            )
            for user in self.user_repository.list_all()
        ]

    def user_usage(
        self,
        user_id: str,
        days: int,
    ) -> tuple[User, list[DailyUsage]]:
        user = self._get_user(user_id)

        return user, self.usage_service.daily(days, user_id=user_id)

    def set_role(self, actor: User, user_id: str, role: UserRole) -> User:
        if actor.user_id == user_id:
            raise CannotChangeOwnRoleError(user_id)

        if not self.user_repository.update_role(user_id, role):
            raise UserNotFoundError(user_id)

        return self._get_user(user_id)

    def is_locked(self, user: User) -> bool:
        return user.is_locked(self.clock())

    def _get_user(self, user_id: str) -> User:
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise UserNotFoundError(user_id)

        return user
