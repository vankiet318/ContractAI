from datetime import date, datetime
from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.admin.service import (
    AdminService,
    CannotChangeOwnRoleError,
    UserNotFoundError,
)
from app.auth.models import User, UserRole
from app.usage.models import DailyUsage

MAX_WINDOW_DAYS = 365

# Number of days counted, today included.
WindowDays = Query(default=30, ge=1, le=MAX_WINDOW_DAYS)


class DailyUsageResponse(BaseModel):
    date: date
    queries: int
    uploads: int


class OverviewResponse(BaseModel):
    days: int
    total_users: int
    new_users: int
    active_users: int
    queries: int
    uploads: int
    likes: int
    dislikes: int
    daily: list[DailyUsageResponse]


class AdminUserResponse(BaseModel):
    user_id: str
    email: str
    role: UserRole
    created_at: datetime
    is_locked: bool


class UserUsageSummaryResponse(AdminUserResponse):
    queries: int
    uploads: int
    total_queries: int
    total_uploads: int
    last_active_at: datetime | None


class UserUsageResponse(BaseModel):
    user: AdminUserResponse
    days: int
    daily: list[DailyUsageResponse]


class SetRoleRequest(BaseModel):
    role: UserRole


def _with_offset(server_time: datetime) -> datetime:
    """
    Stored times are naive server-local; sending the offset along lets the
    browser show them in the viewer's own time.
    """
    return server_time.astimezone()


def _daily_response(daily: list[DailyUsage]) -> list[DailyUsageResponse]:
    return [
        DailyUsageResponse(
            date=day.date,
            queries=day.queries,
            uploads=day.uploads,
        )
        for day in daily
    ]


def create_admin_router(
    admin_service: AdminService,
    require_admin: Callable[..., User],
) -> APIRouter:

    router = APIRouter(dependencies=[Depends(require_admin)])

    def user_response(user: User) -> AdminUserResponse:
        return AdminUserResponse(
            user_id=user.user_id,
            email=user.email,
            role=user.role,
            created_at=_with_offset(user.created_at),
            is_locked=admin_service.is_locked(user),
        )

    @router.get("/overview", response_model=OverviewResponse)
    def overview(days: int = WindowDays):
        result = admin_service.overview(days)

        return OverviewResponse(
            days=days,
            total_users=result.total_users,
            new_users=result.new_users,
            active_users=result.active_users,
            queries=result.queries,
            uploads=result.uploads,
            likes=result.likes,
            dislikes=result.dislikes,
            daily=_daily_response(result.daily),
        )

    @router.get("/users", response_model=list[UserUsageSummaryResponse])
    def list_users(days: int = WindowDays):
        return [
            UserUsageSummaryResponse(
                **user_response(summary.user).model_dump(),
                queries=summary.window.queries,
                uploads=summary.window.uploads,
                total_queries=summary.totals.queries,
                total_uploads=summary.totals.uploads,
                last_active_at=(
                    _with_offset(summary.totals.last_active_at)
                    if summary.totals.last_active_at
                    else None
                ),
            )
            for summary in admin_service.list_users(days)
        ]

    @router.get("/users/{user_id}/usage", response_model=UserUsageResponse)
    def user_usage(user_id: str, days: int = WindowDays):
        try:
            user, daily = admin_service.user_usage(user_id, days)
        except UserNotFoundError:
            raise HTTPException(status_code=404, detail="User not found")

        return UserUsageResponse(
            user=user_response(user),
            days=days,
            daily=_daily_response(daily),
        )

    @router.patch("/users/{user_id}/role", response_model=AdminUserResponse)
    def set_role(
        user_id: str,
        request: SetRoleRequest,
        current_user: User = Depends(require_admin),
    ):
        try:
            user = admin_service.set_role(
                actor=current_user,
                user_id=user_id,
                role=request.role,
            )
        except CannotChangeOwnRoleError:
            raise HTTPException(
                status_code=400,
                detail="Không thể tự đổi quyền của chính mình.",
            )
        except UserNotFoundError:
            raise HTTPException(status_code=404, detail="User not found")

        return user_response(user)

    return router
