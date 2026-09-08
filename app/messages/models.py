from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ChatMessage:
    message_id: str
    session_id: str
    question: str
    answer: str
    citations: list[dict[str, Any]]
    created_at: datetime
