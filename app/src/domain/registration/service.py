"""Business logic for registrations."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from .enums import RegistrationStatus
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

    def get_check_in_registration(
        self,
        event_id: UUID,
        user_id: UUID,
    ) -> Registration | None:
        return self.repository.get_by_event_and_user(event_id, user_id)

    def confirm(self, confirmation_id: UUID, token: str) -> Registration:
        validation_token = self.repository.get_validation_token(confirmation_id)
        if validation_token is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Confirmation not found.",
            )

        if validation_token.expires_at < datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Confirmation token has expired.",
            )

        registration = self.repository.get_by_event_and_user(
            validation_token.event_id, validation_token.user_id
        )
        if registration is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration not found.",
            )

        if registration.status == RegistrationStatus.CONFIRMED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Registration already confirmed.",
            )

        if token != validation_token.token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid confirmation token.",
            )

        return self.repository.update_status(registration, RegistrationStatus.CONFIRMED)


def get_registration_service(
    repository: RegistrationRepository = Depends(get_registration_repository),
) -> RegistrationService:
    return RegistrationService(repository)
