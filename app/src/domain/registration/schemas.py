"""Pydantic schemas for registrations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RegistrationCreateRequest(BaseModel):
    eventId: UUID
    userId: UUID


class RegistrationResponse(BaseModel):
    eventId: UUID
    userId: UUID
    registrationTimestamp: datetime
    confirmationTimestamp: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
