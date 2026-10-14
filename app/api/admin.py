from datetime import date, datetime
from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel

from app.admin.service import (
    AdminService,
    CannotChangeOwnRoleError,
    CannotDeleteSelfError,
    UserNotFoundError,
)
from app.api.query import CitationResponse
from app.auth.models import User, UserRole
from app.logs.buffer import LogBuffer
from app.messages.models import MessageFeedback
from app.usage.models import DailyUsage

MAX_WINDOW_DAYS = 365
MAX_FEEDBACK_PAGE = 100
MAX_LOG_LINES = 5000

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


class RatedMessageResponse(BaseModel):
    message_id: str
    question: str
    answer: str
    citations: list[CitationResponse]
    feedback: MessageFeedback
    created_at: datetime
    user_id: str
    user_email: str
    session_title: str


class FeedbackPageResponse(BaseModel):
    total: int
    items: list[RatedMessageResponse]


class LogEntryResponse(BaseModel):
    entry_id: int
    created_at: datetime
    level: str
    logger: str
    message: str
    exception: str | None


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
    log_buffer: LogBuffer,
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

    @router.get("/feedback", response_model=FeedbackPageResponse)
    def list_feedback(
        days: int = WindowDays,
        rating: MessageFeedback = "dislike",
        limit: int = Query(default=20, ge=1, le=MAX_FEEDBACK_PAGE),
        offset: int = Query(default=0, ge=0),
    ):
        entries, total = admin_service.list_feedback(
            days=days,
            feedback=rating,
            limit=limit,
            offset=offset,
        )

        return FeedbackPageResponse(
            total=total,
            items=[
                RatedMessageResponse(
                    message_id=entry.message.message_id,
                    question=entry.message.question,
                    answer=entry.message.answer,
                    citations=[
                        CitationResponse(**citation)
                        for citation in entry.message.citations
                    ],
                    feedback=entry.message.feedback,
                    created_at=_with_offset(entry.message.created_at),
                    user_id=entry.user_id,
                    user_email=entry.user_email,
                    session_title=entry.session_title,
                )
                for entry in entries
            ],
        )

    @router.get("/logs", response_model=list[LogEntryResponse])
    def list_logs(
        limit: int = Query(default=1000, ge=1, le=MAX_LOG_LINES),
    ):
        """Most recent server log lines, newest first."""
        return [
            LogEntryResponse(
                entry_id=entry.entry_id,
                created_at=entry.created_at,
                level=entry.level,
                logger=entry.logger,
                message=entry.message,
                exception=entry.exception,
            )
            for entry in log_buffer.newest(limit)
        ]

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

    @router.post("/users/{user_id}/unlock", response_model=AdminUserResponse)
    def unlock_user(user_id: str):
        try:
            return user_response(admin_service.unlock(user_id))
        except UserNotFoundError:
            raise HTTPException(status_code=404, detail="User not found")

    @router.delete("/users/{user_id}", status_code=204)
    def delete_user(
        user_id: str,
        current_user: User = Depends(require_admin),
    ):
        try:
            admin_service.delete_user(actor=current_user, user_id=user_id)
        except CannotDeleteSelfError:
            raise HTTPException(
                status_code=400,
                detail="Không thể tự xóa tài khoản của chính mình.",
            )
        except UserNotFoundError:
            raise HTTPException(status_code=404, detail="User not found")

        return Response(status_code=204)

    return router
