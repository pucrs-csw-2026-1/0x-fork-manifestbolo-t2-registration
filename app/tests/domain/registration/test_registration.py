"""Tests for event registration."""

from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from src.database import Base
from src.domain.registration.enums import RegistrationStatus
from src.domain.registration.model import Registration, ValidationToken
from src.domain.registration.repository import RegistrationRepository
from src.domain.registration.service import RegistrationService


@pytest.mark.xfail(reason="POST /events/{event_id}/guests ainda não implementado (501)")
def test_register_endpoint_creates_registration(client: TestClient) -> None:
    event_id = uuid4()
    user_id = str(uuid4())

    response = client.post(f"/events/{event_id}/guests", json={"userId": user_id})

    assert response.status_code == 201
    payload = response.json()
    assert payload["eventId"] == event_id
    assert payload["userId"] == user_id
    assert payload["status"] == RegistrationStatus.REGISTERED.value
    assert payload["createdAt"] is not None
    assert payload["updatedAt"] is None


def test_registration_repository_persists_row(db_session: Session) -> None:
    repository = RegistrationRepository(db_session)
    event_id = uuid4()
    user_id = uuid4()

    registration = repository.create(event_id, user_id)

    assert registration.event_id == event_id
    assert registration.user_id == user_id
    assert registration.status == RegistrationStatus.REGISTERED
    assert registration.created_at is not None
    assert registration.updated_at is None


def test_registration_service_rejects_duplicates(db_session: Session) -> None:
    repository = RegistrationRepository(db_session)
    service = RegistrationService(repository)
    event_id = uuid4()
    user_id = uuid4()

    service.register(event_id, user_id)

    try:
        service.register(event_id, user_id)
    except Exception as exc:  # noqa: BLE001
        assert getattr(exc, "status_code", None) == 409
    else:
        raise AssertionError("expected duplicate registration to fail")


def test_registration_model_defaults_timestamp(db_session: Session) -> None:
    registration = Registration(event_id=uuid4(), user_id=uuid4())
    db_session.add(registration)
    db_session.commit()

    assert registration.status == RegistrationStatus.REGISTERED
    assert registration.created_at is not None
    assert isinstance(registration.created_at, datetime)
    assert registration.created_at.tzinfo is not None
    assert registration.updated_at is None


def test_registration_updated_at_is_populated_on_update(db_session: Session) -> None:
    registration = Registration(event_id=uuid4(), user_id=uuid4())
    db_session.add(registration)
    db_session.commit()

    registration.status = RegistrationStatus.CONFIRMED
    db_session.commit()
    db_session.refresh(registration)

    assert registration.status == RegistrationStatus.CONFIRMED
    assert registration.updated_at is not None


def test_validation_token_belongs_to_registration_domain_metadata() -> None:
    assert ValidationToken.__table__.name == "authentication_tokens"
    assert Base.metadata.tables["authentication_tokens"] is ValidationToken.__table__
