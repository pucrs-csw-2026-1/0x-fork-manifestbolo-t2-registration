"""Schemas for domain events published to SNS."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

REGISTRATION_TOPIC_SOURCE = "registration-events"
# Versão do envelope canônico (US-08, ADR-0009 do Metrics): payload em `data`.
ENVELOPE_VERSION = "1.0"


class DomainEventType(StrEnum):
    REGISTRATION_CONFIRMED = "RegistrationConfirmed"
    REGISTRATION_CANCELLED = "RegistrationCancelled"


class DomainEvent(BaseModel):
    """Envelope published to the `registration-events` SNS topic.

    Carrega o payload de domínio em ``data`` (US-08): o Metrics monta o
    attendant a partir da própria mensagem SQS, sem consultar esta API por HTTP.
    """

    event_id: UUID
    event_type: DomainEventType
    source: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resource_ref: str
    version: str = ENVELOPE_VERSION
    data: dict[str, Any] | None = None
