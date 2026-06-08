"""Schemas for the Events service HTTP contract."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EventLocation(BaseModel):
    venue: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None

    model_config = ConfigDict(extra="ignore")


class EventResponse(BaseModel):
    id: str
    title: str
    description: str | None = None
    starts_at: datetime
    ends_at: datetime
    timezone: str
    registration_deadline: datetime | None = None
    location: EventLocation | None = None
    capacity: int
    category: str | None = None
    language: str | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    deleted_by: str | None = None
    created_by: str

    model_config = ConfigDict(extra="ignore")


class CreateEventRequest(BaseModel):
    title: str
    starts_at: datetime
    ends_at: datetime
    timezone: str
    capacity: int
    created_by: str
    description: str | None = None
    registration_deadline: datetime | None = None
    location: EventLocation | dict[str, Any] | None = None
    category: str | None = None
    language: str | None = None


class UpdateEventRequest(BaseModel):
    title: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    timezone: str | None = None
    capacity: int | None = None
    created_by: str | None = None
    description: str | None = None
    registration_deadline: datetime | None = None
    location: EventLocation | dict[str, Any] | None = None
    category: str | None = None
    language: str | None = None


class EventListResponse(BaseModel):
    data: list[EventResponse]
    total: int
    page: int
    limit: int

    model_config = ConfigDict(extra="ignore")


class ActivityResponse(BaseModel):
    id_activity: str
    title_activity: str
    description_activity: str | None = None
    type: str
    starts_at: datetime
    ends_at: datetime
    timezone: str
    registration_deadline_activity: datetime | None = None
    thumbnail_url: str | None = None
    capacity_activity: int | None = None
    workload_minutes: int
    category_activity: str | None = None
    language_activity: str | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    deleted_by: str | None = None
    created_by: str

    model_config = ConfigDict(extra="ignore")


class EventRoleResponse(BaseModel):
    event_id: str
    role: str

    model_config = ConfigDict(extra="ignore")


class CreateEventRoleRequest(BaseModel):
    role: str


class EventsByStatus(BaseModel):
    upcoming: int
    ongoing: int
    past: int

    model_config = ConfigDict(extra="ignore")


class EventsMetricsResponse(BaseModel):
    total_events: int
    total_activitys: int
    total_capacity: int
    total_enrolled: int
    total_available_spots: int
    average_occupancy_percentage: float
    events_by_category: dict[str, int] = Field(default_factory=dict)
    events_by_status: EventsByStatus

    model_config = ConfigDict(extra="ignore")
