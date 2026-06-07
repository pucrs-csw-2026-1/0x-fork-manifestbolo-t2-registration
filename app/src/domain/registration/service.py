"""Business logic for registrations."""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from .enums import RegistrationStatus
from .model import ActivityRegistration, Registration
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
