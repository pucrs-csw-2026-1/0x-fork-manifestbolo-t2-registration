"""Integration smoke test between ManifestBolo and the live auth-service."""

from uuid import uuid4

from fastapi.testclient import TestClient
import httpx
import pytest

from src.config import get_settings

AUTH_ADMIN_EMAIL = "admin@local.dev"
AUTH_ADMIN_PASSWORD = "Admin@123"
PARTICIPANT_PASSWORD = "Participant@123"


def _login(email: str, password: str) -> str:
    settings = get_settings()
    with httpx.Client(base_url=settings.AUTH_SERVICE_BASE_URL, timeout=10.0) as client:
        response = client.post(
            "/auth/login",
            data={
                "username": email,
                "password": password,
            },
        )
    response.raise_for_status()
    return str(response.json()["access_token"])


def _login_admin() -> str:
    return _login(AUTH_ADMIN_EMAIL, AUTH_ADMIN_PASSWORD)


def _register_participant() -> tuple[str, str]:
    suffix = uuid4().hex[:12]
    email = f"participant-{suffix}@local.dev"
    settings = get_settings()

    with httpx.Client(base_url=settings.AUTH_SERVICE_BASE_URL, timeout=10.0) as client:
        response = client.post(
            "/users/register",
            json={
                "first_name": "Integration",
                "last_name": "Participant",
                "username": f"part.{suffix}",
                "email": email,
                "password": PARTICIPANT_PASSWORD,
            },
        )
    response.raise_for_status()
    payload = response.json()
    assert payload["access_level"] == "PARTICIPANT"
    return str(payload["id"]), email


@pytest.mark.integration
def test_manifestbolo_accepts_live_auth_admin_token(client: TestClient) -> None:
    access_token = _login_admin()
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    list_response = client.get(
        f"/events/{uuid4()}/registrations",
        headers=auth_headers,
    )
    assert list_response.status_code == 200
    assert list_response.json() == []

    register_response = client.post(
        "/register",
        json={
            "eventId": str(uuid4()),
            "userId": str(uuid4()),
        },
        headers=auth_headers,
    )
    assert register_response.status_code == 201

    check_in_response = client.get(
        f"/events/{uuid4()}/guests/{uuid4()}/check-in",
        headers=auth_headers,
    )
    assert check_in_response.status_code == 404


@pytest.mark.integration
def test_manifestbolo_rejects_live_auth_participant_on_operational_routes(
    client: TestClient,
) -> None:
    participant_id, participant_email = _register_participant()
    access_token = _login(participant_email, PARTICIPANT_PASSWORD)
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    list_response = client.get(
        f"/events/{uuid4()}/registrations",
        headers=auth_headers,
    )
    assert list_response.status_code == 403

    check_in_response = client.get(
        f"/events/{uuid4()}/guests/{participant_id}/check-in",
        headers=auth_headers,
    )
    assert check_in_response.status_code == 403

    register_other_user_response = client.post(
        "/register",
        json={
            "eventId": str(uuid4()),
            "userId": str(uuid4()),
        },
        headers=auth_headers,
    )
    assert register_other_user_response.status_code == 403
