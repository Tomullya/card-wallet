"""The interactive gRPC trainer site (NFR-09)."""

import re

import pytest
from playwright.sync_api import expect


def open_lab(page, lab_url, route=""):
    page.goto(f"{lab_url}{route}")
    expect(page.get_by_test_id("lesson-title")).to_be_visible()


@pytest.mark.req("NFR-09")
def test_menu_lists_nine_lessons(page, lab_url):
    open_lab(page, lab_url)
    expect(page.locator('nav [data-testid^="lesson-0"]')).to_have_count(9)


@pytest.mark.req("NFR-09")
def test_tabs_switch_content(page, lab_url):
    open_lab(page, lab_url)
    page.get_by_test_id("tab-theory").click()
    expect(page).to_have_url(re.compile(r"#/00/theory$"))
    expect(page.get_by_test_id("panel-theory")).to_be_visible()
    expect(page.get_by_test_id("tab-theory")).to_have_attribute("aria-selected", "true")


@pytest.mark.req("NFR-09")
def test_deep_link_opens_tab(page, lab_url):
    open_lab(page, lab_url, "#/03/practice")
    expect(page.get_by_test_id("tab-practice")).to_have_attribute("aria-selected", "true")
    expect(page.get_by_test_id("lesson-03")).to_have_attribute("aria-current", "page")


@pytest.mark.req("NFR-09")
def test_language_switch_keeps_place(page, lab_url):
    open_lab(page, lab_url, "#/05/quiz")
    page.get_by_test_id("lang-en").click()
    expect(page).to_have_url(re.compile(r"#/05/quiz$"))
    expect(page.get_by_test_id("lesson-title")).to_have_text("Server streaming")
    expect(page.locator("html")).to_have_attribute("lang", "en")
    page.get_by_test_id("lang-ru").click()
    expect(page.get_by_test_id("lesson-title")).to_have_text("Поток от сервера")


@pytest.mark.req("NFR-09")
def test_theme_toggle_persists(page, lab_url):
    open_lab(page, lab_url)
    page.get_by_test_id("theme-toggle").click()
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    page.reload()
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")


@pytest.mark.req("NFR-09")
def test_site_works_without_storage(browser, lab_url):
    context = browser.new_context()
    context.add_init_script(
        "Object.defineProperty(window, 'localStorage', {get() { throw new Error('blocked'); }});"
    )
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    open_lab(page, lab_url, "#/05/theory")
    page.get_by_test_id("lang-en").click()
    expect(page.get_by_test_id("lesson-title")).to_have_text("Server streaming")
    assert errors == []
    context.close()
