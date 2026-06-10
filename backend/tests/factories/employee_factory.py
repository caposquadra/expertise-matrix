from app.models import Employee
from app.core.security import hash_password


def make_employee(**overrides) -> Employee:
    data = dict(
        email="test@example.com",
        password_hash=hash_password("password123"),
        full_name="Test User",
        role="employee",
        grade="junior",
        is_active=True,
    )
    data.update(overrides)
    return Employee(**data)
