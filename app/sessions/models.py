from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChatSession:
    session_id: str
    user_id: str
    title: str
    created_at: datetime
    title_is_default: bool = True
