import re

import pytest
from playwright.sync_api import expect

from tests.e2e.conftest import FRONTEND_URL


@pytest.mark.req("NFR-07")
def test_login_page_loads(app):
    app.goto(f"{FRONTEND_URL}/login")
    expect(app.get_by_test_id("login-email")).to_be_visible()
    expect(app).to_have_title(re.compile("Card Wallet"))
