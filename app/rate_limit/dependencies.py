from typing import Callable

from fastapi import Depends, HTTPException, Request

from app.auth.models import User
from app.rate_limit.limiter import (
    RateLimitExceededError,
    SlidingWindowRateLimiter,
)


def create_ip_rate_limit(
    limiter: SlidingWindowRateLimiter,
) -> Callable[..., None]:

    def enforce_ip_rate_limit(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        enforce(limiter, f"ip:{client_ip}")

    return enforce_ip_rate_limit


def create_user_rate_limit(
    limiter: SlidingWindowRateLimiter,
    get_current_user: Callable[..., User],
) -> Callable[..., None]:

    def enforce_user_rate_limit(
        current_user: User = Depends(get_current_user),
    ) -> None:
        enforce(limiter, f"user:{current_user.user_id}")

    return enforce_user_rate_limit


def enforce(limiter: SlidingWindowRateLimiter, key: str) -> None:
    try:
        limiter.hit(key)
    except RateLimitExceededError as error:
        raise HTTPException(
            status_code=429,
            detail=(
                "Bạn thao tác quá nhiều lần. Vui lòng thử lại sau "
                f"{error.retry_after_seconds} giây."
            ),
            headers={"Retry-After": str(error.retry_after_seconds)},
        )
