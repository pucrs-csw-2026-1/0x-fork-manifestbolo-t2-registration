"""Pydantic schemas for event slots."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EventSlotCreate(BaseModel):
    name: str = Field(..., max_length=256, description="Nome do slot (ex: Palestra A, Workshop B)")
    description: str | None = Field(None, description="Descrição opcional do slot")
    capacity: int | None = Field(None, gt=0, description="Capacidade máxima de inscritos no slot")
    start_time: datetime | None = Field(None, description="Data/hora de início do slot")
    end_time: datetime | None = Field(None, description="Data/hora de encerramento do slot")


class EventSlotResponse(BaseModel):
    slot_id: UUID
    event_id: UUID
    name: str
    description: str | None
    capacity: int | None
    start_time: datetime | None
    end_time: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RegistrationSlotCreate(BaseModel):
    slot_id: UUID = Field(..., description="ID do slot ao qual o usuário deseja se inscrever")


class RegistrationSlotResponse(BaseModel):
    slot_id: UUID
    event_id: UUID
    user_id: UUID
    registered_at: datetime

    model_config = ConfigDict(from_attributes=True)
