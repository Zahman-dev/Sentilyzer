import hashlib
import os

# Add project root to path for imports
# This is necessary for the test environment to find the service modules
import sys
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
)

from services.common.app.db.base import ApiKey, Base, User
from services.common.app.db.session import get_db
from services.signals_api.app.main import create_app
from tests.integration.db_utils import (
    TestingSessionLocal,
    engine,
    override_get_db,
)

# --- App Setup ---
app = create_app()
app.dependency_overrides[get_db] = override_get_db


# --- Test Fixtures ---
@pytest.fixture(scope="module")
def client():
    """Create a test client for the app that persists for the module."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Create and drop database tables for the test module."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for each test function."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_user(db_session: Session):
    """Create a test user in the database for a single test."""
    user = User(
        email=f"testuser_{datetime.utcnow().isoformat()}@example.com",
        hashed_password="testpassword",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope="function")
def valid_api_key(db_session: Session, test_user: User):
    """Create a valid API key for the test user for a single test."""
    raw_key = "test_key_valid"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    api_key = ApiKey(
        user_id=test_user.id,
        key_hash=key_hash,
        expires_at=datetime.utcnow() + timedelta(days=1),
    )
    db_session.add(api_key)
    db_session.commit()
    return raw_key


@pytest.fixture(scope="function")
def expired_api_key(db_session: Session, test_user: User):
    """Create an expired API key for the test user for a single test."""
    raw_key = "test_key_expired"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    api_key = ApiKey(
        user_id=test_user.id,
        key_hash=key_hash,
        expires_at=datetime.utcnow() - timedelta(days=1),
    )
    db_session.add(api_key)
    db_session.commit()
    return raw_key


class TestSignalsApi:
    def test_health_check(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_get_signals_unauthenticated(self, client: TestClient):
        response = client.post(
            "/v1/signals",
            json={"start_date": "2023-01-01", "end_date": "2023-01-31"},
        )
        assert response.status_code == 403

    def test_get_signals_invalid_key(self, client: TestClient):
        response = client.post(
            "/v1/signals",
            headers={"Authorization": "Bearer invalidkey"},
            json={"start_date": "2023-01-01", "end_date": "2023-01-31"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or expired API key"

    def test_get_signals_expired_key(self, client: TestClient, expired_api_key: str):
        response = client.post(
            "/v1/signals",
            headers={"Authorization": f"Bearer {expired_api_key}"},
            json={"start_date": "2023-01-01", "end_date": "2023-01-31"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "API key has expired"

    def test_get_signals_valid_key(self, client: TestClient, valid_api_key: str):
        response = client.post(
            "/v1/signals",
            headers={"Authorization": f"Bearer {valid_api_key}"},
            json={"start_date": "2023-01-01", "end_date": "2023-01-31"},
        )
        # The response should be 200 even if no data is found for the query.
        assert response.status_code == 200
        assert "signals" in response.json()
