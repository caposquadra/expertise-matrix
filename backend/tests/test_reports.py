"""Tests for report endpoints."""

from httpx import AsyncClient


class TestTeamSummary:
    async def test_team_summary(self, client: AsyncClient, manager_token, employee_user):
        r = await client.get("/api/v1/reports/team-summary", headers={"Authorization": f"Bearer {manager_token}"})
        assert r.status_code == 200
        data = r.json()
        assert "total_employees" in data
        assert "grade_distribution" in data
        assert data["total_employees"] >= 1

    async def test_employee_cannot_access(self, client: AsyncClient, employee_token):
        r = await client.get("/api/v1/reports/team-summary", headers={"Authorization": f"Bearer {employee_token}"})
        assert r.status_code == 403


class TestGrowthZones:
    async def test_growth_zones(self, client: AsyncClient, manager_token):
        r = await client.get("/api/v1/reports/growth-zones", headers={"Authorization": f"Bearer {manager_token}"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    async def test_growth_zones_limited(self, client: AsyncClient, manager_token):
        r = await client.get("/api/v1/reports/growth-zones?limit=3", headers={"Authorization": f"Bearer {manager_token}"})
        assert r.status_code == 200
        assert len(r.json()) <= 3


class TestSkillAverages:
    async def test_skill_averages(self, client: AsyncClient, manager_token, skill):
        r = await client.get("/api/v1/reports/skill-averages", headers={"Authorization": f"Bearer {manager_token}"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    async def test_employee_cannot_access(self, client: AsyncClient, employee_token):
        r = await client.get("/api/v1/reports/skill-averages", headers={"Authorization": f"Bearer {employee_token}"})
        assert r.status_code == 403


class TestRecentChanges:
    async def test_recent_changes(self, client: AsyncClient, manager_token):
        r = await client.get("/api/v1/reports/recent-changes", headers={"Authorization": f"Bearer {manager_token}"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)


class TestComparison:
    async def test_comparison_needs_two_ids(self, client: AsyncClient, manager_token, employee_user, manager_user):
        r = await client.get(
            f"/api/v1/reports/comparison?employee_ids={employee_user.id},{manager_user.id}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    async def test_comparison_fails_with_one_id(self, client: AsyncClient, manager_token, employee_user):
        r = await client.get(
            f"/api/v1/reports/comparison?employee_ids={employee_user.id}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 400

    async def test_employee_cannot_access(self, client: AsyncClient, employee_token, manager_user):
        r = await client.get(
            f"/api/v1/reports/comparison?employee_ids={manager_user.id}",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert r.status_code == 403


class TestReviewCyclesSummary:
    async def test_summary(self, client: AsyncClient, manager_token):
        r = await client.get("/api/v1/reports/review-cycles-summary", headers={"Authorization": f"Bearer {manager_token}"})
        assert r.status_code == 200
        data = r.json()
        assert "status_counts" in data
        assert "total_active" in data
        assert "employees_without_self_assessment" in data

    async def test_employee_cannot_access(self, client: AsyncClient, employee_token):
        r = await client.get("/api/v1/reports/review-cycles-summary", headers={"Authorization": f"Bearer {employee_token}"})
        assert r.status_code == 403


class TestWeakestSkills:
    async def test_weakest_skills(self, client: AsyncClient, manager_token):
        r = await client.get("/api/v1/reports/weakest-skills", headers={"Authorization": f"Bearer {manager_token}"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    async def test_weakest_skills_limited(self, client: AsyncClient, manager_token):
        r = await client.get("/api/v1/reports/weakest-skills?limit=3", headers={"Authorization": f"Bearer {manager_token}"})
        assert r.status_code == 200
        assert len(r.json()) <= 3

    async def test_employee_cannot_access(self, client: AsyncClient, employee_token):
        r = await client.get("/api/v1/reports/weakest-skills", headers={"Authorization": f"Bearer {employee_token}"})
        assert r.status_code == 403


class TestRecentDecisions:
    async def test_recent_decisions(self, client: AsyncClient, manager_token):
        r = await client.get("/api/v1/reports/recent-decisions", headers={"Authorization": f"Bearer {manager_token}"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    async def test_employee_cannot_access(self, client: AsyncClient, employee_token):
        r = await client.get("/api/v1/reports/recent-decisions", headers={"Authorization": f"Bearer {employee_token}"})
        assert r.status_code == 403


class TestPromotionReady:
    async def test_promotion_ready(self, client: AsyncClient, manager_token, employee_user, skill):
        r = await client.get("/api/v1/reports/promotion-ready", headers={"Authorization": f"Bearer {manager_token}"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    async def test_employee_cannot_access(self, client: AsyncClient, employee_token):
        r = await client.get("/api/v1/reports/promotion-ready", headers={"Authorization": f"Bearer {employee_token}"})
        assert r.status_code == 403


class TestAuth:
    async def test_unauthenticated(self, client: AsyncClient):
        r = await client.get("/api/v1/reports/team-summary")
        assert r.status_code == 401
