"""Pydantic schemas for registrations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .enums import RegistrationStatus

# ---------------------------------------------------------------------------
# Schemas legados (mantidos para compatibilidade com POST /register)
# ---------------------------------------------------------------------------


class RegistrationCreateRequest(BaseModel):
    event_id: UUID = Field(..., alias="eventId")
    user_id: UUID = Field(..., alias="userId")

    model_config = ConfigDict(populate_by_name=True)


class RegistrationResponse(BaseModel):
    event_id: UUID = Field(..., alias="eventId")
    user_id: UUID = Field(..., alias="userId")
    status: RegistrationStatus
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ---------------------------------------------------------------------------
# GET /events/available  –  eventos com vagas disponíveis
# ---------------------------------------------------------------------------


class AvailableEventResponse(BaseModel):
    """Representa um evento com vagas ainda abertas para inscrição."""

    event_id: UUID = Field(..., alias="eventId", description="ID único do evento")
    name: str = Field(..., description="Nome do evento")
    max_capacity: int = Field(
        ...,
        alias="maxCapacity",
        description="Capacidade máxima de inscritos",
    )
    registered_count: int = Field(
        ...,
        alias="registeredCount",
        description="Número atual de inscritos (neste serviço)",
    )
    available_slots: int = Field(
        ...,
        alias="availableSlots",
        description="Vagas restantes (max_capacity - registered_count)",
    )

    model_config = ConfigDict(populate_by_name=True)


# ---------------------------------------------------------------------------
# GET /events/{event_id}/registrations  –  inscritos de um evento
# ---------------------------------------------------------------------------


class GuestRegistrationResponse(BaseModel):
    """Representa um convidado inscrito em um evento."""

    event_id: UUID = Field(..., alias="eventId", description="ID do evento")
    user_id: UUID = Field(..., alias="userId", description="ID do usuário inscrito")
    status: RegistrationStatus = Field(..., description="Status atual da inscrição")
    created_at: datetime = Field(
        ...,
        alias="createdAt",
        description="Data/hora de criação da inscrição",
    )
    updated_at: datetime | None = Field(
        None,
        alias="updatedAt",
        description="Data/hora da última atualização da inscrição, se houver",
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ---------------------------------------------------------------------------
# POST /events/{event_id}/guests  –  inscrição de convidado
# ---------------------------------------------------------------------------


class GuestRegistrationRequest(BaseModel):
    """Payload para inscrever um convidado em um evento."""

    user_id: UUID = Field(
        ...,
        alias="userId",
        description="ID do usuário a ser inscrito como convidado",
    )

    model_config = ConfigDict(populate_by_name=True)


# ---------------------------------------------------------------------------
# GET /events/{event_id}/guests/{user_id}/check-in  –  validação para check-in
# ---------------------------------------------------------------------------


class CheckInStatusResponse(BaseModel):
    """Resposta da validação de inscrição para o microsserviço de check-in."""

    event_id: UUID = Field(..., alias="eventId", description="ID do evento")
    user_id: UUID = Field(..., alias="userId", description="ID do usuário consultado")
    status: RegistrationStatus = Field(
        ...,
        description="Status atual da inscrição no banco de dados",
    )
    created_at: datetime = Field(
        ...,
        alias="createdAt",
        description="Data/hora da criação da inscrição",
    )
    updated_at: datetime | None = Field(
        None,
        alias="updatedAt",
        description="Data/hora da última atualização da inscrição, se houver",
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ---------------------------------------------------------------------------
# POST /events/confirmation/{confirmation_id}  –  confirmação de inscrição
# ---------------------------------------------------------------------------


class ConfirmationCodeRequest(BaseModel):
    """Payload para confirmar uma inscrição via token alfanumérico."""

    token: str = Field(
        ...,
        min_length=8,
        max_length=8,
        pattern=r"^[A-Za-z0-9]{8}$",
        description="Token alfanumérico de 8 caracteres enviado ao usuário",
        examples=["XY34ZW78"],
    )


class ConfirmationResponse(BaseModel):
    """Resposta após confirmação bem-sucedida de uma inscrição."""

    confirmation_id: UUID = Field(
        ...,
        alias="confirmationId",
        description="ID da solicitação de confirmação",
    )
    event_id: UUID = Field(..., alias="eventId", description="ID do evento confirmado")
    user_id: UUID = Field(
        ..., alias="userId", description="ID do usuário que confirmou"
    )
    confirmed_at: datetime = Field(
        ...,
        alias="confirmedAt",
        description="Data/hora em que a confirmação foi registrada",
    )

    model_config = ConfigDict(populate_by_name=True)
