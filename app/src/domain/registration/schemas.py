"""Pydantic schemas for registrations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .enums import RegistrationStatus


# ---------------------------------------------------------------------------
# Schemas legados (mantidos para compatibilidade com POST /register)
# ---------------------------------------------------------------------------


class RegistrationCreateRequest(BaseModel):
    eventId: UUID
    userId: UUID


class RegistrationResponse(BaseModel):
    eventId: UUID
    userId: UUID
    status: RegistrationStatus
    createdAt: datetime
    updatedAt: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# GET /events/available  –  eventos com vagas disponíveis
# ---------------------------------------------------------------------------


class AvailableEventResponse(BaseModel):
    """Representa um evento com vagas ainda abertas para inscrição."""

    eventId: UUID = Field(..., description="ID único do evento")
    name: str = Field(..., description="Nome do evento")
    maxCapacity: int = Field(..., description="Capacidade máxima de inscritos")
    registeredCount: int = Field(
        ..., description="Número atual de inscritos (neste serviço)"
    )
    availableSlots: int = Field(
        ..., description="Vagas restantes (maxCapacity - registeredCount)"
    )


# ---------------------------------------------------------------------------
# GET /events/{event_id}/registrations  –  inscritos de um evento
# ---------------------------------------------------------------------------


class GuestRegistrationResponse(BaseModel):
    """Representa um convidado inscrito em um evento."""

    eventId: UUID = Field(..., description="ID do evento")
    userId: UUID = Field(..., description="ID do usuário inscrito")
    status: RegistrationStatus = Field(..., description="Status atual da inscrição")
    createdAt: datetime = Field(..., description="Data/hora de criação da inscrição")
    updatedAt: datetime | None = Field(
        None,
        description="Data/hora da última atualização da inscrição, se houver",
    )

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# POST /events/{event_id}/guests  –  inscrição de convidado
# ---------------------------------------------------------------------------


class GuestRegistrationRequest(BaseModel):
    """Payload para inscrever um convidado em um evento."""

    userId: UUID = Field(..., description="ID do usuário a ser inscrito como convidado")


# ---------------------------------------------------------------------------
# GET /events/{event_id}/guests/{user_id}/check-in  –  validação para check-in
# ---------------------------------------------------------------------------


class CheckInStatusResponse(BaseModel):
    """Resposta da validação de inscrição para o microsserviço de check-in."""

    eventId: UUID = Field(..., description="ID do evento")
    userId: UUID = Field(..., description="ID do usuário consultado")
    isRegistered: bool = Field(
        ...,
        description="Indica se o usuário possui inscrição ativa no evento",
    )
    isConfirmed: bool = Field(
        ...,
        description="Indica se a inscrição foi confirmada pelo usuário (e-mail/token)",
    )
    createdAt: datetime | None = Field(
        None, description="Data/hora da criação da inscrição, se existir"
    )


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

    confirmationId: UUID = Field(..., description="ID da solicitação de confirmação")
    eventId: UUID = Field(..., description="ID do evento confirmado")
    userId: UUID = Field(..., description="ID do usuário que confirmou")
    confirmedAt: datetime = Field(
        ..., description="Data/hora em que a confirmação foi registrada"
    )
