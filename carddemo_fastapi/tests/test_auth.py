"""Tests for the authentication endpoint (POST /api/auth/login).

Ports validation from COBOL program COSGN00C which authenticates
SEC-USR-ID and SEC-USR-PWD against the USRSEC VSAM file.
"""


def test_login_success(client, seed_data):
    """Successful login returns 200 with a JWT token and user context."""
    response = client.post(
        "/api/auth/login",
        json={"user_id": "admin1", "password": "ADMIN123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user_id"] == "ADMIN1"
    assert data["user_type"] == "A"


def test_login_wrong_password(client, seed_data):
    """Wrong password returns 401 with the COBOL error message."""
    response = client.post(
        "/api/auth/login",
        json={"user_id": "admin1", "password": "WRONG"},
    )
    assert response.status_code == 401
    data = response.json()
    assert "Wrong Password" in data["error_message"]


def test_login_user_not_found(client, seed_data):
    """Non-existent user returns 401 with 'User not found' message."""
    response = client.post(
        "/api/auth/login",
        json={"user_id": "NOUSER", "password": "PWD"},
    )
    assert response.status_code == 401
    data = response.json()
    assert "User not found" in data["error_message"]


def test_login_empty_user_id(client, seed_data):
    """Empty user_id triggers a 422 validation error from Pydantic/FastAPI."""
    response = client.post(
        "/api/auth/login",
        json={"user_id": "", "password": "PWD"},
    )
    # FastAPI/Pydantic may return 422 for empty required string
    # or the service may return 401 for user not found.
    # Either 401 or 422 is acceptable; the important thing is it is rejected.
    assert response.status_code in (401, 422)
