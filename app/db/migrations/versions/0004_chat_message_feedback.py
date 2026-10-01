"""add feedback column to chat_messages

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-10

"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "chat_messages",
        sa.Column("feedback", sa.String(16), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("chat_messages", "feedback")
