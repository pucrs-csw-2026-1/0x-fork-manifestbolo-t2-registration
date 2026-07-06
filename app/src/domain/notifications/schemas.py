"""Schemas for domain events published to SNS."""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

REGISTRATION_TOPIC_SOURCE = "registration-events"


class DomainEventType(StrEnum):
    REGISTRATION_CONFIRMED = "RegistrationConfirmed"
    REGISTRATION_CANCELLED = "RegistrationCancelled"


class DomainEvent(BaseModel):
    """Envelope published to the `registration-events` SNS topic."""

    event_id: UUID
    event_type: DomainEventType
    source: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resource_ref: str
