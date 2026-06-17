"""Tests for authentication: login, register, refresh, role checks."""

from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from jose import jwt

from app.core.config import settings


class TestLogin:
    async def test_login_success(self, client: AsyncClient, admin_user):
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@test.com", "password": "admin123"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["user"]["email"] == "admin@test.com"

    async def test_login_invalid_password(self, client: AsyncClient, admin_user):
        r = await client.post(
            "/api/v1/auth/login", json={"email": "admin@test.com", "password": "wrong"}
        )
        assert r.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        r = await client.post(
            "/api/v1/auth/login", json={"email": "nobody@test.com", "password": "x"}
        )
        assert r.status_code == 401


class TestRefresh:
    async def test_refresh_success(self, client: AsyncClient, admin_user):
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@test.com", "password": "admin123"},
        )
        refresh_token = r.cookies.get("refresh_token")
        assert refresh_token is not None, "refresh_token cookie missing"
        r2 = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert r2.status_code == 200
        assert "access_token" in r2.json()

    async def test_refresh_invalid_token(self, client: AsyncClient):
        r = await client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid"})
        assert r.status_code == 401


class TestRegister:
    async def test_register_by_admin(self, client: AsyncClient, admin_token):
        r = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@test.com",
                "password": "new123",
                "full_name": "New User",
                "role": "employee",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 201
        assert r.json()["email"] == "new@test.com"

    async def test_register_by_employee_forbidden(
        self, client: AsyncClient, employee_token
    ):
        r = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "new2@test.com",
                "password": "new123",
                "full_name": "New User",
                "role": "employee",
            },
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 403

    async def test_register_duplicate_email(
        self, client: AsyncClient, admin_token, admin_user
    ):
        r = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "admin@test.com",
                "password": "x",
                "full_name": "x",
                "role": "employee",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 409


class TestMe:
    async def test_get_me(self, client: AsyncClient, employee_token):
        r = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {employee_token}"}
        )
        assert r.status_code == 200
        assert r.json()["email"] == "employee@test.com"

    async def test_get_me_unauthorized(self, client: AsyncClient):
        r = await client.get("/api/v1/auth/me")
        assert r.status_code == 401

    async def test_get_me_invalid_token(self, client: AsyncClient):
        r = await client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid"}
        )
        assert r.status_code == 401

    async def test_get_me_expired_token(self, client: AsyncClient, admin_user):
        token = jwt.encode(
            {
                "sub": str(admin_user.id),
                "exp": datetime.now(timezone.utc) - timedelta(hours=1),
                "type": "access",
            },
            settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )
        r = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert r.status_code == 401
