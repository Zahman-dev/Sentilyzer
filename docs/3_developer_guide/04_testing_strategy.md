# Testing Strategy

This document explains the testing philosophy, tools, and best practices used to ensure code quality and system reliability in the Sentilyzer project.

## Philosophy

Tests in the project aim to **simulate the production environment** as much as possible. Abstract `mocks` and fake objects are strategically avoided. Instead, **lightweight versions of real components** specifically configured for testing are used (for example, an in-memory SQLite database instead of a full PostgreSQL).

The main goal is to verify not only that the code works logically correctly but also that it behaves as expected at integration points (database, Pydantic models, AI model, etc.).

## Tools

- **Test Framework:** `pytest`
- **Code Coverage:** `pytest-cov`

## Test Types

- **Unit Tests (`/tests/unit`):** Tests the logic of a single function, method, or class in isolation from external dependencies. They are typically used for complex algorithms or data processing functions.
- **Integration Tests (`/tests/integration`):** Verifies how multiple components of the system work together. These tests are the backbone of the project. An example integration test would send a request to an API endpoint and check if it made the correct change in the database.

## Key `pytest` Fixtures

Fixtures defined in `tests/conftest.py` ensure tests are clean and reproducible.

- **`test_db`**:
    - Creates a **brand new, empty SQLite database** for each test function.
    - Destroys this database when the test completes.
    - This ensures each test runs in a completely isolated environment.

- **`client`**:
    - Uses FastAPI's `TestClient` to programmatically send HTTP requests to API endpoints.
    - Configured to communicate with the test database using the `test_db` fixture.

- **`mock_finbert_model`**:
    - Uses `monkeypatch` to replace the real FinBERT model with a simple function that mimics its behavior to avoid the slowness of loading the actual model.
    - This ensures tests run quickly while still testing the core logic of the project.

## How to Add a New Test?

1.  **Choose the Right Directory:** Is your test checking a single function (`unit`) or the interaction of multiple parts (`integration`)?
2.  **File Name:** Your test file should start with `test_` (e.g., `test_api_auth.py`).
3.  **Function Name:** Your test function should start with `test_` (e.g., `test_should_return_401_for_invalid_key`).
4.  **Use Fixtures:** If you need a database or API client, just specify them as function parameters:
    ```python
    from fastapi.testclient import TestClient

    def test_health_check_returns_200(client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    ```

> **Tip:** To run tests, simply type `pytest` in the terminal while in the main directory. Use `pytest -v` for more detailed output.
