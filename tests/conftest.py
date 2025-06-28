"""
Main configuration file for pytest.

This file contains shared fixtures that can be used across all test files.
Fixtures defined here have a global scope unless specified otherwise.
"""
import hashlib
import os
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from services.common.app.db.models import ApiKey, Base, User
from services.common.app.db.session import get_db
from services.signals_api.app.main import app


@pytest.fixture(scope="session", autouse=True)
def _setup_test_environment():
    """
    Setup test environment variables before any tests run.
    This ensures all services use the test database.
    """
    # Set test database URL for all services
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    # Set test Redis URL
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"
    yield
    # Clean up
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]
    if "REDIS_URL" in os.environ:
        del os.environ["REDIS_URL"]


@pytest.fixture(scope="session")
def db_engine():
    """
    Session-scoped, in-memory SQLite engine for tests.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="session")
def db_session_factory(db_engine):
    """
    Returns a sessionmaker factory bound to the test engine.
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=db_engine)


@pytest.fixture()
def db_session(db_session_factory):
    """
    Returns a new session for each test, rolled back after test.
    """
    session = db_session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="module")
def api_client(db_session_factory):
    """
    Provides a TestClient for making API requests in tests.
    This client uses an overridden database session from our test factory.
    """

    def override_get_db():
        """FastAPI dependency override to use the test database session."""
        try:
            db = db_session_factory()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    # Clean up dependency override after tests
    app.dependency_overrides.clear()


@pytest.fixture()
def test_user(db_session):
    """Creates and returns a standard, active user for testing."""
    user = User(
        email=f"testuser_{datetime.utcnow().isoformat()}@example.com",
        hashed_password="test_password_hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def inactive_user(db_session):
    """Creates and returns an inactive user for testing auth scenarios."""
    user = User(
        email=f"inactive_user_{datetime.utcnow().isoformat()}@example.com",
        hashed_password="test_password_hash",
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def api_key_factory(db_session):
    """Factory fixture to create API keys for different scenarios."""

    def _factory(
        user_id: int,
        expires_in_days: int = 7,
        is_active: bool = True,
    ) -> ApiKey:
        key = hashlib.sha256(str(datetime.utcnow().timestamp()).encode()).hexdigest()
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        api_key = ApiKey(
            key_hash=key_hash,
            user_id=user_id,
            expires_at=expires_at,
            is_active=is_active,
        )
        db_session.add(api_key)
        db_session.commit()
        db_session.refresh(api_key)
        # Add the raw key to the object for use in tests, it's not stored in DB
        api_key.raw_key = key
        return api_key

    return _factory
