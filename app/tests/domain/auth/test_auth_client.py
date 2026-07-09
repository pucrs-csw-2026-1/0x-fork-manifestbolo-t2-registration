"""Tests for the Auth service client."""

from uuid import uuid4

from fastapi import HTTPException
import httpx
import pytest

from src.domain.auth.client import AuthClient


def test_validate_token_returns_active_user() -> None:
    user_id = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/users/me"
        assert request.headers["Authorization"] == "Bearer access-token"
        return httpx.Response(
            200,
            json={
                "id": str(user_id),
                "email": "user@example.com",
                "username": "user",
                "access_level": "PARTICIPANT",
                "is_active": True,
                "first_name": "Ignored",
            },
        )

    client = AuthClient(
        base_url="http://auth.test",
        transport=httpx.MockTransport(handler),
    )

    user = client.validate_token("access-token")

    assert user.id == user_id
    assert user.email == "user@example.com"
    assert user.username == "user"


@pytest.mark.parametrize("status_code", [401, 403])
def test_validate_token_rejects_auth_failures(status_code: int) -> None:
    client = AuthClient(
        base_url="http://auth.test",
        transport=httpx.MockTransport(lambda _: httpx.Response(status_code)),
    )

    with pytest.raises(HTTPException) as exc_info:
        client.validate_token("bad-token")

    assert exc_info.value.status_code == 401


def test_validate_token_rejects_inactive_user() -> None:
    client = AuthClient(
        base_url="http://auth.test",
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                json={
                    "id": str(uuid4()),
                    "email": "user@example.com",
                    "username": "user",
                    "access_level": "PARTICIPANT",
                    "is_active": False,
                },
            )
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        client.validate_token("inactive-token")

    assert exc_info.value.status_code == 401


@pytest.mark.parametrize(
    ("transport", "expected_status"),
    [
        (httpx.MockTransport(lambda _: httpx.Response(500)), 503),
        (
            httpx.MockTransport(
                lambda request: (_ for _ in ()).throw(
                    httpx.TimeoutException("timeout", request=request)
                )
            ),
            503,
        ),
    ],
)
def test_validate_token_maps_auth_unavailable(
    transport: httpx.MockTransport,
    expected_status: int,
) -> None:
    client = AuthClient(base_url="http://auth.test", transport=transport)

    with pytest.raises(HTTPException) as exc_info:
        client.validate_token("access-token")

    assert exc_info.value.status_code == expected_status
