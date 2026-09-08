from typing import Callable

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.models import User
from app.sessions.deletion_service import SessionDeletionService
from app.sessions.service import SessionService


class CreateSessionRequest(BaseModel):
    title: str = Field(default="New chat", min_length=1)


class SessionResponse(BaseModel):
    session_id: str
    title: str
    created_at: str


def create_sessions_router(
    session_service: SessionService,
    deletion_service: SessionDeletionService,
    get_current_user: Callable[..., User],
) -> APIRouter:

    router = APIRouter()

    @router.post("", response_model=SessionResponse, status_code=201)
    def create_session(
        request: CreateSessionRequest,
        current_user: User = Depends(get_current_user),
    ):
        session = session_service.create(
            user_id=current_user.user_id,
            title=request.title,
        )

        return SessionResponse(
            session_id=session.session_id,
            title=session.title,
            created_at=session.created_at.isoformat(),
        )

    @router.get("", response_model=list[SessionResponse])
    def list_sessions(
        current_user: User = Depends(get_current_user),
    ):
        sessions = session_service.list_for_user(current_user.user_id)

        return [
            SessionResponse(
                session_id=session.session_id,
                title=session.title,
                created_at=session.created_at.isoformat(),
            )
            for session in sessions
        ]

    @router.delete("/{session_id}", status_code=204)
    def delete_session(
        session_id: str,
        current_user: User = Depends(get_current_user),
    ):
        try:
            deletion_service.delete(
                session_id=session_id,
                user_id=current_user.user_id,
            )
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail="Session not found",
            )

    return router
