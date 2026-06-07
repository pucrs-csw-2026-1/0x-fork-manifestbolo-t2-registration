"""HTTP client for the Auth service."""

import logging

from fastapi import Depends, HTTPException, status
import httpx

from src.config import Settings, get_settings

from .schemas import UserResponse

logger = logging.getLogger(__name__)


class AuthClient:
    """Encapsulates calls to the Auth service."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 5.0,
        transport: httpx.BaseTransport | None = None,
        settings: Settings | None = None,
    ) -> None:
        app_settings = settings or get_settings()
        self._base_url = base_url or app_settings.AUTH_SERVICE_BASE_URL
        self._timeout = timeout
        self._transport = transport

    def validate_token(self, token: str) -> UserResponse:
        """Validate a Bearer token against Auth /users/me."""

        try:
            with httpx.Client(
                base_url=self._base_url,
                timeout=self._timeout,
                transport=self._transport,
            ) as client:
                response = client.get(
                    "/users/me",
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.TimeoutException as exc:
            logger.warning("Auth service timeout while validating token")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service unavailable",
            ) from exc
        except httpx.RequestError as exc:
            logger.warning("Auth service request failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service unavailable",
            ) from exc

        if (
            status.HTTP_400_BAD_REQUEST
            <= response.status_code
            < status.HTTP_500_INTERNAL_SERVER_ERROR
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token",
            )

        if response.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service unavailable",
            )

        response.raise_for_status()
        user = UserResponse.model_validate(response.json())
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive authenticated user",
            )
        return user


def get_auth_client(
    settings: Settings = Depends(get_settings),
) -> AuthClient:
    """Return an Auth client instance for FastAPI dependency injection."""

    return AuthClient(settings=settings)
