"""Tests for event registration."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from src.database import Base
from src.domain.registration.enums import RegistrationStatus
from src.domain.registration.model import Registration, ValidationToken
from src.domain.registration.repository import RegistrationRepository
from src.domain.registration.service import RegistrationService


def _seed_registration_with_token(
    db_session: Session,
    *,
    token: str = "XY34ZW78",
    status: RegistrationStatus = RegistrationStatus.REGISTERED,
    expires_at: datetime | None = None,
) -> ValidationToken:
    """Create a registration plus its validation token and return the token."""
    event_id = uuid4()
    user_id = uuid4()
    db_session.add(Registration(event_id=event_id, user_id=user_id, status=status))
    validation_token = ValidationToken(
        event_id=event_id,
        user_id=user_id,
        token=token,
        expires_at=expires_at or datetime.now(UTC) + timedelta(hours=1),
    )
    db_session.add(validation_token)
    db_session.commit()
    db_session.refresh(validation_token)
    return validation_token


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


def test_validate_check_in_returns_registration_state(
    client: TestClient, db_session: Session
) -> None:
    event_id = uuid4()
    user_id = uuid4()
    registration = Registration(
        event_id=event_id,
        user_id=user_id,
        status=RegistrationStatus.CONFIRMED,
    )
    db_session.add(registration)
    db_session.commit()

    response = client.get(f"/events/{event_id}/guests/{user_id}/check-in")

    assert response.status_code == 200
    payload = response.json()
    assert payload["eventId"] == str(event_id)
    assert payload["userId"] == str(user_id)
    assert payload["status"] == RegistrationStatus.CONFIRMED.value
    assert payload["createdAt"] is not None
    assert payload["updatedAt"] is None


def test_validate_check_in_returns_false_for_missing_registration(
    client: TestClient,
) -> None:
    event_id = uuid4()
    user_id = uuid4()

    response = client.get(f"/events/{event_id}/guests/{user_id}/check-in")

    assert response.status_code == 404


def test_confirm_registration_succeeds_with_valid_token(
    client: TestClient, db_session: Session
) -> None:
    validation_token = _seed_registration_with_token(db_session, token="ABCD1234")

    response = client.post(
        f"/events/confirmation/{validation_token.id}",
        json={"token": "ABCD1234"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["confirmationId"] == str(validation_token.id)
    assert payload["eventId"] == str(validation_token.event_id)
    assert payload["userId"] == str(validation_token.user_id)
    assert payload["confirmedAt"] is not None

    registration = RegistrationRepository(db_session).get_by_event_and_user(
        validation_token.event_id, validation_token.user_id
    )
    assert registration is not None
    assert registration.status == RegistrationStatus.CONFIRMED


def test_confirm_registration_rejects_wrong_token(
    client: TestClient, db_session: Session
) -> None:
    validation_token = _seed_registration_with_token(db_session, token="ABCD1234")

    response = client.post(
        f"/events/confirmation/{validation_token.id}",
        json={"token": "WRONG999"},
    )

    assert response.status_code == 400


def test_confirm_registration_rejects_expired_token(
    client: TestClient, db_session: Session
) -> None:
    validation_token = _seed_registration_with_token(
        db_session,
        token="ABCD1234",
        expires_at=datetime.now(UTC) - timedelta(hours=1),
    )

    response = client.post(
        f"/events/confirmation/{validation_token.id}",
        json={"token": "ABCD1234"},
    )

    assert response.status_code == 410


def test_confirm_registration_rejects_already_confirmed(
    client: TestClient, db_session: Session
) -> None:
    validation_token = _seed_registration_with_token(
        db_session,
        token="ABCD1234",
        status=RegistrationStatus.CONFIRMED,
    )

    response = client.post(
        f"/events/confirmation/{validation_token.id}",
        json={"token": "ABCD1234"},
    )

    assert response.status_code == 409


def test_confirm_registration_returns_404_for_unknown_confirmation(
    client: TestClient,
) -> None:
    response = client.post(
        f"/events/confirmation/{uuid4()}",
        json={"token": "ABCD1234"},
    )

    assert response.status_code == 404


def test_confirm_registration_rejects_malformed_token(client: TestClient) -> None:
    response = client.post(
        f"/events/confirmation/{uuid4()}",
        json={"token": "short"},
    )

    assert response.status_code == 422


def test_validation_token_belongs_to_registration_domain_metadata() -> None:
    assert ValidationToken.__table__.name == "authentication_tokens"
    assert Base.metadata.tables["authentication_tokens"] is ValidationToken.__table__
