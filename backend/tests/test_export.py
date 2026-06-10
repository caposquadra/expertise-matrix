"""Tests for CSV and Excel export."""

from httpx import AsyncClient


class TestExportCsv:
    async def test_csv_export(self, client: AsyncClient, manager_token):
        r = await client.get("/api/v1/export/csv", headers={"Authorization": f"Bearer {manager_token}"})
        assert r.status_code == 200
        assert r.headers["content-type"] == "text/csv; charset=utf-8"

    async def test_csv_export_unauthorized(self, client: AsyncClient):
        r = await client.get("/api/v1/export/csv")
        assert r.status_code == 401

    async def test_csv_employee_forbidden(self, client: AsyncClient, employee_token):
        r = await client.get("/api/v1/export/csv", headers={"Authorization": f"Bearer {employee_token}"})
        assert r.status_code == 403


class TestExportExcel:
    async def test_excel_export(self, client: AsyncClient, manager_token):
        r = await client.get("/api/v1/export/excel", headers={"Authorization": f"Bearer {manager_token}"})
        assert r.status_code == 200
        assert "spreadsheet" in r.headers["content-type"]

    async def test_excel_export_unauthorized(self, client: AsyncClient):
        r = await client.get("/api/v1/export/excel")
        assert r.status_code == 401

    async def test_excel_employee_forbidden(self, client: AsyncClient, employee_token):
        r = await client.get("/api/v1/export/excel", headers={"Authorization": f"Bearer {employee_token}"})
        assert r.status_code == 403
