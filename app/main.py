from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from src.config import get_settings
from src.domain.health.controller import router as health_router
from src.domain.health.model import HealthLog
from src.domain.registration.model import Registration, ValidationToken
from src.domain.registration.controller import router as registration_router

logger = logging.getLogger(__name__)
settings = get_settings()

# Ensure SQLAlchemy metadata is populated before tests call Base.metadata.create_all().
MODELS = (HealthLog, Registration, ValidationToken)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting up %s v%s", settings.APP_NAME, settings.APP_VERSION)
    yield
    logger.info("Shutting down %s v%s", settings.APP_NAME, settings.APP_VERSION)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=f"{settings.APP_NAME} API",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(registration_router)
