import pytest
from playwright.sync_api import expect


@pytest.mark.req("BR-ACC-01", "BR-ACC-02")
def test_empty_state_then_open_account(signed_in):
    page, _ = signed_in
    expect(page.get_by_test_id("empty-accounts")).to_be_visible()
    page.get_by_test_id("open-account-currency").select_option("EUR")
    page.get_by_test_id("open-account-submit").click()
    expect(page.get_by_test_id("account-balance-EUR")).to_have_text("0.00 EUR")
    expect(page.get_by_test_id("empty-accounts")).to_have_count(0)


@pytest.mark.req("BR-ACC-01")
def test_second_account_same_currency_shows_conflict(signed_in):
    page, _ = signed_in
    for _ in range(2):
        page.get_by_test_id("open-account-currency").select_option("USD")
        page.get_by_test_id("open-account-submit").click()
    expect(page.get_by_test_id("error-banner")).to_contain_text("already have a USD account")
    expect(page.get_by_test_id("account-card-USD")).to_have_count(1)
