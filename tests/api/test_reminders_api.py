"""API tests for reminder CRUD and mark-paid."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_reminder(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/api/reminders",
        json={"name": "Internet", "amount": "99.90", "due_date": "2026-08-01", "notes": "Boleto"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Internet"
    assert body["is_paid"] is False


def test_create_reminder_without_amount(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/api/reminders", json={"name": "Academia", "due_date": "2026-08-01"}
    )

    assert response.status_code == 201
    assert response.json()["amount"] is None


def test_mark_paid_and_reopen(auth_client: TestClient) -> None:
    created = auth_client.post(
        "/api/reminders", json={"name": "Água", "due_date": "2026-08-01"}
    ).json()

    paid_response = auth_client.patch(
        f"/api/reminders/{created['id']}/paid", params={"is_paid": True}
    )
    assert paid_response.status_code == 200
    assert paid_response.json()["is_paid"] is True
    assert paid_response.json()["status"] == "paid"

    reopened_response = auth_client.patch(
        f"/api/reminders/{created['id']}/paid", params={"is_paid": False}
    )
    assert reopened_response.json()["is_paid"] is False


def test_delete_reminder(auth_client: TestClient) -> None:
    created = auth_client.post(
        "/api/reminders", json={"name": "Gás", "due_date": "2026-08-01"}
    ).json()

    delete_response = auth_client.delete(f"/api/reminders/{created['id']}")
    assert delete_response.status_code == 204

    list_response = auth_client.get("/api/reminders")
    assert list_response.json() == []


def test_user_cannot_modify_another_users_reminder(client: TestClient) -> None:
    client.post(
        "/api/auth/register", json={"email": "alice2@example.com", "password": "password123"}
    )
    reminder = client.post(
        "/api/reminders", json={"name": "Alice's bill", "due_date": "2026-08-01"}
    ).json()
    client.post("/api/auth/logout")

    client.post("/api/auth/register", json={"email": "bob2@example.com", "password": "password123"})

    delete_response = client.delete(f"/api/reminders/{reminder['id']}")
    assert delete_response.status_code == 404

    paid_response = client.patch(f"/api/reminders/{reminder['id']}/paid", params={"is_paid": True})
    assert paid_response.status_code == 404
