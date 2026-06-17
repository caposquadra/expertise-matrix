import logging

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.limiter import limiter

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

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Матрица компетенций департамента тестирования API", version="0.1.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(employees_router, prefix="/api/v1")
app.include_router(skills_router, prefix="/api/v1")
app.include_router(assessments_router, prefix="/api/v1")
app.include_router(ipr_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")
app.include_router(teams_router, prefix="/api/v1")
app.include_router(reviews_router, prefix="/api/v1")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


_openapi_schema: dict | None = None


def custom_openapi() -> dict:
    global _openapi_schema
    if _openapi_schema is not None:
        return _openapi_schema

    _openapi_schema = get_openapi(
        title="Матрица компетенций департамента тестирования API",
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
