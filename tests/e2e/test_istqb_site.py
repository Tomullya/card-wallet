"""The ISTQB trainer site (NFR-11)."""

import re

import pytest
from playwright.sync_api import expect


def open_site(page, istqb_url, route=""):
    page.goto(f"{istqb_url}{route}")
    expect(page.get_by_test_id("page-title")).not_to_be_empty()


@pytest.mark.req("NFR-11")
def test_menu_lists_chapters_and_sections(page, istqb_url):
    open_site(page, istqb_url)
    expect(page.locator('nav [data-testid^="chapter-"]')).to_have_count(6)
    expect(page.locator('nav [data-testid^="section-"]')).to_have_count(22)


@pytest.mark.req("NFR-11")
def test_home_shows_chapter_cards(page, istqb_url):
    open_site(page, istqb_url)
    expect(page.get_by_test_id("chapter-card")).to_have_count(6)
    page.get_by_test_id("chapter-card").nth(3).click()
    expect(page).to_have_url(re.compile(r"#/ch/4$"))


@pytest.mark.req("NFR-11")
def test_deep_link_opens_section_tab(page, istqb_url):
    open_site(page, istqb_url, "#/s/4.2/terms")
    expect(page.get_by_test_id("page-title")).to_contain_text("4.2")
    expect(page.get_by_test_id("tab-terms")).to_have_attribute("aria-selected", "true")
    expect(page.get_by_test_id("panel-terms")).to_be_visible()


@pytest.mark.req("NFR-11")
def test_tabs_switch_and_keyboard(page, istqb_url):
    open_site(page, istqb_url, "#/s/1.1/theory")
    page.get_by_test_id("tab-theory").focus()
    page.keyboard.press("ArrowRight")
    expect(page).to_have_url(re.compile(r"#/s/1\.1/terms$"))
    expect(page.get_by_test_id("tab-terms")).to_be_focused()


@pytest.mark.req("NFR-11")
def test_language_switch_keeps_place(page, istqb_url):
    open_site(page, istqb_url, "#/s/4.2/quiz")
    page.get_by_test_id("lang-en").click()
    expect(page).to_have_url(re.compile(r"#/s/4\.2/quiz$"))
    expect(page.get_by_test_id("page-title")).to_contain_text("Black-box Test Techniques")
    page.get_by_test_id("lang-ru").click()
    expect(page.get_by_test_id("page-title")).to_contain_text("Методы черного ящика")


@pytest.mark.req("NFR-11")
def test_theme_toggle(page, istqb_url):
    open_site(page, istqb_url)
    page.get_by_test_id("theme-toggle").click()
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    page.reload()
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")


@pytest.mark.req("NFR-11")
def test_site_works_without_storage(browser, istqb_url):
    context = browser.new_context()
    context.add_init_script(
        "Object.defineProperty(window, 'localStorage', {get() { throw new Error('blocked'); }});"
    )
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    open_site(page, istqb_url, "#/s/2.2/theory")
    page.get_by_test_id("lang-en").click()
    expect(page.get_by_test_id("page-title")).to_contain_text("Test Levels and Test Types")
    assert errors == []
    context.close()


@pytest.mark.req("NFR-11")
def test_footer_disclaimer(page, istqb_url):
    open_site(page, istqb_url)
    page.get_by_test_id("lang-en").click()
    expect(page.get_by_test_id("disclaimer")).to_contain_text(
        "not affiliated with or endorsed by ISTQB/RSTQB"
    )
    expect(page.get_by_test_id("disclaimer")).to_contain_text("v4.0.1")


@pytest.mark.req("NFR-11")
def test_unknown_route_falls_back_home(page, istqb_url):
    open_site(page, istqb_url, "#/s/9.9/theory")
    expect(page.get_by_test_id("chapter-card")).to_have_count(6)
