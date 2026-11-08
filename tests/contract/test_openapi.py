"""Contract tests: generated requests must never cause a 5xx, and responses must match
the OpenAPI schema published at /openapi.json (NFR-05, NFR-03)."""

import pytest
import schemathesis
from hypothesis import HealthCheck, settings
from schemathesis.checks import (
    not_a_server_error,
    response_schema_conformance,
    status_code_conformance,
)

from tests.conftest import WALLET_URL


@pytest.fixture
def wallet_schema():
    return schemathesis.openapi.from_url(f"{WALLET_URL}/openapi.json")


schema = schemathesis.pytest.from_fixture("wallet_schema")


@pytest.fixture(scope="session")
def auth_headers(api):
    from tests.helpers import register_and_login

    return register_and_login(api).headers


@pytest.mark.req("NFR-03", "NFR-05")
@schema.parametrize()
@settings(max_examples=50, deadline=None, suppress_health_check=list(HealthCheck))
def test_api_conforms_to_schema(case, auth_headers):
    case.call_and_validate(
        headers=auth_headers,
        checks=[not_a_server_error, response_schema_conformance, status_code_conformance],
    )
