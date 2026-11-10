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


@pytest.fixture(scope="session")
def site_base():
    """Serve site/ locally (ES modules need http://, not file://) and return its base URL."""
    import socket
    import subprocess
    import sys
    import time
    from pathlib import Path

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    site = Path(__file__).resolve().parents[2] / "site"
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=site,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    yield f"http://127.0.0.1:{port}"
    server.terminate()
    server.wait(5)


@pytest.fixture(scope="session")
def lab_url(site_base):
    return f"{site_base}/grpc-lab/index.html"


@pytest.fixture(scope="session")
def istqb_url(site_base):
    return f"{site_base}/istqb/index.html"
