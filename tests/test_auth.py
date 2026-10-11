"""Integration tests untuk alur autentikasi JWT."""
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.core.security import decode_token
from app.main import app
from app.models import Base
from app.models.user import User
from app.core.rate_limit import reset_rate_limit_state_for_tests


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    # Database SQLite in-memory terisolasi untuk setiap pengujian.
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=test_engine, class_=Session, autoflush=False, autocommit=False, expire_on_commit=False
    )
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.state.testing_session_local = TestingSessionLocal
    reset_rate_limit_state_for_tests()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def _signup(client: TestClient, email: str = "guru@example.com") -> dict:
    response = client.post(
        "/api/auth/signup",
        json={"email": email, "password": "Password-Aman-123"},
    )
    assert response.status_code == 201, response.text
    # Hanya fixture test yang memprovisikan role staf aktif. Signup publik tidak boleh.
    with app.state.testing_session_local() as db:
        user = db.scalar(select(User).where(User.email == email))
        assert user is not None
        user.role = "guru_bk"
        user.is_active = True
        db.commit()
    return response.json()


def _login(client: TestClient, email: str = "guru@example.com") -> dict:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Password-Aman-123"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_signup_stores_hash_and_never_returns_password_hash(client: TestClient) -> None:
    data = _signup(client)
    assert "password" not in data
    assert "password_hash" not in data
    assert data["email"] == "guru@example.com"


def test_login_and_protected_me(client: TestClient) -> None:
    _signup(client)
    tokens = _login(client)
    access_claims = decode_token(tokens["access_token"])
    refresh_claims = decode_token(tokens["refresh_token"])
    assert access_claims["token_type"] == "access"
    assert refresh_claims["token_type"] == "refresh"
    assert "password_hash" not in access_claims
    assert "secret_key" not in access_claims

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "guru@example.com"
    assert "password_hash" not in response.json()


def test_refresh_rotates_token_and_rejects_reuse(client: TestClient) -> None:
    _signup(client)
    tokens = _login(client)
    refreshed = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200, refreshed.text
    new_tokens = refreshed.json()
    assert new_tokens["refresh_token"] != tokens["refresh_token"]

    reuse = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert reuse.status_code == 401

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
    )
    assert response.status_code == 200


def test_bad_login_is_401_and_bad_access_token_is_401(client: TestClient) -> None:
    _signup(client)
    response = client.post(
        "/api/auth/login",
        json={"email": "guru@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401

    response = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.value"})
    assert response.status_code == 401


def test_oauth2_form_login_supported(client: TestClient) -> None:
    _signup(client)
    response = client.post(
        "/api/auth/login",
        data={"username": "guru@example.com", "password": "Password-Aman-123", "grant_type": "password"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["access_token"]


def test_inactive_user_gets_403_for_me_and_refresh(client: TestClient) -> None:
    _signup(client)
    tokens = _login(client)
    with app.state.testing_session_local() as db:
        user = db.scalar(select(User).where(User.email == "guru@example.com"))
        assert user is not None
        user.is_active = False
        db.commit()

    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me_response.status_code == 403

    refresh_response = client.post(
        "/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh_response.status_code == 403


def test_signup_rejects_client_supplied_role(client: TestClient) -> None:
    response = client.post(
        "/api/auth/signup",
        json={"email": "attacker@example.com", "password": "Password-Aman-123", "role": "guru_bk"},
    )
    assert response.status_code == 422


def test_public_signup_creates_pending_inactive_account(client: TestClient) -> None:
    response = client.post(
        "/api/auth/signup",
        json={"email": "pending@example.com", "password": "Password-Aman-123"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["role"] == "pending"
    assert body["is_active"] is False
    login = client.post(
        "/api/auth/login",
        json={"email": "pending@example.com", "password": "Password-Aman-123"},
    )
    assert login.status_code == 403
