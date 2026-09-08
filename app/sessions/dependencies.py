from typing import Callable

from fastapi import Depends, HTTPException

from app.auth.models import User
from app.sessions.models import ChatSession
from app.sessions.service import SessionService


def create_get_owned_session(
    session_service: SessionService,
    get_current_user: Callable[..., User],
) -> Callable[..., ChatSession]:

    def get_owned_session(
        session_id: str,
        current_user: User = Depends(get_current_user),
    ) -> ChatSession:

        session = session_service.get_owned(
            session_id=session_id,
            user_id=current_user.user_id,
        )

        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Session not found",
            )

        return session

    return get_owned_session
