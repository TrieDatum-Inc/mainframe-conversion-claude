"""Tests for report endpoint (POST /api/reports).

Ports validation from COBOL program CORPT00C which accepts monthly,
yearly, or custom date range reports with a two-step confirmation flow.
"""


def test_submit_monthly_report(client, seed_data, admin_headers):
    """Confirmed monthly report returns 200 with submission message."""
    response = client.post(
        "/api/reports",
        headers=admin_headers,
        json={"report_type": "monthly", "confirm": "Y"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "report" in data["message"].lower()


def test_submit_yearly_report(client, seed_data, admin_headers):
    """Confirmed yearly report returns 200 with submission message."""
    response = client.post(
        "/api/reports",
        headers=admin_headers,
        json={"report_type": "yearly", "confirm": "Y"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "report" in data["message"].lower()


def test_submit_custom_report(client, seed_data, admin_headers):
    """Confirmed custom report with valid dates returns 200."""
    response = client.post(
        "/api/reports",
        headers=admin_headers,
        json={
            "report_type": "custom",
            "start_month": 1,
            "start_day": 1,
            "start_year": 2023,
            "end_month": 12,
            "end_day": 31,
            "end_year": 2023,
            "confirm": "Y",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "report" in data["message"].lower()


def test_submit_report_invalid_type(client, seed_data, admin_headers):
    """Invalid report type returns 422."""
    response = client.post(
        "/api/reports",
        headers=admin_headers,
        json={"report_type": "invalid", "confirm": "Y"},
    )
    assert response.status_code == 422


def test_submit_report_no_confirm(client, seed_data, admin_headers):
    """Unconfirmed report (confirm='N') returns 'Please confirm' prompt."""
    response = client.post(
        "/api/reports",
        headers=admin_headers,
        json={"report_type": "monthly", "confirm": "N"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "confirm" in data["message"].lower() or "Please" in data["message"]
