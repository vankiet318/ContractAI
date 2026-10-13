import dataclasses
import os

import pytest

# app.auth.security reads the JWT secret at import time and refuses to
# start without one, so tests get a throwaway value if .env has none.
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-unit-tests-only-0123")

from app.messages.service import ChatMessageService  # noqa: E402


class InMemoryMessageRepository:
    """ChatMessageRepository without a database."""

    def __init__(self):
        self.rows = {}

    def create(self, message):
        self.rows[message.message_id] = message

    def list_by_session(self, session_id):
        return [
            message
            for message in self.rows.values()
            if message.session_id == session_id
        ]

    def finish_pending(self, message_id, values):
        message = self.rows.get(message_id)

        if message is None or message.status != "pending":
            return False

        self.rows[message_id] = dataclasses.replace(message, **values)
        return True

    def fail_all_pending(self, error_message):
        pending = [
            message_id
            for message_id, message in self.rows.items()
            if message.status == "pending"
        ]

        for message_id in pending:
            self.finish_pending(
                message_id,
                {"status": "failed", "error_message": error_message},
            )

        return len(pending)


@pytest.fixture
def message_service():
    return ChatMessageService(InMemoryMessageRepository())
