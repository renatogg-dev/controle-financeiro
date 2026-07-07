"""Tests for the HTMX web routes: auth gating, CSRF enforcement, fragments."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _category_id(client: TestClient) -> int:
    return client.get("/api/categories").json()[0]["id"]


def test_unauthenticated_transactions_page_redirects_to_login(client: TestClient) -> None:
    response = client.get("/app/transactions", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_unauthenticated_htmx_request_gets_hx_redirect(client: TestClient) -> None:
    response = client.get(
        "/app/transactions", headers={"HX-Request": "true"}, follow_redirects=False
    )

    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == "/login"


def test_create_transaction_without_csrf_header_is_rejected(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/app/transactions",
        data={
            "type": "expense",
            "amount": "10.00",
            "date": "2026-01-05",
            "category_id": _category_id(auth_client),
            "description": "sem csrf",
        },
    )

    assert response.status_code == 403


def test_create_transaction_with_csrf_header_succeeds_and_fires_toast(
    auth_client: TestClient,
) -> None:
    page = auth_client.get("/app/transactions")
    csrf_token = page.text.split('name="csrf-token" content="')[1].split('"')[0]

    response = auth_client.post(
        "/app/transactions",
        headers={"X-CSRF-Token": csrf_token, "HX-Request": "true"},
        data={
            "type": "expense",
            "amount": "10.00",
            "date": "2026-01-05",
            "category_id": _category_id(auth_client),
            "description": "com csrf",
        },
    )

    assert response.status_code == 200
    assert "show-toast" in response.headers["HX-Trigger"]
    assert "com csrf" in response.text


def test_list_fragment_is_a_partial_not_a_full_page(auth_client: TestClient) -> None:
    response = auth_client.get("/app/transactions/list")

    assert response.status_code == 200
    assert "<html" not in response.text
    assert 'id="transaction-list-container"' in response.text


def test_goals_and_reminders_pages_require_login(client: TestClient) -> None:
    for path in ["/app/goals", "/app/reminders"]:
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/login"


def _csrf_token(client: TestClient, page_path: str) -> str:
    page = client.get(page_path)
    return page.text.split('name="csrf-token" content="')[1].split('"')[0]


def test_login_form_success_sets_cookie_and_redirects(client: TestClient) -> None:
    client.post(
        "/api/auth/register", json={"email": "formlogin@example.com", "password": "password123"}
    )
    client.post("/api/auth/logout")

    response = client.post(
        "/login",
        data={"email": "formlogin@example.com", "password": "password123"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/app"
    assert "session" in response.cookies


def test_login_form_wrong_password_rerenders_with_error(client: TestClient) -> None:
    client.post(
        "/api/auth/register", json={"email": "formlogin2@example.com", "password": "password123"}
    )
    client.post("/api/auth/logout")

    response = client.post("/login", data={"email": "formlogin2@example.com", "password": "wrong"})

    assert response.status_code == 401
    assert "incorretos" in response.text


def test_register_form_short_password_rerenders_with_error(client: TestClient) -> None:
    response = client.post(
        "/register", data={"email": "shortpass@example.com", "password": "short"}
    )

    assert response.status_code == 422
    assert "8 caracteres" in response.text


def test_register_form_duplicate_email_rerenders_with_error(client: TestClient) -> None:
    client.post(
        "/api/auth/register", json={"email": "dupform@example.com", "password": "password123"}
    )

    response = client.post(
        "/register", data={"email": "dupform@example.com", "password": "password123"}
    )

    assert response.status_code == 409
    assert "já está cadastrado" in response.text


def test_goals_content_fragment_and_set_goal(auth_client: TestClient) -> None:
    csrf_token = _csrf_token(auth_client, "/app/goals")

    set_response = auth_client.put(
        "/app/goals/2026-03",
        headers={"X-CSRF-Token": csrf_token},
        data={"target_amount": "250.00"},
    )
    assert set_response.status_code == 200
    assert "show-toast" in set_response.headers["HX-Trigger"]

    fragment_response = auth_client.get("/app/goals/content", params={"month": "2026-03"})
    assert "<html" not in fragment_response.text
    assert "250" in fragment_response.text


def test_reminders_web_create_and_delete(auth_client: TestClient) -> None:
    csrf_token = _csrf_token(auth_client, "/app/reminders")

    create_response = auth_client.post(
        "/app/reminders",
        headers={"X-CSRF-Token": csrf_token},
        data={"name": "Internet", "due_date": "2026-08-01"},
    )
    assert create_response.status_code == 200
    assert "Internet" in create_response.text

    reminder_id = auth_client.get("/api/reminders").json()[0]["id"]
    delete_response = auth_client.delete(
        f"/app/reminders/{reminder_id}", headers={"X-CSRF-Token": csrf_token}
    )
    assert delete_response.status_code == 200
    assert "Nenhum lembrete" in delete_response.text


def test_transactions_edit_form_and_update(auth_client: TestClient) -> None:
    category_id = _category_id(auth_client)
    csrf_token = _csrf_token(auth_client, "/app/transactions")

    auth_client.post(
        "/app/transactions",
        headers={"X-CSRF-Token": csrf_token},
        data={
            "type": "expense",
            "amount": "20.00",
            "date": "2026-01-05",
            "category_id": category_id,
            "description": "original",
        },
    )
    transaction_id = auth_client.get("/api/transactions").json()["items"][0]["id"]

    edit_response = auth_client.get(f"/app/transactions/{transaction_id}/edit")
    assert "original" in edit_response.text

    update_response = auth_client.put(
        f"/app/transactions/{transaction_id}",
        headers={"X-CSRF-Token": csrf_token},
        data={
            "type": "expense",
            "amount": "30.00",
            "date": "2026-01-05",
            "category_id": category_id,
            "description": "atualizado",
        },
    )
    assert update_response.status_code == 200
    assert "atualizado" in update_response.text
