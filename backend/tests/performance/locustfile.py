"""Locust load tests for reports and matrix endpoints."""

from locust import HttpUser, between, task


class ManagerUser(HttpUser):
    wait_time = between(1, 3)
    token: str | None = None

    def on_start(self):
        r = self.client.post("/api/v1/auth/login", json={
            "email": "manager@example.com",
            "password": "manager123",
        })
        self.token = r.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def team_summary(self):
        self.client.get("/api/v1/reports/team-summary", headers=self.headers)

    @task(2)
    def growth_zones(self):
        self.client.get("/api/v1/reports/growth-zones?limit=10", headers=self.headers)

    @task(2)
    def skill_averages(self):
        self.client.get("/api/v1/reports/skill-averages", headers=self.headers)

    @task(2)
    def review_cycles_summary(self):
        self.client.get("/api/v1/reports/review-cycles-summary", headers=self.headers)

    @task(1)
    def weakest_skills(self):
        self.client.get("/api/v1/reports/weakest-skills?limit=5", headers=self.headers)

    @task(1)
    def matrix(self):
        self.client.get("/api/v1/assessments/matrix", headers=self.headers)

    @task(2)
    def recent_changes(self):
        self.client.get("/api/v1/reports/recent-changes?limit=8", headers=self.headers)

    @task(1)
    def promotion_ready(self):
        self.client.get("/api/v1/reports/promotion-ready", headers=self.headers)

    @task(1)
    def recent_decisions(self):
        self.client.get("/api/v1/reports/recent-decisions?limit=5", headers=self.headers)
