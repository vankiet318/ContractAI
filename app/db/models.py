from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime]


class SessionORM(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255))
    title_is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
    created_at: Mapped[datetime]

    documents: Mapped[list["DocumentORM"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )

    messages: Mapped[list["ChatMessageORM"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class DocumentORM(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sessions.id"),
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(1024))
    status: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime]
    error_message: Mapped[str | None] = mapped_column(
        String(2048),
        default=None,
    )

    session: Mapped["SessionORM"] = relationship(
        back_populates="documents",
    )


class ChatMessageORM(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sessions.id"),
        index=True,
    )
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime]
    feedback: Mapped[str | None] = mapped_column(
        String(16),
        default=None,
    )

    session: Mapped["SessionORM"] = relationship(
        back_populates="messages",
    )
