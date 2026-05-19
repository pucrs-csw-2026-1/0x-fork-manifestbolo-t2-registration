"""Repository for event slots and registration-slot bindings."""

from collections.abc import Generator
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from src.database import get_db

from .model import EventSlot, RegistrationSlot


class EventSlotRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, slot_id: UUID) -> EventSlot | None:
        return self.db.query(EventSlot).filter(EventSlot.slot_id == slot_id).first()

    def list_by_event(self, event_id: UUID) -> list[EventSlot]:
        return self.db.query(EventSlot).filter(EventSlot.event_id == event_id).all()

    def create(
        self,
        event_id: UUID,
        name: str,
        description: str | None,
        capacity: int | None,
        start_time,
        end_time,
    ) -> EventSlot:
        slot = EventSlot(
            event_id=event_id,
            name=name,
            description=description,
            capacity=capacity,
            start_time=start_time,
            end_time=end_time,
        )
        self.db.add(slot)
        self.db.commit()
        self.db.refresh(slot)
        return slot

    def delete(self, slot: EventSlot) -> None:
        self.db.delete(slot)
        self.db.commit()


class RegistrationSlotRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, slot_id: UUID, event_id: UUID, user_id: UUID) -> RegistrationSlot | None:
        return (
            self.db.query(RegistrationSlot)
            .filter(
                RegistrationSlot.slot_id == slot_id,
                RegistrationSlot.event_id == event_id,
                RegistrationSlot.user_id == user_id,
            )
            .first()
        )

    def list_by_registration(self, event_id: UUID, user_id: UUID) -> list[RegistrationSlot]:
        return (
            self.db.query(RegistrationSlot)
            .filter(
                RegistrationSlot.event_id == event_id,
                RegistrationSlot.user_id == user_id,
            )
            .all()
        )

    def count_by_slot(self, slot_id: UUID) -> int:
        return (
            self.db.query(RegistrationSlot)
            .filter(RegistrationSlot.slot_id == slot_id)
            .count()
        )

    def create(self, slot_id: UUID, event_id: UUID, user_id: UUID) -> RegistrationSlot:
        reg_slot = RegistrationSlot(slot_id=slot_id, event_id=event_id, user_id=user_id)
        self.db.add(reg_slot)
        self.db.commit()
        self.db.refresh(reg_slot)
        return reg_slot

    def delete(self, reg_slot: RegistrationSlot) -> None:
        self.db.delete(reg_slot)
        self.db.commit()


def get_event_slot_repository(
    db: Session = Depends(get_db),
) -> Generator[EventSlotRepository, None, None]:
    yield EventSlotRepository(db)


def get_registration_slot_repository(
    db: Session = Depends(get_db),
) -> Generator[RegistrationSlotRepository, None, None]:
    yield RegistrationSlotRepository(db)
