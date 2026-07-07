"""API tests for the transactions JSON endpoints, including cross-user isolation."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _first_category_id(client: TestClient) -> int:
    return client.get("/api/categories").json()[0]["id"]


def test_create_and_list_transaction(auth_client: TestClient) -> None:
    category_id = _first_category_id(auth_client)

    create_response = auth_client.post(
        "/api/transactions",
        json={
            "type": "expense",
            "amount": "42.50",
            "date": "2026-01-10",
            "category_id": category_id,
            "description": "Mercado",
        },
    )
    assert create_response.status_code == 201

    list_response = auth_client.get("/api/transactions", params={"month": "2026-01"})
    body = list_response.json()
    assert body["total"] == 1
    assert body["items"][0]["description"] == "Mercado"


def test_create_transaction_rejects_negative_amount(auth_client: TestClient) -> None:
    category_id = _first_category_id(auth_client)

    response = auth_client.post(
        "/api/transactions",
        json={
            "type": "expense",
            "amount": "-5.00",
            "date": "2026-01-10",
            "category_id": category_id,
            "description": "Invalid",
        },
    )

    assert response.status_code == 422


def test_update_and_delete_transaction(auth_client: TestClient) -> None:
    category_id = _first_category_id(auth_client)
    created = auth_client.post(
        "/api/transactions",
        json={
            "type": "income",
            "amount": "100.00",
            "date": "2026-01-10",
            "category_id": category_id,
            "description": "Salário",
        },
    ).json()

    update_response = auth_client.put(
        f"/api/transactions/{created['id']}",
        json={
            "type": "income",
            "amount": "150.00",
            "date": "2026-01-10",
            "category_id": category_id,
            "description": "Salário revisado",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["amount"] == "150.00"

    delete_response = auth_client.delete(f"/api/transactions/{created['id']}")
    assert delete_response.status_code == 204

    get_response = auth_client.get(f"/api/transactions/{created['id']}")
    assert get_response.status_code == 404


def test_user_cannot_access_another_users_transaction(client: TestClient) -> None:
    client.post("/api/auth/register", json={"email": "alice@example.com", "password": "password123"})
    category_id = _first_category_id(client)
    transaction = client.post(
        "/api/transactions",
        json={
            "type": "expense",
            "amount": "10.00",
            "date": "2026-01-10",
            "category_id": category_id,
            "description": "Alice's",
        },
    ).json()
    client.post("/api/auth/logout")

    client.post("/api/auth/register", json={"email": "bob@example.com", "password": "password123"})

    get_response = client.get(f"/api/transactions/{transaction['id']}")
    assert get_response.status_code == 404

    delete_response = client.delete(f"/api/transactions/{transaction['id']}")
    assert delete_response.status_code == 404

    list_response = client.get("/api/transactions")
    assert list_response.json()["total"] == 0


def test_pagination_metadata(auth_client: TestClient) -> None:
    category_id = _first_category_id(auth_client)
    for day in range(1, 4):
        auth_client.post(
            "/api/transactions",
            json={
                "type": "expense",
                "amount": "1.00",
                "date": f"2026-01-0{day}",
                "category_id": category_id,
                "description": f"tx-{day}",
            },
        )

    response = auth_client.get("/api/transactions", params={"page": 1, "page_size": 2})
    body = response.json()

    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["page"] == 1
    assert body["page_size"] == 2


def test_csv_export_contains_header_and_rows(auth_client: TestClient) -> None:
    category_id = _first_category_id(auth_client)
    auth_client.post(
        "/api/transactions",
        json={
            "type": "expense",
            "amount": "12.34",
            "date": "2026-01-05",
            "category_id": category_id,
            "description": "Café",
        },
    )

    response = auth_client.get("/api/transactions/export.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "date,type,category,amount,description" in response.text
    assert "Café" in response.text
