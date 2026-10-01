import math
import threading
import time
from collections import defaultdict, deque
from typing import Callable


class RateLimitExceededError(Exception):

    def __init__(self, retry_after_seconds: int):
        super().__init__(
            f"Rate limit exceeded, retry after {retry_after_seconds}s"
        )
        self.retry_after_seconds = retry_after_seconds


class SlidingWindowRateLimiter:
    """
    Allows at most `max_requests` per key within any `window_seconds`
    interval. State is in-process memory: it resets on restart and is not
    shared between workers, which is fine for a single local backend.
    """

    def __init__(
        self,
        max_requests: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str) -> None:

        now = self.clock()

        with self._lock:
            hits = self._hits[key]
            self._drop_expired(hits, now)

            if len(hits) >= self.max_requests:
                raise RateLimitExceededError(
                    self._retry_after(hits, now)
                )

            hits.append(now)

    def _drop_expired(self, hits: deque[float], now: float) -> None:
        while hits and hits[0] <= now - self.window_seconds:
            hits.popleft()

    def _retry_after(self, hits: deque[float], now: float) -> int:
        oldest_expires_at = hits[0] + self.window_seconds
        return max(1, math.ceil(oldest_expires_at - now))
