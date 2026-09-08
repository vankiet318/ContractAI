from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    user_id: str
    email: str
    hashed_password: str
    created_at: datetime
