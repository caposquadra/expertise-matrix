"""Tests for IPR plans and goals CRUD."""

from httpx import AsyncClient


async def create_plan(client, token, employee_user):
    r = await client.post(
        "/api/v1/ipr-plans",
        json={
            "employee_id": str(employee_user.id),
            "title": "Q1 Plan",
            "description": "Growth",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    return r.json()


class TestIprPlans:
    async def test_manager_create_plan(
        self, client: AsyncClient, manager_token, employee_user
    ):
        plan = await create_plan(client, manager_token, employee_user)
        assert plan["title"] == "Q1 Plan"
        assert plan["employee_id"] == str(employee_user.id)

    async def test_employee_cannot_create_plan(
        self, client: AsyncClient, employee_token, employee_user
    ):
        r = await client.post(
            "/api/v1/ipr-plans",
            json={"employee_id": str(employee_user.id), "title": "My Plan"},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 403

    async def test_get_own_plans(
        self, client: AsyncClient, manager_token, employee_token, employee_user
    ):
        await create_plan(client, manager_token, employee_user)
        r = await client.get(
            f"/api/v1/ipr-plans?employee_id={employee_user.id}",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 200
        assert len(r.json()) == 1

    async def test_manager_can_list_all(
        self, client: AsyncClient, manager_token, employee_user
    ):
        await create_plan(client, manager_token, employee_user)
        r = await client.get(
            "/api/v1/ipr-plans", headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert r.status_code == 200
        assert len(r.json()) >= 1

    async def test_update_plan(self, client: AsyncClient, manager_token, employee_user):
        plan = await create_plan(client, manager_token, employee_user)
        r = await client.patch(
            f"/api/v1/ipr-plans/{plan['id']}",
            json={"title": "Updated Plan"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Updated Plan"

    async def test_employee_cannot_update_plan(
        self, client: AsyncClient, manager_token, employee_token, employee_user
    ):
        plan = await create_plan(client, manager_token, employee_user)
        r = await client.patch(
            f"/api/v1/ipr-plans/{plan['id']}",
            json={"title": "Hacked"},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 403

    async def test_get_nonexistent_plan(self, client: AsyncClient, manager_token):
        r = await client.get(
            "/api/v1/ipr-plans/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 404


class TestIprGoals:
    async def test_add_goal(
        self, client: AsyncClient, manager_token, employee_user, skill
    ):
        plan = await create_plan(client, manager_token, employee_user)
        r = await client.post(
            f"/api/v1/ipr-plans/{plan['id']}/goals",
            json={
                "skill_id": str(skill.id),
                "current_level": 2,
                "target_level": 4,
                "notes": "Practice daily",
            },
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 201
        assert r.json()["skill_id"] == str(skill.id)

    async def test_employee_cannot_add_goal(
        self, client: AsyncClient, manager_token, employee_token, employee_user, skill
    ):
        plan = await create_plan(client, manager_token, employee_user)
        r = await client.post(
            f"/api/v1/ipr-plans/{plan['id']}/goals",
            json={"skill_id": str(skill.id), "current_level": 2, "target_level": 4},
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 403

    async def test_get_plan_with_goals(
        self, client: AsyncClient, manager_token, employee_user, skill
    ):
        plan = await create_plan(client, manager_token, employee_user)
        await client.post(
            f"/api/v1/ipr-plans/{plan['id']}/goals",
            json={"skill_id": str(skill.id), "current_level": 2, "target_level": 4},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        r = await client.get(
            f"/api/v1/ipr-plans/{plan['id']}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 200
        assert len(r.json()["goals"]) == 1

    async def test_update_goal_status(
        self, client: AsyncClient, manager_token, employee_user, skill
    ):
        plan = await create_plan(client, manager_token, employee_user)
        goal = await client.post(
            f"/api/v1/ipr-plans/{plan['id']}/goals",
            json={"skill_id": str(skill.id), "current_level": 2, "target_level": 4},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        goal_id = goal.json()["id"]
        r = await client.patch(
            f"/api/v1/ipr-plans/goals/{goal_id}",
            json={"status": "achieved"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "achieved"

    async def test_update_goal_nonexistent(self, client: AsyncClient, manager_token):
        r = await client.patch(
            "/api/v1/ipr-plans/goals/00000000-0000-0000-0000-000000000000",
            json={"status": "achieved"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 404
