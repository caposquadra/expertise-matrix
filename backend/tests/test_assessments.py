"""Tests for assessment CRUD: self-assessment and manager assessment."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Assessment


@pytest.fixture
def assessment_payload():
    return {"self_level": 3, "manager_level": 4, "target_level": 4}


class TestSelfAssessment:
    async def test_employee_set_self_level(self, client: AsyncClient, employee_token, employee_user, skill):
        r = await client.put(
            f"/api/v1/assessments/{skill.id}",
            json={"self_level": 3},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["self_level"] == 3
        assert data["skill_id"] == str(skill.id)

    async def test_employee_set_self_to_null(self, client: AsyncClient, employee_token, employee_user, skill):
        r = await client.put(
            f"/api/v1/assessments/{skill.id}",
            json={"self_level": None},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 200
        assert r.json()["self_level"] is None

    async def test_employee_cannot_set_manager_level(self, client: AsyncClient, employee_token, employee_user, skill):
        r = await client.put(
            f"/api/v1/assessments/{skill.id}",
            json={"manager_level": 3},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 403

    async def test_invalid_level_out_of_range(self, client: AsyncClient, employee_token, skill):
        r = await client.put(
            f"/api/v1/assessments/{skill.id}",
            json={"self_level": 5},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 422


class TestManagerAssessment:
    async def test_manager_set_manager_level(self, client: AsyncClient, manager_token, manager_user, employee_user, skill):
        r = await client.put(
            f"/api/v1/assessments/{skill.id}?employee_id={employee_user.id}",
            json={"manager_level": 3},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 200
        assert r.json()["manager_level"] == 3

    async def test_manager_missing_employee_id_for_other(self, client: AsyncClient, manager_token, skill):
        r = await client.put(
            f"/api/v1/assessments/{skill.id}",
            json={"manager_level": 3},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 200

    async def test_employee_cannot_edit_others(self, client: AsyncClient, employee_token, employee_user, manager_user, skill):
        r = await client.put(
            f"/api/v1/assessments/{skill.id}?employee_id={manager_user.id}",
            json={"self_level": 3},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 403


class TestGetAssessments:
    async def test_get_own_assessments(self, client: AsyncClient, employee_token, employee_user, skill):
        await client.put(
            f"/api/v1/assessments/{skill.id}",
            json={"self_level": 3},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        r = await client.get(
            f"/api/v1/assessments?employee_id={employee_user.id}",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 200
        assert len(r.json()) == 1

    async def test_employee_cannot_get_others(self, client: AsyncClient, employee_token, manager_user):
        r = await client.get(
            f"/api/v1/assessments?employee_id={manager_user.id}",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 403


class TestAssessmentHistory:
    async def test_get_history(self, client: AsyncClient, employee_token, employee_user, skill):
        created = await client.put(
            f"/api/v1/assessments/{skill.id}",
            json={"self_level": 2},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assessment_id = created.json()["id"]
        # Make another change
        await client.put(
            f"/api/v1/assessments/{skill.id}",
            json={"self_level": 4},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        r = await client.get(f"/api/v1/assessments/{assessment_id}/history", headers={"Authorization": f"Bearer {employee_token}"})
        assert r.status_code == 200
        assert len(r.json()) >= 1


class TestMatrix:
    async def test_manager_can_view_matrix(self, client: AsyncClient, manager_token):
        r = await client.get("/api/v1/assessments/matrix", headers={"Authorization": f"Bearer {manager_token}"})
        assert r.status_code == 200

    async def test_employee_cannot_view_matrix(self, client: AsyncClient, employee_token):
        r = await client.get("/api/v1/assessments/matrix", headers={"Authorization": f"Bearer {employee_token}"})
        assert r.status_code == 403


class TestBulkTarget:
    async def test_set_bulk_target(self, client: AsyncClient, employee_token):
        r = await client.put(
            "/api/v1/assessments/bulk-target",
            json={"target_level": 4},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 200
