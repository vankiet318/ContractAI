"""add users.role and the usage_events table

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-14

"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(16),
            nullable=False,
            server_default="user",
        ),
    )

    op.create_table(
        "usage_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_usage_events_user_id", "usage_events", ["user_id"])
    op.create_index(
        "ix_usage_events_created_at", "usage_events", ["created_at"]
    )

    # Usage before this migration, from what is still stored. Questions
    # and documents in chats the users already deleted are lost.
    op.execute(
        """
        INSERT INTO usage_events (id, user_id, kind, created_at)
        SELECT gen_random_uuid()::text, s.user_id, 'query', m.created_at
        FROM chat_messages m JOIN sessions s ON s.id = m.session_id
        """
    )
    op.execute(
        """
        INSERT INTO usage_events (id, user_id, kind, created_at)
        SELECT gen_random_uuid()::text, s.user_id, 'upload', d.created_at
        FROM documents d JOIN sessions s ON s.id = d.session_id
        """
    )


def downgrade() -> None:
    op.drop_index("ix_usage_events_created_at", table_name="usage_events")
    op.drop_index("ix_usage_events_user_id", table_name="usage_events")
    op.drop_table("usage_events")
    op.drop_column("users", "role")
