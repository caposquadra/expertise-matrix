"""Tests for skill CRUD — admin-only creation/deletion, everyone can list."""

from httpx import AsyncClient


class TestListSkills:
    async def test_anyone_can_list(self, client: AsyncClient, employee_token, skill):
        r = await client.get("/api/v1/skills", headers={"Authorization": f"Bearer {employee_token}"})
        assert r.status_code == 200
        names = [s["name"] for s in r.json()]
        assert skill.name in names


class TestCreateSkill:
    async def test_admin_can_create(self, client: AsyncClient, admin_token):
        r = await client.post(
            "/api/v1/skills",
            json={"name": "Kubernetes", "category": "ОС", "sort_order": 5},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 201
        assert r.json()["name"] == "Kubernetes"

    async def test_employee_cannot_create(self, client: AsyncClient, employee_token):
        r = await client.post(
            "/api/v1/skills",
            json={"name": "New Skill", "category": "X", "sort_order": 1},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 403


class TestUpdateSkill:
    async def test_admin_can_update(self, client: AsyncClient, admin_token, skill):
        r = await client.patch(
            f"/api/v1/skills/{skill.id}",
            json={"name": "Linux Advanced"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        assert r.json()["name"] == "Linux Advanced"

    async def test_manager_cannot_update(self, client: AsyncClient, manager_token, skill):
        r = await client.patch(
            f"/api/v1/skills/{skill.id}",
            json={"name": "Hacked"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 403


class TestDeleteSkill:
    async def test_admin_can_deactivate(self, client: AsyncClient, admin_token, skill):
        r = await client.delete(f"/api/v1/skills/{skill.id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 204

    async def test_employee_cannot_delete(self, client: AsyncClient, employee_token, skill):
        r = await client.delete(f"/api/v1/skills/{skill.id}", headers={"Authorization": f"Bearer {employee_token}"})
        assert r.status_code == 403
