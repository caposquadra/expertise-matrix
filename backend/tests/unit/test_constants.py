"""Unit tests for API constants."""

from app.api.v1.constants import (
    ACTIVE_REVIEW_STATUSES,
    GRADE_TARGETS,
    NEXT_GRADE,
    PROMOTION_THRESHOLD,
    REVIEW_STATUSES,
)


class TestGradeTargets:
    def test_known_grades(self):
        assert GRADE_TARGETS["junior"] == 2
        assert GRADE_TARGETS["middle"] == 3
        assert GRADE_TARGETS["senior"] == 4

    def test_unknown_grade_fallback(self):
        assert GRADE_TARGETS.get("lead", 3) == 3


class TestNextGrade:
    def test_next_grade_mapping(self):
        assert NEXT_GRADE["junior"] == "middle"
        assert NEXT_GRADE["middle"] == "senior"
        assert NEXT_GRADE["senior"] == "senior"

    def test_next_grade_unknown(self):
        assert NEXT_GRADE.get("lead", "lead") == "lead"


class TestReviewStatuses:
    def test_all_statuses(self):
        assert len(REVIEW_STATUSES) == 6
        assert "draft" in REVIEW_STATUSES
        assert "completed" in REVIEW_STATUSES
        assert "rejected" in REVIEW_STATUSES

    def test_active_statuses_subset(self):
        for s in ACTIVE_REVIEW_STATUSES:
            assert s in REVIEW_STATUSES
        assert len(ACTIVE_REVIEW_STATUSES) < len(REVIEW_STATUSES)


class TestPromotionThreshold:
    def test_threshold_value(self):
        assert PROMOTION_THRESHOLD == 0.10
