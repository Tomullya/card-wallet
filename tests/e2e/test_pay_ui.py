import pytest
from playwright.sync_api import expect

from tests.e2e.conftest import FRONTEND_URL
from tests.helpers import PASSWORD, balance_of, funded_card, unique_email, wrong_cvv


def fill_payment(page, cvv, amount="10.00", merchant="Coffee Shop", category="RESTAURANTS"):
    page.goto(f"{FRONTEND_URL}/pay")
    page.get_by_test_id("pay-cvv").fill(cvv)
    page.get_by_test_id("pay-amount").fill(amount)
    page.get_by_test_id("pay-merchant").fill(merchant)
    page.get_by_test_id("pay-category").select_option(category)


@pytest.mark.req("BR-AUTH-01", "BR-ACC-03", "BR-CARD-02", "BR-PAY-05", "BR-STM-01")
def test_full_journey(app):
    """Everything through the browser: register → account → top-up → card → pay → statement."""
    app.goto(f"{FRONTEND_URL}/register")
    app.get_by_test_id("register-email").fill(unique_email())
    app.get_by_test_id("register-name").fill("Anna Tester")
    app.get_by_test_id("register-password").fill(PASSWORD)
    app.get_by_test_id("register-submit").click()

    app.get_by_test_id("open-account-currency").select_option("EUR")
    app.get_by_test_id("open-account-submit").click()
    app.get_by_test_id("account-card-EUR").click()
    app.get_by_test_id("topup-amount").fill("100.00")
    app.get_by_test_id("topup-submit").click()
    expect(app.get_by_test_id("account-balance")).to_have_text("100.00 EUR")

    app.get_by_test_id("issue-submit").click()
    cvv = app.get_by_test_id("issued-cvv").inner_text()
    app.get_by_test_id("issued-close").click()

    fill_payment(app, cvv)
    app.get_by_test_id("pay-submit").click()
    expect(app.get_by_test_id("pay-status")).to_have_text("APPROVED")
    expect(app.get_by_test_id("pay-commission")).to_have_text("0.50 EUR")

    app.get_by_test_id("pay-account-link").click()
    expect(app.get_by_test_id("account-balance")).to_have_text("89.50 EUR")
    expect(app.get_by_test_id("tx-type")).to_have_count(3)  # the statement loads after the balance
    types = app.get_by_test_id("tx-type").all_inner_texts()
    assert sorted(types) == ["Commission", "Payment", "Top-up"]


@pytest.mark.req("BR-CARD-06", "BR-PAY-06")
def test_wrong_cvv_declined(signed_in, api):
    page, client = signed_in
    card = funded_card(api, client, "100.00")
    fill_payment(page, wrong_cvv(card["cvv"]))
    page.get_by_test_id("pay-submit").click()
    expect(page.get_by_test_id("pay-status")).to_have_text("DECLINED")
    expect(page.get_by_test_id("pay-reason")).to_have_text("INVALID_CVV")
    assert balance_of(api, client, card["account_id"]) == "100.00"


@pytest.mark.req("BR-PAY-07")
def test_double_click_pays_once(signed_in, api, db):
    page, client = signed_in
    card = funded_card(api, client, "100.00")
    fill_payment(page, card["cvv"])
    page.get_by_test_id("pay-submit").dblclick()
    expect(page.get_by_test_id("pay-status")).to_have_text("APPROVED")
    page.wait_for_timeout(500)
    rows = db.execute(
        "select count(*) from transactions where card_id = %s and type = 'PAYMENT'", (card["id"],)
    ).fetchone()[0]
    assert rows == 1
    assert balance_of(api, client, card["account_id"]) == "89.50"


@pytest.mark.req("BR-PAY-08")
def test_fraud_unavailable_message(signed_in, api):
    page, client = signed_in
    card = funded_card(api, client, "100.00")
    fill_payment(page, card["cvv"], merchant="TEST_TIMEOUT")
    page.get_by_test_id("pay-submit").click()
    expect(page.get_by_test_id("error-banner")).to_contain_text("try again")
    expect(page.get_by_test_id("pay-result")).to_have_count(0)
    assert balance_of(api, client, card["account_id"]) == "100.00"


def payment_rows(db, card_id):
    return db.execute(
        "select count(*) from transactions where card_id = %s and type = 'PAYMENT'", (card_id,)
    ).fetchone()[0]


@pytest.mark.req("BR-PAY-05", "BR-PAY-07")
def test_repeat_payment_with_same_values_charges_again(signed_in, api, db):
    """Found in final review: a second identical purchase silently replayed the first result."""
    page, client = signed_in
    card = funded_card(api, client, "100.00")
    fill_payment(page, card["cvv"])
    page.get_by_test_id("pay-submit").click()
    expect(page.get_by_test_id("pay-status")).to_have_text("APPROVED")
    page.get_by_test_id("pay-cvv").fill(card["cvv"])
    page.get_by_test_id("pay-submit").click()
    expect(page.get_by_test_id("pay-status")).to_have_text("APPROVED")
    page.wait_for_timeout(300)
    assert payment_rows(db, card["id"]) == 2
    assert balance_of(api, client, card["account_id"]) == "79.00"


@pytest.mark.req("NFR-04")
def test_cvv_cleared_after_payment(signed_in, api):
    page, client = signed_in
    card = funded_card(api, client, "100.00")
    fill_payment(page, card["cvv"])
    page.get_by_test_id("pay-submit").click()
    expect(page.get_by_test_id("pay-status")).to_have_text("APPROVED")
    expect(page.get_by_test_id("pay-cvv")).to_have_value("")
