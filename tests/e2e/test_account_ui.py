import re
import uuid

import pytest
from playwright.sync_api import expect

from tests.e2e.conftest import FRONTEND_URL
from tests.helpers import create_account, register_and_login, top_up


@pytest.fixture
def account_page(signed_in, api):
    page, client = signed_in
    account = create_account(api, client, "EUR")
    page.goto(f"{FRONTEND_URL}/accounts/{account['id']}")
    expect(page.get_by_test_id("account-balance")).to_have_text("0.00 EUR")
    return page, client, account


@pytest.mark.req("BR-ACC-03", "NFR-01")
def test_top_up_updates_balance(account_page):
    page, _, _ = account_page
    page.get_by_test_id("topup-amount").fill("0")
    page.get_by_test_id("topup-submit").click()
    expect(page.get_by_test_id("error-banner")).to_be_visible()
    expect(page.get_by_test_id("account-balance")).to_have_text("0.00 EUR")
    page.get_by_test_id("topup-amount").fill("10000.00")
    page.get_by_test_id("topup-submit").click()
    expect(page.get_by_test_id("account-balance")).to_have_text("10000.00 EUR")


@pytest.mark.req("BR-CARD-02", "BR-CARD-03", "NFR-04")
def test_issue_card_shows_pan_once(account_page):
    page, _, _ = account_page
    page.get_by_test_id("issue-submit").click()
    pan = page.get_by_test_id("issued-pan").inner_text().replace(" ", "")
    assert re.fullmatch(r"400000\d{10}", pan)
    expect(page.get_by_test_id("issued-cvv")).to_have_text(re.compile(r"^\d{3}$"))
    page.get_by_test_id("issued-close").click()
    expect(page.get_by_test_id("card-masked")).to_have_text(f"**** **** **** {pan[-4:]}")
    assert pan not in page.content().replace(" ", "")


@pytest.mark.req("BR-CARD-04")
def test_block_card(account_page):
    page, _, _ = account_page
    page.get_by_test_id("issue-submit").click()
    page.get_by_test_id("issued-close").click()
    page.get_by_test_id("card-block").click()
    expect(page.get_by_test_id("card-status")).to_have_text("BLOCKED")
    expect(page.get_by_test_id("card-block")).to_have_count(0)


@pytest.mark.req("BR-STM-02", "BR-STM-03")
def test_statement_filters_and_pages(account_page, api):
    page, client, account = account_page
    for i in range(12):
        top_up(api, client, account["id"], f"{i + 1}.00")
    page.reload()
    expect(page.get_by_test_id("statement-total")).to_have_text("12 operations")
    expect(page.get_by_test_id("statement-row")).to_have_count(10)
    expect(page.get_by_test_id("tx-amount").first).to_have_text("12.00 EUR")
    page.get_by_test_id("statement-next").click()
    expect(page.get_by_test_id("statement-row")).to_have_count(2)
    page.get_by_test_id("filter-type").select_option("COMMISSION")
    expect(page.get_by_test_id("statement-total")).to_have_text("0 operations")
    expect(page.get_by_test_id("statement-row")).to_have_count(0)


@pytest.mark.req("BR-ACC-02")
def test_foreign_account_shows_not_found(signed_in, api):
    page, _ = signed_in
    stranger = register_and_login(api)
    foreign = create_account(api, stranger, "EUR")
    page.goto(f"{FRONTEND_URL}/accounts/{foreign['id']}")
    expect(page.get_by_test_id("not-found")).to_be_visible()
    page.goto(f"{FRONTEND_URL}/accounts/{uuid.uuid4()}")
    expect(page.get_by_test_id("not-found")).to_be_visible()
