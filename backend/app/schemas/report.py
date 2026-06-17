import uuid
from datetime import datetime

from pydantic import BaseModel


class GradeDistributionItem(BaseModel):
    grade: str
    count: int


class SkillCoverageItem(BaseModel):
    skill_name: str
    category: str
    employees_with_assessment: int
    total_employees: int
    coverage_percent: float


class TeamSummaryOut(BaseModel):
    total_employees: int
    grade_distribution: list[GradeDistributionItem]
    avg_self_level: float | None = None
    avg_manager_level: float | None = None
    skill_coverage: list[SkillCoverageItem]


class GrowthZoneOut(BaseModel):
    skill_name: str
    category: str
    avg_self_level: float
    avg_manager_level: float
    avg_gap: float


class ComparisonCell(BaseModel):
    employee_name: str
    employee_id: str
    self_level: int | None = None
    manager_level: int | None = None


class ComparisonRow(BaseModel):
    skill_name: str
    category: str
    cells: list[ComparisonCell]


class SkillAverageItem(BaseModel):
    category: str
    avg_self_level: float
    avg_manager_level: float


class RecentChangeItem(BaseModel):
    id: uuid.UUID
    field_name: str
    old_value: int | None = None
    new_value: int | None = None
    employee_name: str | None = None
    skill_name: str | None = None
    changed_at: datetime


class StatusCountItem(BaseModel):
    status: str
    count: int


class EmployeeCycleInfo(BaseModel):
    employee_name: str
    employee_id: str
    grade: str | None = None
    profile_grade: int | None = None
    cycle_id: str | None = None
    status: str | None = None
    days_in_status: int = 0


class ReviewCyclesSummaryOut(BaseModel):
    status_counts: list[StatusCountItem]
    total_active: int
    employees_without_self_assessment: list[EmployeeCycleInfo]
    status_employees: dict[str, list[EmployeeCycleInfo]] = {}


class WeakestSkillOut(BaseModel):
    skill_name: str
    category: str
    avg_manager_level: float
    assessment_count: int


class RecentDecisionOut(BaseModel):
    employee_name: str
    employee_id: str
    decision: str
    current_grade: str | None = None
    target_grade: str | None = None
    completed_at: datetime


class PromotionReadyOut(BaseModel):
    employee_name: str
    employee_id: str
    current_grade: str | None = None
    target_grade: str | None = None
    total_score: float = 0.0
    target_score: float | None = None
    avg_self_level: float = 0.0
    avg_manager_level: float = 0.0
