"""
Integration tests for the API Authentication mechanism.

These tests verify that the API correctly handles valid, invalid, expired,
and unauthorized API keys, ensuring the security layer works as expected.
"""

from fastapi.testclient import TestClient

# --- Test Suite for API Authentication ---


class TestApiAuthentication:
    """
    Tests the authentication and authorization logic of the /v1/signals endpoint.
    """

    def test_get_signals_no_auth_header(self, api_client: TestClient):
        """
        Tests that a request without any Authorization header is rejected.
        FastAPI's Security dependency should handle this.
        """
        response = api_client.post("/v1/signals", json={})
        # The specific code for missing header can be 403 or 401 depending on server config,
        # but it must be an error. FastAPI's default is 403 for missing dependency.
        assert response.status_code == 403

    def test_get_signals_invalid_bearer_token(self, api_client: TestClient):
        """Tests that a request with a malformed or non-existent key is rejected."""
        response = api_client.post(
            "/v1/signals",
            headers={"Authorization": "Bearer invalid-key-123"},
            json={"ticker": "AAPL", "start_date": "2023-01-01", "end_date": "2023-01-31"},
        )
        assert response.status_code == 401
        assert "Invalid or expired API key" in response.json()["detail"]

    def test_get_signals_expired_key(
        self, api_client: TestClient, test_user, api_key_factory
    ):
        """Tests that a request with an expired API key is rejected."""
        # Arrange: Create an expired key
        expired_key = api_key_factory(
            user_id=test_user.id,
            expires_in_days=-1,  # Expired yesterday
        )

        # Act
        response = api_client.post(
            "/v1/signals",
            headers={"Authorization": f"Bearer {expired_key.raw_key}"},
            json={"ticker": "AAPL", "start_date": "2023-01-01", "end_date": "2023-01-31"},
        )

        # Assert
        assert response.status_code == 401
        assert "API key has expired" in response.json()["detail"]

    def test_get_signals_inactive_user(
        self, api_client: TestClient, inactive_user, api_key_factory
    ):
        """
        Tests that a request with a valid key belonging to an inactive user is rejected.
        """
        # Arrange: Create a valid key for an inactive user
        key_for_inactive_user = api_key_factory(user_id=inactive_user.id)

        # Act
        response = api_client.post(
            "/v1/signals",
            headers={"Authorization": f"Bearer {key_for_inactive_user.raw_key}"},
            json={"ticker": "AAPL", "start_date": "2023-01-01", "end_date": "2023-01-31"},
        )

        # Assert
        assert response.status_code == 401
        assert "User account is inactive" in response.json()["detail"]

    def test_get_signals_inactive_key(
        self, api_client: TestClient, test_user, api_key_factory
    ):
        """
        Tests that a request with an API key marked as inactive is rejected.
        """
        # Arrange: Create an inactive key
        inactive_key = api_key_factory(user_id=test_user.id, is_active=False)

        # Act
        response = api_client.post(
            "/v1/signals",
            headers={"Authorization": f"Bearer {inactive_key.raw_key}"},
            json={"ticker": "AAPL", "start_date": "2023-01-01", "end_date": "2023-01-31"},
        )

        # Assert
        assert response.status_code == 401
        assert "Invalid or expired API key" in response.json()["detail"]

    def test_get_signals_valid_key(
        self, api_client: TestClient, test_user, api_key_factory
    ):
        """
        Tests that a request with a valid API key is successful.
        The endpoint should return 200 OK even if no data is found, as the request is valid.
        """
        # Arrange: Create a valid key for an active user
        valid_key = api_key_factory(user_id=test_user.id)

        # Act
        response = api_client.post(
            "/v1/signals",
            headers={"Authorization": f"Bearer {valid_key.raw_key}"},
            json={"ticker": "FAKE", "start_date": "2023-01-01", "end_date": "2023-01-31"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total_count" in data
        assert data["total_count"] == 0
