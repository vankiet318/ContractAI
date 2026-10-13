from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

MessageFeedback = Literal["like", "dislike"]

# pending: question saved, answer still being generated.
# done: answer saved. failed: generation stopped, error_message says why.
MessageStatus = Literal["pending", "done", "failed"]


@dataclass
class ChatMessage:
    message_id: str
    session_id: str
    question: str
    answer: str
    citations: list[dict[str, Any]]
    created_at: datetime
    feedback: MessageFeedback | None = None
    status: MessageStatus = "done"
    error_message: str | None = None
