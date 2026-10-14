from typing import Callable

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from app.auth.models import User
from app.auth.repository import UserRepository
from app.auth.security import decode_access_token

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_get_current_user(
    user_repository: UserRepository,
) -> Callable[..., User]:

    def get_current_user(
        token: str = Depends(_oauth2_scheme),
    ) -> User:

        credentials_error = HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        user_id = decode_access_token(token)

        if user_id is None:
            raise credentials_error

        user = user_repository.get_by_id(user_id)

        if user is None:
            raise credentials_error

        return user

    return get_current_user


def create_require_admin(
    get_current_user: Callable[..., User],
) -> Callable[..., User]:

    def require_admin(
        current_user: User = Depends(get_current_user),
    ) -> User:

        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Bạn không có quyền truy cập trang quản trị.",
            )

        return current_user

    return require_admin
