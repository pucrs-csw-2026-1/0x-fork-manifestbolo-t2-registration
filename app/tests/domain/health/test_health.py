"""Automated tests for health domain."""

from datetime import UTC, datetime
from unittest.mock import create_autospec
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.config import get_settings
from src.domain.health.model import HealthLog
from src.domain.health.repository import HealthRepository
from src.domain.health.service import HealthService


def test_health_check_returns_200(client: TestClient) -> None:
    """Health endpoint should respond successfully."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_response_schema(client: TestClient) -> None:
    """Health endpoint response should contain required schema fields."""
    response = client.get("/health")
    payload = response.json()

    assert "status" in payload
    assert "version" in payload
    assert "timestamp" in payload


def test_health_check_status_is_ok(client: TestClient) -> None:
    """Health endpoint status field should be 'ok'."""
    response = client.get("/health")
    assert response.json()["status"] == "ok"


def test_health_repository_create_log(db_session: Session) -> None:
    """Repository should persist and return a new health log."""
    repository = HealthRepository(db_session)

    created_log = repository.create_log("ok")

    assert created_log.id is not None
    assert created_log.status == "ok"
    assert created_log.checked_at is not None


def test_health_repository_get_latest(db_session: Session) -> None:
    """Repository should return the most recently checked log entry."""
    repository = HealthRepository(db_session)

    older_log = HealthLog(
        id=uuid4(),
        status="ok",
        checked_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC),
    )
    newer_log = HealthLog(
        id=uuid4(),
        status="ok",
        checked_at=datetime(2026, 1, 1, 10, 0, 1, tzinfo=UTC),
    )
    db_session.add_all([older_log, newer_log])
    db_session.commit()

    latest = repository.get_latest()

    assert latest is not None
    assert latest.id == newer_log.id


def test_health_service_check() -> None:
    """Service should return typed response and use repository to create log."""
    now = datetime.now(UTC)
    created_log = HealthLog(id=uuid4(), status="ok", checked_at=now)
    repository_mock = create_autospec(HealthRepository, instance=True)
    repository_mock.create_log.return_value = created_log

    service = HealthService(repository=repository_mock)

    response = service.check()

    repository_mock.create_log.assert_called_once_with(status="ok")
    assert response.status == "ok"
    assert response.version == get_settings().APP_VERSION
    assert response.timestamp == now
