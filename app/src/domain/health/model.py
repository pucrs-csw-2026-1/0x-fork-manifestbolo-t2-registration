"""SQLAlchemy models for the health domain."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from src.database import Base


class HealthLog(Base):
    """Stores health-check execution records."""

    __tablename__ = "health_log"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
