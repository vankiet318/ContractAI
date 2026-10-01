import pytest

from app.rate_limit.limiter import RateLimitExceededError, SlidingWindowRateLimiter


class FakeClock:

    def __init__(self):
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_blocks_after_limit_and_reports_retry_after():
    clock = FakeClock()
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60, clock=clock)

    limiter.hit("ip:1")
    clock.now += 10
    limiter.hit("ip:1")

    with pytest.raises(RateLimitExceededError) as error:
        limiter.hit("ip:1")

    assert error.value.retry_after_seconds == 50


def test_allows_again_once_oldest_hit_leaves_window():
    clock = FakeClock()
    limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60, clock=clock)

    limiter.hit("ip:1")
    clock.now += 60

    limiter.hit("ip:1")


def test_keys_are_limited_independently():
    limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60, clock=FakeClock())

    limiter.hit("ip:1")
    limiter.hit("ip:2")
