"""Tests for event registration."""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.domain.registration.model import Registration
from src.domain.registration.repository import RegistrationRepository
from src.domain.registration.service import RegistrationService


def test_register_endpoint_creates_registration(client: TestClient) -> None:
    event_id = str(uuid4())
    user_id = str(uuid4())

    response = client.post("/register", json={"eventId": event_id, "userId": user_id})

    assert response.status_code == 201
    payload = response.json()
    assert payload["eventId"] == event_id
    assert payload["userId"] == user_id
    assert payload["registrationTimestamp"] is not None
    assert payload["confirmationTimestamp"] is None


def test_registration_repository_persists_row(db_session: Session) -> None:
    repository = RegistrationRepository(db_session)
    event_id = uuid4()
    user_id = uuid4()

    registration = repository.create(event_id, user_id)

    assert registration.event_id == event_id
    assert registration.user_id == user_id
    assert registration.registration_timestamp is not None
    assert registration.confirmation_timestamp is None


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

    assert registration.registration_timestamp is not None
    assert isinstance(registration.registration_timestamp, datetime)
    assert registration.registration_timestamp.tzinfo is not None
    assert registration.confirmation_timestamp is None