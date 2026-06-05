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

    def list_event_registrations(self, event_id: UUID) -> list[Registration]:
        return self.repository.list_by_event(event_id)

    def list_activity_user_ids(self, activity_id: UUID) -> list[UUID]:
        return self.repository.list_user_ids_by_activity(activity_id)

    def get_check_in_registration(
        self,
        event_id: UUID,
        user_id: UUID,
    ) -> Registration | None:
        return self.repository.get_by_event_and_user(event_id, user_id)


def get_registration_service(
    repository: RegistrationRepository = Depends(get_registration_repository),
) -> RegistrationService:
    return RegistrationService(repository)
