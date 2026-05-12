"""Repository layer for health persistence."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import HealthLog


class HealthRepository:
    """Encapsulates database operations for health logs."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create_log(self, status: str) -> HealthLog:
        """Create and persist a new health log entry."""
        log = HealthLog(status=status)
        self._db.add(log)
        self._db.commit()
        self._db.refresh(log)
        return log

    def get_latest(self) -> HealthLog | None:
        """Return the newest health log entry, if available."""
        stmt = select(HealthLog).order_by(HealthLog.checked_at.desc()).limit(1)
        return self._db.execute(stmt).scalar_one_or_none()
