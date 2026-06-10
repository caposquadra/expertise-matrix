"""Schemathesis contract tests — validate API against OpenAPI spec."""

import pytest
from hypothesis import settings
from schemathesis import openapi

from app.main import app

pytestmark = pytest.mark.usefixtures("setup_database")

schema = openapi.from_asgi("/openapi.json", app)


@schema.parametrize()
@settings(max_examples=5)
def test_api_contract(case):
    """Run schemathesis against all endpoints to find contract violations."""
    case.call_and_validate()
