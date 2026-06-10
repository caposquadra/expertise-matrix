"""Tests for employee CRUD and role-based access."""

from httpx import AsyncClient


class TestListEmployees:
    async def test_admin_can_list_all(
        self, client: AsyncClient, admin_token, employee_user, manager_user
    ):
        r = await client.get(
            "/api/v1/employees", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert r.status_code == 200
        ids = [e["id"] for e in r.json()]
        assert str(employee_user.id) in ids
        assert str(manager_user.id) in ids

    async def test_employee_can_only_list_self(
        self, client: AsyncClient, employee_token, employee_user, manager_user
    ):
        r = await client.get(
            "/api/v1/employees", headers={"Authorization": f"Bearer {employee_token}"}
        )
        assert r.status_code == 200
        assert len(r.json()) == 1


class TestGetEmployee:
    async def test_admin_get_any(self, client: AsyncClient, admin_token, employee_user):
        r = await client.get(
            f"/api/v1/employees/{employee_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        assert r.json()["email"] == employee_user.email

    async def test_employee_get_self(
        self, client: AsyncClient, employee_token, employee_user
    ):
        r = await client.get(
            f"/api/v1/employees/{employee_user.id}",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 200

    async def test_employee_get_other_forbidden(
        self, client: AsyncClient, employee_token, manager_user
    ):
        r = await client.get(
            f"/api/v1/employees/{manager_user.id}",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 403

    async def test_get_nonexistent(self, client: AsyncClient, admin_token):
        r = await client.get(
            "/api/v1/employees/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 404


class TestCreateEmployee:
    async def test_admin_can_create(self, client: AsyncClient, admin_token):
        r = await client.post(
            "/api/v1/employees",
            json={
                "email": "new@test.com",
                "password": "new123",
                "full_name": "New Employee",
                "role": "employee",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 201
        assert r.json()["email"] == "new@test.com"

    async def test_employee_cannot_create(self, client: AsyncClient, employee_token):
        r = await client.post(
            "/api/v1/employees",
            json={
                "email": "hacker@test.com",
                "password": "x",
                "full_name": "Hacker",
                "role": "employee",
            },
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 403

    async def test_create_duplicate_email(
        self, client: AsyncClient, admin_token, employee_user
    ):
        r = await client.post(
            "/api/v1/employees",
            json={
                "email": employee_user.email,
                "password": "x",
                "full_name": "Duplicate",
                "role": "employee",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 409


class TestUpdateEmployee:
    async def test_admin_update(self, client: AsyncClient, admin_token, employee_user):
        r = await client.patch(
            f"/api/v1/employees/{employee_user.id}",
            json={"full_name": "Updated Name"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        assert r.json()["full_name"] == "Updated Name"

    async def test_employee_cannot_update_self(
        self, client: AsyncClient, employee_token, employee_user
    ):
        r = await client.patch(
            f"/api/v1/employees/{employee_user.id}",
            json={"full_name": "Hacked"},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 403

    async def test_update_nonexistent(self, client: AsyncClient, admin_token):
        r = await client.patch(
            "/api/v1/employees/00000000-0000-0000-0000-000000000000",
            json={"full_name": "Ghost"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 404


class TestScore:
    async def test_get_score(
        self, client: AsyncClient, employee_token, employee_user, skill
    ):
        r = await client.get(
            f"/api/v1/employees/{employee_user.id}/score",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "current_score" in data
        assert "target_score" in data
        assert "total_weight" in data
        assert "assessed_weight" in data

    async def test_employee_cannot_get_others_score(
        self, client: AsyncClient, employee_token, manager_user
    ):
        r = await client.get(
            f"/api/v1/employees/{manager_user.id}/score",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 403

    async def test_score_nonexistent_employee(self, client: AsyncClient, admin_token):
        r = await client.get(
            "/api/v1/employees/00000000-0000-0000-0000-000000000000/score",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 404
