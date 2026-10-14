import logging
import sys
from collections import deque
from dataclasses import dataclass
from datetime import datetime

ACCESS_LOGGER = "uvicorn.access"

# The log page polls this path; its own requests would bury everything else.
_IGNORED_ACCESS_PATHS = ("/admin/logs",)


@dataclass(frozen=True)
class LogEntry:
    entry_id: int
    created_at: datetime
    level: str
    logger: str
    message: str
    exception: str | None = None


class LogBuffer(logging.Handler):
    """
    Keeps the most recent log records in memory for the admin log page.

    Like the in-memory rate limiter, it belongs to this process: records are
    lost on restart, and each process would only see its own. The full log
    still goes to stderr (`docker compose logs`).
    """

    def __init__(self, capacity: int, level: int = logging.INFO):
        super().__init__(level=level)
        self._entries: deque[LogEntry] = deque(maxlen=capacity)
        self._next_id = 1
        self._exception_formatter = logging.Formatter()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = record.getMessage()

            if record.name == ACCESS_LOGGER and any(
                path in message for path in _IGNORED_ACCESS_PATHS
            ):
                return

            exception = (
                self._exception_formatter.formatException(record.exc_info)
                if record.exc_info
                else None
            )

            # Handler.handle() already holds self.lock here.
            self._entries.append(
                LogEntry(
                    entry_id=self._next_id,
                    created_at=datetime.fromtimestamp(record.created).astimezone(),
                    level=record.levelname,
                    logger=record.name,
                    message=message,
                    exception=exception,
                )
            )
            self._next_id += 1
        except Exception:
            self.handleError(record)

    def newest(self, limit: int) -> list[LogEntry]:
        """Up to `limit` entries, newest first."""
        with self.lock:
            entries = list(self._entries)

        return entries[::-1][:limit]


def install_log_buffer(buffer: LogBuffer) -> None:
    """
    Sends application and uvicorn logs to `buffer` as well as to stderr.

    Run after uvicorn has configured its own loggers. Its "uvicorn" and
    "uvicorn.access" loggers do not propagate, so they get the buffer
    directly; everything else reaches it through the root logger.
    """
    root = logging.getLogger()

    # Python only prints warnings of unconfigured loggers while the root
    # logger has no handler at all; adding the buffer would silence them.
    if not root.handlers:
        stderr = logging.StreamHandler(sys.stderr)
        stderr.setFormatter(
            logging.Formatter("%(levelname)s:     %(name)s - %(message)s")
        )
        root.addHandler(stderr)

    root.setLevel(logging.INFO)

    # One INFO line per outgoing HTTP call (Qdrant, LLM APIs) would drown
    # the application's own logs.
    for noisy in ("httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    for logger in (root, logging.getLogger("uvicorn"), logging.getLogger(ACCESS_LOGGER)):
        if buffer not in logger.handlers:
            logger.addHandler(buffer)
