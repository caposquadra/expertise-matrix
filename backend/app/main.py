from fastapi import Depends, FastAPI
from fastapi.openapi.utils import get_openapi
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from app.api.v1 import (
    assessments_router,
    auth_router,
    employees_router,
    export_router,
    ipr_router,
    reports_router,
    reviews_router,
    skills_router,
    teams_router,
)

app = FastAPI(title="Expertise Matrix API", version="0.1.0")

app.include_router(auth_router, prefix="/api/v1")
app.include_router(employees_router, prefix="/api/v1")
app.include_router(skills_router, prefix="/api/v1")
app.include_router(assessments_router, prefix="/api/v1")
app.include_router(ipr_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")
app.include_router(teams_router, prefix="/api/v1")
app.include_router(reviews_router, prefix="/api/v1")


_openapi_schema: dict | None = None


def custom_openapi() -> dict:
    global _openapi_schema
    if _openapi_schema is not None:
        return _openapi_schema

    _openapi_schema = get_openapi(
        title="Expertise Matrix API",
        version="0.1.0",
        routes=app.routes,
    )

    for path, methods in _openapi_schema.get("paths", {}).items():
        for method in methods.values():
            if not isinstance(method, dict) or "responses" not in method:
                continue
            responses = method["responses"]
            if path == "/api/v1/auth/login":
                if "401" not in responses:
                    responses["401"] = {
                        "description": "Unauthorized: invalid email or password"
                    }
            elif path != "/health":
                if "401" not in responses:
                    responses["401"] = {
                        "description": "Unauthorized: missing or invalid token"
                    }
                if "403" not in responses:
                    responses["403"] = {
                        "description": "Forbidden: insufficient permissions"
                    }

    return _openapi_schema


app.openapi = custom_openapi  # type: ignore[method-assign]


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "connected", "service": "expertise-matrix-backend"}
