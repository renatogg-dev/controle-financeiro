"""API tests for the dashboard summary endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_summary_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/dashboard/summary", params={"month": "2026-01"})

    assert response.status_code == 401


def test_summary_shape(auth_client: TestClient) -> None:
    category_id = auth_client.get("/api/categories").json()[0]["id"]
    auth_client.post(
        "/api/transactions",
        json={
            "type": "income",
            "amount": "500.00",
            "date": "2026-01-10",
            "category_id": category_id,
            "description": "",
        },
    )

    response = auth_client.get("/api/dashboard/summary", params={"month": "2026-01"})

    assert response.status_code == 200
    body = response.json()
    assert body["month"] == "2026-01"
    assert body["totals"]["income"] == "500.00"
    assert len(body["monthly_series"]) == 6
    assert body["monthly_series"][-1]["month"] == "2026-01"


def test_summary_rejects_malformed_month(auth_client: TestClient) -> None:
    response = auth_client.get("/api/dashboard/summary", params={"month": "not-a-month"})

    assert response.status_code == 400
