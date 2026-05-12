"""SQLAlchemy models for event registrations."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import DateTime, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from src.database import Base


class Registration(Base):
    __tablename__ = "registrations"

    event_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    registration_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    confirmation_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
