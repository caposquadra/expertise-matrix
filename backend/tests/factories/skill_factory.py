from app.models import Skill


def make_skill(**overrides) -> Skill:
    data = dict(name="Test Skill", category="Testing", description="Test", sort_order=1, is_active=True)
    data.update(overrides)
    return Skill(**data)
