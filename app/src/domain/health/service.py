"""Application service for health checks."""

from src.config import get_settings

from .repository import HealthRepository
from .schemas import HealthResponse


class HealthService:
    """Coordinates health check use-cases."""

    def __init__(self, repository: HealthRepository) -> None:
        self._repository = repository
        self._settings = get_settings()

    def check(self) -> HealthResponse:
        """Persist an 'ok' log and return health response data."""
        log = self._repository.create_log(status="ok")
        return HealthResponse(
            status=log.status,
            version=self._settings.APP_VERSION,
            timestamp=log.checked_at,
        )
