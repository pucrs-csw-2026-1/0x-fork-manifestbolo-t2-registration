"""Tests for event registration."""

from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from src.database import Base
from src.domain.registration.enums import RegistrationStatus
from src.domain.registration.model import (
    ActivityRegistration,
    Registration,
    ValidationToken,
)
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


def test_list_activity_registrations_returns_user_ids(
    client: TestClient, db_session: Session
) -> None:
    activity_id = uuid4()
    event_id = uuid4()
    user_ids = [uuid4(), uuid4()]
    for user_id in user_ids:
        db_session.add(
            ActivityRegistration(
                activity_id=activity_id,
                user_id=user_id,
                event_id=event_id,
            )
        )
    db_session.commit()

    response = client.get(f"/activities/{activity_id}/registrations")

    assert response.status_code == 200
    assert sorted(response.json()) == sorted(str(uid) for uid in user_ids)


def test_list_activity_registrations_returns_empty_list_when_none(
    client: TestClient,
) -> None:
    activity_id = uuid4()

    response = client.get(f"/activities/{activity_id}/registrations")

    assert response.status_code == 200
    assert response.json() == []


def test_activity_registration_repository_finds_row(db_session: Session) -> None:
    repository = RegistrationRepository(db_session)
    activity_id = uuid4()
    user_id = uuid4()
    event_id = uuid4()

    db_session.add(
        ActivityRegistration(
            activity_id=activity_id,
            user_id=user_id,
            event_id=event_id,
        )
    )
    db_session.commit()

    registration = repository.get_by_activity_and_user(activity_id, user_id)

    assert registration is not None
    assert registration.activity_id == activity_id
    assert registration.user_id == user_id
    assert registration.event_id == event_id


def test_activity_registration_service_returns_row(db_session: Session) -> None:
    repository = RegistrationRepository(db_session)
    service = RegistrationService(repository)
    activity_id = uuid4()
    user_id = uuid4()
    event_id = uuid4()

    db_session.add(
        ActivityRegistration(
            activity_id=activity_id,
            user_id=user_id,
            event_id=event_id,
        )
    )
    db_session.commit()

    registration = service.get_activity_registration(activity_id, user_id)

    assert registration is not None
    assert registration.activity_id == activity_id
    assert registration.user_id == user_id
    assert registration.event_id == event_id


def test_get_activity_registration_endpoint_returns_row(
    client: TestClient, db_session: Session
) -> None:
    activity_id = uuid4()
    user_id = uuid4()
    event_id = uuid4()

    db_session.add(
        ActivityRegistration(
            activity_id=activity_id,
            user_id=user_id,
            event_id=event_id,
        )
    )
    db_session.commit()

    response = client.get(f"/activities/{activity_id}/users/{user_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["activityId"] == str(activity_id)
    assert payload["userId"] == str(user_id)
    assert payload["eventId"] == str(event_id)
    assert payload["createdAt"] is not None
    assert payload["updatedAt"] is not None


def test_activity_registration_repository_creates_row(db_session: Session) -> None:
    repository = RegistrationRepository(db_session)
    activity_id = uuid4()
    user_id = uuid4()
    event_id = uuid4()

    registration = repository.create_activity_registration(
        activity_id,
        user_id,
        event_id,
    )

    assert registration.activity_id == activity_id
    assert registration.user_id == user_id
    assert registration.event_id == event_id
    assert registration.created_at is not None
    assert registration.updated_at is not None


def test_activity_registration_service_creates_row(db_session: Session) -> None:
    repository = RegistrationRepository(db_session)
    service = RegistrationService(repository)
    activity_id = uuid4()
    user_id = uuid4()
    event_id = uuid4()

    registration = service.register_activity(activity_id, user_id, event_id)

    assert registration.activity_id == activity_id
    assert registration.user_id == user_id
    assert registration.event_id == event_id


def test_post_activity_registration_endpoint_creates_row(
    client: TestClient, db_session: Session
) -> None:
    activity_id = uuid4()
    user_id = uuid4()
    event_id = uuid4()

    response = client.post(
        "/activities/registrations",
        json={
            "activityId": str(activity_id),
            "userId": str(user_id),
            "eventId": str(event_id),
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["activityId"] == str(activity_id)
    assert payload["userId"] == str(user_id)
    assert payload["eventId"] == str(event_id)
    assert payload["createdAt"] is not None
    assert payload["updatedAt"] is not None


def test_validation_token_belongs_to_registration_domain_metadata() -> None:
    assert ValidationToken.__table__.name == "authentication_tokens"
    assert Base.metadata.tables["authentication_tokens"] is ValidationToken.__table__
