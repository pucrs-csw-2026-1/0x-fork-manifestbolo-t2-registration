"""Pydantic schemas for the health domain."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Response payload returned by the health endpoint."""

    status: str
    version: str
    timestamp: datetime


class HealthLogSchema(BaseModel):
    """Serialized representation of a health log row."""

    id: UUID
    checked_at: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)
