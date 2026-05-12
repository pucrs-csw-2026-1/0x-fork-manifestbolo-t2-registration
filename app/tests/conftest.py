"""Shared pytest fixtures for application tests."""

from collections.abc import Generator
import contextlib
from pathlib import Path
import sys

from faker import Faker
from fastapi.testclient import TestClient
from moto import mock_aws
import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

from main import app
from src.database import Base, get_db

# Ensure app root is importable regardless of where pytest is executed from.
APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

# ---------------------------------------------------------------------------
# PostgreSQL container — shared across the entire test session for speed.
# ---------------------------------------------------------------------------

POSTGRES_IMAGE = "postgres:15-alpine"


@pytest.fixture(scope="session")
def pg_engine() -> Generator[Engine, None, None]:
    """Start a real PostgreSQL container once per test session and create schema."""
    with PostgresContainer(POSTGRES_IMAGE) as pg:
        engine = create_engine(pg.get_connection_url(), echo=False)
        Base.metadata.create_all(bind=engine)
        yield engine
        Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Isolated session — each test runs inside a transaction that is rolled back.
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_session(pg_engine: Engine) -> Generator[Session, None, None]:
    """Provide an isolated Postgres session via nested transaction rollback per test.

    Each test runs inside a SAVEPOINT managed by SQLAlchemy's begin_nested().
    If the test triggers an IntegrityError (which aborts the Postgres transaction),
    the session is expired and the outer transaction still rolls back cleanly.
    """
    connection = pg_engine.connect()
    outer_tx = connection.begin()

    session_factory = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = session_factory()

    nested = session.begin_nested()  # SAVEPOINT

    try:
        yield session
    finally:
        session.close()
        # Roll back to the SAVEPOINT — if the session is already in an error
        # state, expire_all() resets it so the outer rollback can proceed.
        with contextlib.suppress(Exception):
            nested.rollback()
        outer_tx.rollback()
        connection.close()


# ---------------------------------------------------------------------------
# FastAPI test client with DB override.
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(db_session: Session, pg_engine: Engine) -> Generator[TestClient, None, None]:
    """Provide a FastAPI test client with database dependency override."""
    import main as main_module

    test_session_factory = sessionmaker(bind=pg_engine, autocommit=False, autoflush=False)
    original_session_local = main_module.SessionLocal
    main_module.SessionLocal = test_session_factory

    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        main_module.SessionLocal = original_session_local


# ---------------------------------------------------------------------------
# AWS mock
# ---------------------------------------------------------------------------

@pytest.fixture()
def aws_mock() -> Generator[None, None, None]:
    """Mock AWS services using Moto for isolated tests."""
    with mock_aws():
        yield


# ---------------------------------------------------------------------------
# Faker — randomized test data for each test run.
# ---------------------------------------------------------------------------

@pytest.fixture()
def fake() -> Faker:
    """Return a Faker instance with a random seed per test."""
    return Faker()
