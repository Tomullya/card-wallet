"""End-to-end tests through the browser (Playwright, Chromium)."""

import os

import pytest

from tests.helpers import PASSWORD, register_and_login

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@pytest.fixture
def app(page):
    page.set_default_timeout(10_000)
    return page


@pytest.fixture
def signed_in(app, api):
    """A client registered through the API and logged in through the UI."""
    client = register_and_login(api)
    app.goto(f"{FRONTEND_URL}/login")
    app.get_by_test_id("login-email").fill(client.email)
    app.get_by_test_id("login-password").fill(PASSWORD)
    app.get_by_test_id("login-submit").click()
    app.get_by_test_id("user-name").wait_for()
    return app, client
