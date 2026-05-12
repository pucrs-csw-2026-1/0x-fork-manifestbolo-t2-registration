"""HTTP controller for health endpoints."""

from collections.abc import Generator

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db

from .repository import HealthRepository
from .schemas import HealthResponse
from .service import HealthService

router = APIRouter(prefix="/health", tags=["health"])


def get_health_service(
    db: Session = Depends(get_db),
) -> Generator[HealthService, None, None]:
    """Build a health service instance with injected dependencies."""
    repository = HealthRepository(db)
    yield HealthService(repository)


@router.get("/", response_model=HealthResponse, summary="Health check")
def health_check(
    service: HealthService = Depends(get_health_service),
) -> HealthResponse:
    """Return API health information and persist a health log."""
    return service.check()
