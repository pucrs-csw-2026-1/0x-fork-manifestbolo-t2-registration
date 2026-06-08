"""Repository for registration persistence."""

from collections.abc import Generator
from datetime import datetime
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from src.database import get_db

from .enums import RegistrationStatus
from .model import ActivityRegistration, Registration, ValidationToken

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

    def list_user_ids_by_activity(self, activity_id: UUID) -> list[UUID]:
        rows = (
            self.db.query(ActivityRegistration.user_id)
            .filter(ActivityRegistration.activity_id == activity_id)
            .order_by(ActivityRegistration.created_at)
            .all()
        )
        return [row.user_id for row in rows]

    def create(self, event_id: UUID, user_id: UUID) -> Registration:
        registration = Registration(event_id=event_id, user_id=user_id)
        self.db.add(registration)
        self.db.commit()
        self.db.refresh(registration)
        return registration

    def get_validation_token(self, confirmation_id: UUID) -> ValidationToken | None:
        return (
            self.db.query(ValidationToken)
            .filter(ValidationToken.id == confirmation_id)
            .first()
        )

    def create_with_authentication_token(
        self,
        event_id: UUID,
        user_id: UUID,
        token: str,
        expires_at: datetime,
    ) -> Registration:
        registration = Registration(event_id=event_id, user_id=user_id)
        authentication_token = ValidationToken(
            event_id=event_id,
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )
        self.db.add(registration)
        self.db.add(authentication_token)
        self.db.commit()
        self.db.refresh(registration)
        return registration

    def create_authentication_token(
        self,
        event_id: UUID,
        user_id: UUID,
        token: str,
        expires_at: datetime,
    ) -> ValidationToken:
        authentication_token = ValidationToken(
            event_id=event_id,
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )
        self.db.add(authentication_token)
        self.db.commit()
        self.db.refresh(authentication_token)
        return authentication_token

    def update_status(
        self, registration: Registration, new_status: RegistrationStatus
    ) -> Registration:
        registration.status = new_status
        self.db.commit()
        self.db.refresh(registration)
        return registration


def get_registration_repository(
    db: Session = Depends(get_db),
) -> Generator[RegistrationRepository, None, None]:
    yield RegistrationRepository(db)
