"""Repository for registration persistence."""

from collections.abc import Generator
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from src.database import get_db

from .model import ActivityRegistration, Registration


class RegistrationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_event_and_user(
        self, event_id: UUID, user_id: UUID
    ) -> Registration | None:
        return (
            self.db.query(Registration)
            .filter(
                Registration.event_id == event_id,
                Registration.user_id == user_id,
            )
            .first()
        )

    def get_by_activity_and_user(
        self, activity_id: UUID, user_id: UUID
    ) -> ActivityRegistration | None:
        return (
            self.db.query(ActivityRegistration)
            .filter(
                ActivityRegistration.activity_id == activity_id,
                ActivityRegistration.user_id == user_id,
            )
            .first()
        )

    def create_activity_registration(
        self, activity_id: UUID, user_id: UUID, event_id: UUID
    ) -> ActivityRegistration:
        registration = ActivityRegistration(
            activity_id=activity_id,
            user_id=user_id,
            event_id=event_id,
        )
        self.db.add(registration)
        self.db.commit()
        self.db.refresh(registration)
        return registration

    def list_by_event(self, event_id: UUID) -> list[Registration]:
        return (
            self.db.query(Registration)
            .filter(Registration.event_id == event_id)
            .order_by(Registration.created_at)
            .all()
        )

    def create(self, event_id: UUID, user_id: UUID) -> Registration:
        registration = Registration(event_id=event_id, user_id=user_id)
        self.db.add(registration)
        self.db.commit()
        self.db.refresh(registration)
        return registration


def get_registration_repository(
    db: Session = Depends(get_db),
) -> Generator[RegistrationRepository, None, None]:
    yield RegistrationRepository(db)
