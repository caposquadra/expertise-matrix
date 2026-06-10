from app.api.v1.assessments import router as assessments_router
from app.api.v1.auth import router as auth_router
from app.api.v1.employees import router as employees_router
from app.api.v1.export import router as export_router
from app.api.v1.ipr import router as ipr_router
from app.api.v1.reports import router as reports_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.skills import router as skills_router
from app.api.v1.teams import router as teams_router

__all__ = [
    "assessments_router",
    "auth_router",
    "employees_router",
    "export_router",
    "ipr_router",
    "reports_router",
    "reviews_router",
    "skills_router",
    "teams_router",
]
