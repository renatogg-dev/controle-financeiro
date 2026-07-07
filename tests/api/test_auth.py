"""API tests for registration, login, logout, and login-gated routes."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_register_creates_user_and_session_cookie(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register", json={"email": "new@example.com", "password": "password123"}
    )

    assert response.status_code == 201
    assert response.json()["email"] == "new@example.com"
    assert "session" in response.cookies


def test_register_duplicate_email_returns_409(client: TestClient) -> None:
    payload = {"email": "dup@example.com", "password": "password123"}
    client.post("/api/auth/register", json=payload)

    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 409


def test_login_wrong_password_returns_401(client: TestClient) -> None:
    client.post("/api/auth/register", json={"email": "a@example.com", "password": "password123"})

    response = client.post(
        "/api/auth/login", json={"email": "a@example.com", "password": "wrong-password"}
    )

    assert response.status_code == 401


def test_login_unknown_email_returns_401(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login", json={"email": "ghost@example.com", "password": "password123"}
    )

    assert response.status_code == 401


def test_me_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_me_returns_current_user_when_authenticated(auth_client: TestClient) -> None:
    response = auth_client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


def test_logout_clears_session(auth_client: TestClient) -> None:
    logout_response = auth_client.post("/api/auth/logout")
    assert logout_response.status_code == 204

    me_response = auth_client.get("/api/auth/me")
    assert me_response.status_code == 401


def test_dashboard_redirects_when_not_authenticated(client: TestClient) -> None:
    response = client.get("/app", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_dashboard_accessible_when_authenticated(auth_client: TestClient) -> None:
    response = auth_client.get("/app", follow_redirects=False)

    assert response.status_code == 200


def test_dashboard_htmx_redirect_uses_hx_redirect_header(client: TestClient) -> None:
    response = client.get("/app", headers={"HX-Request": "true"}, follow_redirects=False)

    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == "/login"
