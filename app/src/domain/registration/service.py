"""Business logic for registrations."""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from .model import Registration
from .repository import RegistrationRepository, get_registration_repository


class RegistrationService:
    def __init__(self, repository: RegistrationRepository) -> None:
        self.repository = repository

    def register(self, event_id: UUID, user_id: UUID) -> Registration:
        if self.repository.get_by_event_and_user(event_id, user_id) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already registered for this event",
            )

        try:
            return self.repository.create(event_id, user_id)
        except IntegrityError as exc:
            self.repository.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already registered for this event",
            ) from exc


def get_registration_service(
    repository: RegistrationRepository = Depends(get_registration_repository),
) -> RegistrationService:
    return RegistrationService(repository)
