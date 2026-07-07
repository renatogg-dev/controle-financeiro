"""API tests for goal set/read and history."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_set_and_get_goal(auth_client: TestClient) -> None:
    response = auth_client.put("/api/goals/2026-01", json={"target_amount": "500.00"})

    assert response.status_code == 200
    body = response.json()
    assert body["month"] == "2026-01"
    assert body["target"] == "500.00"


def test_get_goal_without_setting_returns_zero_target(auth_client: TestClient) -> None:
    response = auth_client.get("/api/goals/2026-02")

    assert response.status_code == 200
    assert response.json()["target"] == "0"


def test_history_returns_requested_number_of_months(auth_client: TestClient) -> None:
    auth_client.put("/api/goals/2026-03", json={"target_amount": "100.00"})

    response = auth_client.get("/api/goals/history", params={"end_month": "2026-03", "months": 3})

    assert response.status_code == 200
    body = response.json()
    assert [item["month"] for item in body] == ["2026-01", "2026-02", "2026-03"]
    assert body[-1]["target"] == "100.00"


def test_goals_are_isolated_per_user(client: TestClient) -> None:
    client.post(
        "/api/auth/register", json={"email": "goalowner@example.com", "password": "password123"}
    )
    client.put("/api/goals/2026-01", json={"target_amount": "999.00"})
    client.post("/api/auth/logout")

    client.post(
        "/api/auth/register", json={"email": "otherviewer@example.com", "password": "password123"}
    )
    response = client.get("/api/goals/2026-01")

    assert response.json()["target"] == "0"
