"""Business logic for event slots and registration-slot bindings."""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from .model import EventSlot, RegistrationSlot
from .repository import (
    EventSlotRepository,
    RegistrationSlotRepository,
    get_event_slot_repository,
    get_registration_slot_repository,
)
from .schemas import EventSlotCreate


class EventSlotService:
    def __init__(self, repository: EventSlotRepository) -> None:
        self.repository = repository

    def list_slots(self, event_id: UUID) -> list[EventSlot]:
        return self.repository.list_by_event(event_id)

    def create_slot(self, event_id: UUID, data: EventSlotCreate) -> EventSlot:
        return self.repository.create(
            event_id=event_id,
            name=data.name,
            description=data.description,
            capacity=data.capacity,
            start_time=data.start_time,
            end_time=data.end_time,
        )

    def delete_slot(self, event_id: UUID, slot_id: UUID) -> None:
        slot = self.repository.get_by_id(slot_id)
        if slot is None or slot.event_id != event_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
        self.repository.delete(slot)


class RegistrationSlotService:
    def __init__(
        self,
        slot_repo: EventSlotRepository,
        reg_slot_repo: RegistrationSlotRepository,
    ) -> None:
        self.slot_repo = slot_repo
        self.reg_slot_repo = reg_slot_repo

    def list_user_slots(self, event_id: UUID, user_id: UUID) -> list[RegistrationSlot]:
        return self.reg_slot_repo.list_by_registration(event_id, user_id)

    def register_slot(self, event_id: UUID, user_id: UUID, slot_id: UUID) -> RegistrationSlot:
        slot = self.slot_repo.get_by_id(slot_id)
        if slot is None or slot.event_id != event_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")

        if slot.capacity is not None:
            count = self.reg_slot_repo.count_by_slot(slot_id)
            if count >= slot.capacity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail="Slot is full"
                )

        if self.reg_slot_repo.get(slot_id, event_id, user_id) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already registered for this slot",
            )

        try:
            return self.reg_slot_repo.create(slot_id, event_id, user_id)
        except IntegrityError as exc:
            self.reg_slot_repo.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already registered for this slot",
            ) from exc

    def unregister_slot(self, event_id: UUID, user_id: UUID, slot_id: UUID) -> None:
        reg_slot = self.reg_slot_repo.get(slot_id, event_id, user_id)
        if reg_slot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Registration for slot not found"
            )
        self.reg_slot_repo.delete(reg_slot)


def get_event_slot_service(
    repository: EventSlotRepository = Depends(get_event_slot_repository),
) -> EventSlotService:
    return EventSlotService(repository)


def get_registration_slot_service(
    slot_repo: EventSlotRepository = Depends(get_event_slot_repository),
    reg_slot_repo: RegistrationSlotRepository = Depends(get_registration_slot_repository),
) -> RegistrationSlotService:
    return RegistrationSlotService(slot_repo, reg_slot_repo)
