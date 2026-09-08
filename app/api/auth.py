from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.auth.security import create_access_token
from app.auth.service import AuthService

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    user_id: str
    email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def create_auth_router(auth_service: AuthService) -> APIRouter:

    @router.post(
        "/register",
        response_model=UserResponse,
        status_code=201,
    )
    def register(request: RegisterRequest):
        try:
            user = auth_service.register(
                email=request.email,
                password=request.password,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=409,
                detail=str(error),
            )

        return UserResponse(
            user_id=user.user_id,
            email=user.email,
        )

    @router.post("/login", response_model=TokenResponse)
    def login(request: LoginRequest):
        user = auth_service.authenticate(
            email=request.email,
            password=request.password,
        )

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password",
            )

        access_token = create_access_token(user.user_id)

        return TokenResponse(access_token=access_token)

    return router
