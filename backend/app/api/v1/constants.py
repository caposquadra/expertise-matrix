GRADE_TARGETS: dict[str, int] = {"junior": 2, "middle": 3, "senior": 4}

NEXT_GRADE: dict[str, str] = {
    "junior": "middle",
    "middle": "senior",
    "senior": "senior",
}

REVIEW_STATUSES: list[str] = [
    "draft",
    "manager_review",
    "interview",
    "decision",
    "completed",
    "rejected",
]

ACTIVE_REVIEW_STATUSES: list[str] = ["draft", "manager_review", "interview", "decision"]

PROMOTION_THRESHOLD: float = 0.10
