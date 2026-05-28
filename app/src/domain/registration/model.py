"""SQLAlchemy models for the registration domain."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKeyConstraint,
    String,
    text,
    Index
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator, Uuid

from src.database import Base

from .enums import RegistrationStatus


class RegistrationStatusType(TypeDecorator[RegistrationStatus]):
    """Persist registration status as string while exposing a backend enum."""

    impl = String(32)
    cache_ok = True

    def process_bind_param(
        self,
        value: RegistrationStatus | str | None,
        dialect: object,
    ) -> str | None:
        if value is None:
            return None
        return RegistrationStatus(value).value

    def process_result_value(
        self,
        value: str | None,
        dialect: object,
    ) -> RegistrationStatus | None:
        if value is None:
            return None
        return RegistrationStatus(value)


class Registration(Base):
    __tablename__ = "registrations"

    event_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    status: Mapped[RegistrationStatus] = mapped_column(
        RegistrationStatusType(),
        default=RegistrationStatus.REGISTERED,
        server_default=text("'REGISTERED'"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=lambda: datetime.now(UTC),
        nullable=True,
    )


class ValidationToken(Base):
    __tablename__ = "authentication_tokens"

    __table_args__ = (
        ForeignKeyConstraint(
            ["event_id", "user_id"],
            ["registrations.event_id", "registrations.user_id"],
            ondelete="CASCADE",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    user_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    token: Mapped[str] = mapped_column(String(8), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class ActivityRegistration(Base):
    __tablename__ = "activity_registrations"
    __table_args__ = (
        Index(
            "ix_activity_registrations_event_user",
            "event_id",
            "user_id",
        ),
    )

    activity_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    event_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
