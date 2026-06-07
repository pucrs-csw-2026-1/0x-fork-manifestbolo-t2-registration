"""FastAPI dependencies for authentication and role-based authorization."""

from collections.abc import Callable
from enum import StrEnum
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .client import AuthClient, get_auth_client
from .schemas import UserResponse

bearer_scheme = HTTPBearer(auto_error=False)


class Role(StrEnum):
    """Roles emitted by the auth-service access_level field."""

    PARTICIPANT = "PARTICIPANT"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_client: AuthClient = Depends(get_auth_client),
) -> UserResponse:
    """Resolve the authenticated user from a Bearer access token."""

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer authentication token",
        )

    return auth_client.validate_token(credentials.credentials)


def _user_role(user: UserResponse) -> Role:
    try:
        return Role(user.access_level.upper())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unsupported authenticated user role",
        ) from exc


def require_roles(*roles: Role) -> Callable[[UserResponse], UserResponse]:
    """Return a dependency that accepts only users with one of the given roles."""

    allowed_roles = set(roles)

    def _dependency(
        auth_user: UserResponse = Depends(get_current_user),
    ) -> UserResponse:
        if _user_role(auth_user) not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role for this operation",
            )
        return auth_user

    return _dependency


require_manager_or_admin = require_roles(Role.MANAGER, Role.ADMIN)


def is_admin(user: UserResponse) -> bool:
    return _user_role(user) is Role.ADMIN


def is_manager_or_admin(user: UserResponse) -> bool:
    return _user_role(user) in {Role.MANAGER, Role.ADMIN}


def ensure_self_or_admin(auth_user: UserResponse, target_user_id: UUID) -> None:
    """Allow users to mutate themselves and admins to mutate any registration."""

    if auth_user.id == target_user_id or is_admin(auth_user):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Authenticated user cannot operate on this registration",
    )


def ensure_self_or_manager_or_admin(
    auth_user: UserResponse,
    target_user_id: UUID,
) -> None:
    """Allow self access, operational access for managers, and full admin access."""

    if auth_user.id == target_user_id or is_manager_or_admin(auth_user):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Authenticated user cannot access this registration",
    )
