"""Business logic for registrations."""

from datetime import UTC, datetime, timedelta
import secrets
from string import ascii_letters, digits
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from src.config import get_settings

from .enums import RegistrationStatus
from .model import ActivityRegistration, Registration
from .repository import RegistrationRepository, get_registration_repository


class RegistrationService:
    def __init__(self, repository: RegistrationRepository) -> None:
        self.repository = repository

    def _generate_authentication_token(self) -> str:
        alphabet = ascii_letters + digits
        return "".join(secrets.choice(alphabet) for _ in range(8))

    def _authentication_token_expires_at(self) -> datetime:
        settings = get_settings()
        return datetime.now(UTC) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    def register(
        self,
        event_id: UUID,
        user_id: UUID,
        authenticated_user_id: UUID,
    ) -> Registration:
        if authenticated_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authenticated user does not match requested user",
            )

        if self.repository.get_by_event_and_user(event_id, user_id) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already registered for this event",
            )

        try:
            return self.repository.create_with_authentication_token(
                event_id,
                user_id,
                self._generate_authentication_token(),
                self._authentication_token_expires_at(),
            )
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

    def cancel_registration(self, event_id: UUID, user_id: UUID) -> None:
        registration = self.repository.get_by_event_and_user(event_id, user_id)
        if registration is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration not found.",
            )

        # TODO: rejeitar cancelamento com 422 quando o evento já tiver ocorrido.
        # Depende do contrato real do events-service (EventsClient hoje é apenas
        # um placeholder), então a checagem fica pendente até a integração existir.

        # Soft delete: mantém o histórico marcando a inscrição como CANCELLED.
        # Idempotente: cancelar uma inscrição já cancelada também retorna 204.
        if registration.status != RegistrationStatus.CANCELLED:
            self.repository.update_status(registration, RegistrationStatus.CANCELLED)

    def get_activity_registration(
        self,
        activity_id: UUID,
        user_id: UUID,
    ) -> ActivityRegistration | None:
        return self.repository.get_by_activity_and_user(activity_id, user_id)

    def register_activity(
        self,
        activity_id: UUID,
        user_id: UUID,
        event_id: UUID,
    ) -> ActivityRegistration:
        if self.repository.get_by_activity_and_user(activity_id, user_id) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already registered for this activity",
            )

        try:
            return self.repository.create_activity_registration(
                activity_id,
                user_id,
                event_id,
            )
        except IntegrityError as exc:
            self.repository.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already registered for this activity",
            ) from exc


def get_registration_service(
    repository: RegistrationRepository = Depends(get_registration_repository),
) -> RegistrationService:
    return RegistrationService(repository)
