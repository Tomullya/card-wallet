import pytest
from playwright.sync_api import expect

from tests.e2e.conftest import FRONTEND_URL
from tests.helpers import PASSWORD, register, unique_email


def fill_register(page, email, name, password):
    page.goto(f"{FRONTEND_URL}/register")
    page.get_by_test_id("register-email").fill(email)
    page.get_by_test_id("register-name").fill(name)
    page.get_by_test_id("register-password").fill(password)
    page.get_by_test_id("register-submit").click()


@pytest.mark.req("BR-AUTH-01", "BR-AUTH-02")
def test_register_then_land_on_dashboard(app):
    fill_register(app, unique_email(), "Anna Tester", PASSWORD)
    expect(app.get_by_test_id("user-name")).to_have_text("Anna Tester")
    expect(app).to_have_url(f"{FRONTEND_URL}/")


@pytest.mark.req("BR-AUTH-01")
def test_register_validation_error_shown(app):
    fill_register(app, unique_email(), "Anna", "short12")
    expect(app.get_by_test_id("error-banner")).to_contain_text("password")


@pytest.mark.req("BR-AUTH-02")
def test_login_wrong_password_shows_error(app, api):
    email = unique_email()
    register(api, email)
    app.goto(f"{FRONTEND_URL}/login")
    app.get_by_test_id("login-email").fill(email)
    app.get_by_test_id("login-password").fill("Wrong1234")
    app.get_by_test_id("login-submit").click()
    expect(app.get_by_test_id("error-banner")).to_contain_text("Invalid email or password")


@pytest.mark.req("BR-AUTH-03")
def test_logout_returns_to_login(signed_in):
    page, _ = signed_in
    page.get_by_test_id("logout-button").click()
    expect(page.get_by_test_id("login-email")).to_be_visible()
    page.goto(f"{FRONTEND_URL}/")
    expect(page).to_have_url(f"{FRONTEND_URL}/login")


@pytest.mark.req("BR-AUTH-03")
def test_expired_session_redirects_to_login(signed_in):
    page, _ = signed_in
    page.evaluate("sessionStorage.setItem('cw.token', 'garbage')")
    page.reload()
    expect(page.get_by_test_id("session-message")).to_contain_text("Session expired")
    expect(page).to_have_url(f"{FRONTEND_URL}/login")


@pytest.mark.req("BR-AUTH-03")
def test_session_expiring_during_an_action_redirects_to_login(signed_in, api):
    """401 from an action on an already loaded page (not only on reload)."""
    from tests.helpers import create_account

    page, client = signed_in
    account = create_account(api, client)
    page.goto(f"{FRONTEND_URL}/accounts/{account['id']}")
    expect(page.get_by_test_id("account-balance")).to_have_text("0.00 EUR")
    page.evaluate("sessionStorage.setItem('cw.token', 'garbage')")
    page.get_by_test_id("topup-amount").fill("10.00")
    page.get_by_test_id("topup-submit").click()
    expect(page.get_by_test_id("session-message")).to_contain_text("Session expired")
    expect(page).to_have_url(f"{FRONTEND_URL}/login")
