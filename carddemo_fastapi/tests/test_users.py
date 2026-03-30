"""Tests for user management endpoints (CRUD on /api/users).

Ports validation from COBOL programs COUSR00C (list), COUSR01C (add),
COUSR02C (view/update), and COUSR03C (delete). All endpoints require
admin access (user_type='A').
"""


def test_list_users(client, seed_data, admin_headers):
    """Admin can list users; response has paginated items list."""
    response = client.get("/api/users", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["total_count"] >= 3


def test_list_users_unauthorized(client, seed_data, user_headers):
    """Regular user is denied access to user list (admin-only)."""
    response = client.get("/api/users", headers=user_headers)
    assert response.status_code == 403


def test_add_user(client, seed_data, admin_headers):
    """Admin can create a new user; response contains 'has been added'."""
    response = client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "usr_id": "newusr1",
            "usr_fname": "New",
            "usr_lname": "User",
            "usr_pwd": "NEWPWD01",
            "usr_type": "U",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "has been added" in data["message"]


def test_add_user_duplicate(client, seed_data, admin_headers):
    """Creating a user with an existing usr_id returns 409."""
    response = client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "usr_id": "admin1",
            "usr_fname": "Dup",
            "usr_lname": "User",
            "usr_pwd": "DUPPWD01",
            "usr_type": "A",
        },
    )
    assert response.status_code == 409
    data = response.json()
    assert "already exist" in data["error_message"]


def test_add_user_empty_fields(client, seed_data, admin_headers):
    """Creating a user with an empty first name returns 422."""
    response = client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "usr_id": "emptyusr",
            "usr_fname": "",
            "usr_lname": "User",
            "usr_pwd": "EMPTYPWD",
            "usr_type": "U",
        },
    )
    assert response.status_code == 422


def test_get_user(client, seed_data, admin_headers):
    """Admin can retrieve a specific user by ID."""
    response = client.get("/api/users/admin1", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["usr_id"] == "ADMIN1"


def test_update_user(client, seed_data, admin_headers):
    """Admin can update a user's first name; response says 'has been updated'."""
    response = client.put(
        "/api/users/user001",
        headers=admin_headers,
        json={"usr_fname": "Updated"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "has been updated" in data["message"]


def test_update_user_no_changes(client, seed_data, admin_headers):
    """Submitting unchanged data returns 422 with 'modify to update'."""
    response = client.put(
        "/api/users/user001",
        headers=admin_headers,
        json={"usr_fname": "Regular"},
    )
    assert response.status_code == 422
    data = response.json()
    assert "modify to update" in data["error_message"]


def test_delete_user(client, seed_data, admin_headers):
    """Admin can delete a user; response says 'has been deleted'."""
    response = client.delete("/api/users/user002", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "has been deleted" in data["message"]


def test_delete_user_not_found(client, seed_data, admin_headers):
    """Deleting a non-existent user returns 404."""
    response = client.delete("/api/users/NOUSER", headers=admin_headers)
    assert response.status_code == 404
