from typing import Annotated, Callable

from fastapi import APIRouter, Depends, HTTPException
from pydantic import AfterValidator, BaseModel, EmailStr, Field

from app.auth.security import create_access_token
from app.auth.service import (
    AccountLockedError,
    AuthService,
    EmailAlreadyRegisteredError,
)

# bcrypt rejects passwords longer than 72 bytes; Vietnamese characters take
# several bytes each, so the limit is on encoded size, not characters.
MAX_PASSWORD_BYTES = 72


def check_password_size(password: str) -> str:
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError(f"Mật khẩu tối đa {MAX_PASSWORD_BYTES} byte")

    return password


Password = Annotated[str, AfterValidator(check_password_size)]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: Password = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: Password


class UserResponse(BaseModel):
    user_id: str
    email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def create_auth_router(
    auth_service: AuthService,
    login_rate_limit: Callable[..., None],
    register_rate_limit: Callable[..., None],
) -> APIRouter:

    router = APIRouter()

    @router.post(
        "/register",
        response_model=UserResponse,
        status_code=201,
        dependencies=[Depends(register_rate_limit)],
    )
    def register(request: RegisterRequest):
        try:
            user = auth_service.register(
                email=request.email,
                password=request.password,
            )
        except EmailAlreadyRegisteredError:
            raise HTTPException(
                status_code=409,
                detail="Không thể đăng ký với email này.",
            )

        return UserResponse(
            user_id=user.user_id,
            email=user.email,
        )

    @router.post(
        "/login",
        response_model=TokenResponse,
        dependencies=[Depends(login_rate_limit)],
    )
    def login(request: LoginRequest):
        try:
            user = auth_service.authenticate(
                email=request.email,
                password=request.password,
            )
        except AccountLockedError as error:
            raise HTTPException(
                status_code=429,
                detail=(
                    "Tài khoản tạm khoá do đăng nhập sai nhiều lần. "
                    f"Vui lòng thử lại sau {error.retry_after_minutes} phút."
                ),
            )

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Email hoặc mật khẩu không đúng.",
            )

        access_token = create_access_token(user.user_id)

        return TokenResponse(access_token=access_token)

    return router
