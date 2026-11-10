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


# ---------- section 4.2 ----------


@pytest.mark.req("NFR-11")
def test_theory_shows_lo_quote_and_wallet_example(page, istqb_url):
    open_site(page, istqb_url, "#/s/4.2/theory")
    page.get_by_test_id("lang-ru").click()
    objectives = page.get_by_test_id("objective")
    expect(objectives).to_have_count(4)
    first = objectives.first
    expect(first.get_by_test_id("lo-badge")).to_have_text("K3")
    expect(first.get_by_test_id("lo-quote")).to_contain_text("эквивалентного разбиения")
    expect(first.get_by_test_id("lo-source")).to_contain_text("§4.2.1")
    expect(first.get_by_test_id("wallet-example")).to_be_visible()
    links = page.get_by_test_id("syllabus-link")
    expect(links).to_have_count(2)
    expect(links.first).to_have_attribute("href", re.compile(r"ISTQB_CTFL_Syllabus"))


@pytest.mark.req("NFR-11")
def test_terms_show_both_languages(page, istqb_url):
    open_site(page, istqb_url, "#/s/4.2/terms")
    first = page.get_by_test_id("term").first
    expect(first).to_contain_text("эквивалентное разбиение")
    expect(first).to_contain_text("equivalence partitioning")
    page.get_by_test_id("lang-en").click()
    expect(page.get_by_test_id("term-name").first).to_have_text(
        re.compile(r"^equivalence partitioning \(")
    )


@pytest.mark.req("NFR-11")
def test_section_quiz_marks_done(page, istqb_url):
    open_site(page, istqb_url, "#/s/4.2/quiz")
    questions = page.get_by_test_id("quiz-question")
    expect(questions).to_have_count(5)
    for i in range(5):
        q = questions.nth(i)
        q.locator('[data-correct="true"]').first.click()
        if q.locator('[data-testid="quiz-check"]').count():  # select-TWO questions
            q.locator('[data-correct="true"]').nth(1).click()
            q.get_by_test_id("quiz-check").click()
        expect(q.get_by_test_id("quiz-why")).to_be_visible()
    expect(page.get_by_test_id("quiz-score")).to_contain_text("5")
    expect(page.get_by_test_id("done-4.2")).to_be_visible()


@pytest.mark.req("NFR-11")
def test_quiz_retake_shows_other_questions(page, istqb_url):
    open_site(page, istqb_url, "#/s/4.2/quiz")
    first = page.get_by_test_id("quiz-question").first.locator("legend").inner_text()
    questions = page.get_by_test_id("quiz-question")
    for i in range(5):
        questions.nth(i).get_by_test_id("quiz-option").first.click()
        if questions.nth(i).get_by_test_id("quiz-check").count():
            questions.nth(i).get_by_test_id("quiz-option").nth(1).click()
            questions.nth(i).get_by_test_id("quiz-check").click()
    page.get_by_test_id("quiz-retake").click()
    expect(page.get_by_test_id("quiz-question").first.locator("legend")).not_to_have_text(first)


@pytest.mark.req("NFR-11", "NFR-12")
def test_ep_trainer_reports_missing_partition(page, istqb_url):
    open_site(page, istqb_url, "#/s/4.2/trainer")
    trainer = page.get_by_test_id("trainer-ep")
    trainer.get_by_test_id("trainer-input").fill("100; 6000; -5")
    trainer.get_by_test_id("trainer-check").click()
    result = trainer.get_by_test_id("trainer-result")
    expect(result).to_contain_text("75%")
    expect(result.get_by_test_id("missing")).to_contain_text("10000")


@pytest.mark.req("NFR-11", "NFR-12")
def test_ep_trainer_accepts_russian_number_format(page, istqb_url):
    open_site(page, istqb_url, "#/s/4.2/trainer")
    trainer = page.get_by_test_id("trainer-ep")
    trainer.get_by_test_id("trainer-input").fill("-1; 2 500,50; 7 500,00; 10 000,01")
    trainer.get_by_test_id("trainer-check").click()
    expect(trainer.get_by_test_id("trainer-result")).to_contain_text("100%")


@pytest.mark.req("NFR-11", "NFR-12")
def test_trainer_explains_garbage_input(page, istqb_url):
    open_site(page, istqb_url, "#/s/4.2/trainer")
    trainer = page.get_by_test_id("trainer-ep")
    trainer.get_by_test_id("trainer-input").fill("abc")
    trainer.get_by_test_id("trainer-check").click()
    expect(trainer.get_by_test_id("trainer-invalid")).to_contain_text("abc")


@pytest.mark.req("NFR-11", "NFR-12")
def test_bva_trainer_variant_switch(page, istqb_url):
    open_site(page, istqb_url, "#/s/4.2/trainer")
    trainer = page.get_by_test_id("trainer-bva")
    trainer.get_by_test_id("trainer-input").fill("5000; 5000,01")
    trainer.get_by_test_id("trainer-check").click()
    expect(trainer.get_by_test_id("trainer-result")).to_contain_text("100%")
    trainer.get_by_test_id("bva-variant-3").check()
    trainer.get_by_test_id("trainer-check").click()
    expect(trainer.get_by_test_id("trainer-result")).to_contain_text("50%")
    expect(trainer.get_by_test_id("missing")).to_contain_text("4999.99")
    expect(trainer.get_by_test_id("missing")).to_contain_text("5000.02")


# ---------- trainers: decision table, state transitions, code coverage ----------


@pytest.mark.req("NFR-11", "NFR-12")
def test_decision_table_trainer_finds_missing_column(page, istqb_url):
    open_site(page, istqb_url, "#/s/4.2/trainer")
    trainer = page.get_by_test_id("trainer-decision")
    selects = trainer.get_by_test_id("dt-action")
    expect(selects).to_have_count(4)
    selects.nth(0).select_option("DECLINE_HIGH")
    selects.nth(1).select_option("DECLINE_HIGH")
    selects.nth(2).select_option("DECLINE_CATEGORY")
    trainer.get_by_test_id("trainer-check").click()
    result = trainer.get_by_test_id("trainer-result")
    expect(result).to_contain_text("75%")
    expect(result.get_by_test_id("missing")).to_be_visible()
    expect(result.get_by_test_id("dt-minimised")).to_be_visible()


@pytest.mark.req("NFR-11", "NFR-12")
def test_decision_table_trainer_flags_wrong_action(page, istqb_url):
    open_site(page, istqb_url, "#/s/4.2/trainer")
    trainer = page.get_by_test_id("trainer-decision")
    selects = trainer.get_by_test_id("dt-action")
    for i, action in enumerate(["DECLINE_CATEGORY", "DECLINE_HIGH", "DECLINE_CATEGORY", "APPROVE"]):
        selects.nth(i).select_option(action)
    trainer.get_by_test_id("trainer-check").click()
    expect(trainer.get_by_test_id("dt-wrong")).to_be_visible()


@pytest.mark.req("NFR-11", "NFR-12")
def test_state_trainer_counts_transitions(page, istqb_url):
    open_site(page, istqb_url, "#/s/4.2/trainer")
    trainer = page.get_by_test_id("trainer-state")
    trainer.get_by_test_id("event-blockByClient").click()
    trainer.get_by_test_id("event-expiryPassed").click()
    result = trainer.get_by_test_id("trainer-result")
    expect(result.get_by_test_id("state-valid")).to_contain_text("50%")
    expect(result.get_by_test_id("state-states")).to_contain_text("67%")
    trainer.get_by_test_id("state-new-test").click()
    trainer.get_by_test_id("event-expiryPassed").click()
    trainer.get_by_test_id("event-blockByClient").click()
    expect(result.get_by_test_id("state-invalid")).to_contain_text("BUG-13")
    steps = trainer.get_by_test_id("state-test")
    expect(steps.nth(0)).to_contain_text("BLOCKED")
    expect(steps.nth(1)).to_contain_text("EXPIRED")
    expect(steps.nth(1)).to_contain_text("✗")
    expect(result.get_by_test_id("state-states")).to_contain_text("100%")


@pytest.mark.req("NFR-11", "NFR-12")
def test_coverage_trainer_statement_vs_branch(page, istqb_url):
    open_site(page, istqb_url, "#/s/4.3/trainer")
    trainer = page.get_by_test_id("trainer-coverage")
    trainer.get_by_test_id("trainer-input").fill("10")
    trainer.get_by_test_id("trainer-check").click()
    result = trainer.get_by_test_id("trainer-result")
    expect(result.get_by_test_id("cov-statement")).to_contain_text("100%")
    expect(result.get_by_test_id("cov-branch")).to_contain_text("75%")
    expect(trainer.locator('[data-testid="code-line"][data-hit="true"]')).to_have_count(4)
    trainer.get_by_test_id("cov-program-fraud").check()
    trainer.get_by_test_id("trainer-input").fill("6000 OTHER\n10 GAMBLING\n10 OTHER")
    trainer.get_by_test_id("trainer-check").click()
    expect(result.get_by_test_id("cov-branch")).to_contain_text("100%")


@pytest.mark.req("NFR-11")
def test_section_43_theory_and_quiz(page, istqb_url):
    open_site(page, istqb_url, "#/s/4.3/theory")
    expect(page.get_by_test_id("objective")).to_have_count(3)
    page.get_by_test_id("tab-quiz").click()
    expect(page.get_by_test_id("quiz-question")).to_have_count(5)


# ---------- chapter pages ----------


@pytest.mark.req("NFR-11")
@pytest.mark.parametrize("chapter", ["1", "2", "3", "4", "5", "6"])
def test_chapter_page_has_comic_and_sections(page, istqb_url, chapter):
    open_site(page, istqb_url, f"#/ch/{chapter}")
    panels = page.get_by_test_id("comic-panel")
    expect(panels.first).to_be_visible()
    assert 3 <= panels.count() <= 4
    expect(page.get_by_test_id("comic-bubble").first).not_to_be_empty()
    expect(page.get_by_test_id("chapter-section").first).to_be_visible()
    page.get_by_test_id("chapter-section").first.click()
    expect(page).to_have_url(re.compile(rf"#/s/{chapter}\.1/theory$"))


# ---------- glossary and mock exam ----------


@pytest.mark.req("NFR-11")
def test_glossary_search_both_languages(page, istqb_url):
    open_site(page, istqb_url, "#/glossary")
    terms = page.get_by_test_id("glossary-term")
    expect(terms.first).to_be_visible()
    total = terms.count()
    page.get_by_test_id("glossary-search").fill("граничн")
    expect(terms.filter(visible=True).first).to_contain_text("boundary value")
    ru_hits = terms.filter(visible=True).count()
    page.get_by_test_id("glossary-search").fill("boundary")
    expect(terms.filter(visible=True)).to_have_count(ru_hits)
    assert ru_hits < total


def start_exam(page, istqb_url):
    open_site(page, istqb_url, "#/exam")
    page.get_by_test_id("exam-start").click()
    expect(page.get_by_test_id("exam-question")).to_have_count(40)


@pytest.mark.req("NFR-11")
def test_official_samples_links(page, istqb_url):
    open_site(page, istqb_url, "#/exam")
    links = page.get_by_test_id("sample-link")
    assert links.count() >= 4
    for i in range(links.count()):
        expect(links.nth(i)).to_have_attribute(
            "href", re.compile(r"^https://(www\.)?(istqb\.org|rstqb\.org)/")
        )


@pytest.mark.req("NFR-11")
def test_mock_exam_full_run(page, istqb_url):
    start_exam(page, istqb_url)
    expect(page.get_by_test_id("exam-timer")).to_contain_text(re.compile(r"\d+:\d\d"))
    questions = page.get_by_test_id("exam-question")
    for i in range(40):
        inputs = questions.nth(i).locator("input")
        inputs.nth(0).check()
        if inputs.nth(0).get_attribute("type") == "checkbox":
            inputs.nth(1).check()
    expect(page.get_by_test_id("exam-answered")).to_contain_text("40")
    page.get_by_test_id("exam-submit").click()
    page.get_by_test_id("exam-confirm").click()
    expect(page.get_by_test_id("exam-score")).to_contain_text("/ 40")
    expect(page.get_by_test_id("exam-chapter-row")).to_have_count(6)
    review = page.get_by_test_id("exam-review-item")
    if review.count():
        expect(review.first.get_by_test_id("quiz-why")).to_be_visible()


@pytest.mark.req("NFR-11")
def test_language_switch_keeps_exam(page, istqb_url):
    start_exam(page, istqb_url)
    first = page.get_by_test_id("exam-question").first.locator("input")
    first.nth(1).check()
    page.get_by_test_id("lang-en").click()
    expect(page.get_by_test_id("exam-question")).to_have_count(40)
    expect(page.get_by_test_id("exam-question").first.locator("input").nth(1)).to_be_checked()
    expect(page.get_by_test_id("exam-answered")).to_contain_text("1")


@pytest.mark.req("NFR-11")
def test_exam_survives_reload(page, istqb_url):
    start_exam(page, istqb_url)
    page.get_by_test_id("exam-question").nth(2).locator("input").nth(0).check()
    page.reload()
    expect(page.get_by_test_id("exam-question")).to_have_count(40)
    expect(page.get_by_test_id("exam-question").nth(2).locator("input").nth(0)).to_be_checked()


@pytest.mark.req("NFR-11")
def test_submit_confirmation_is_visible(page, istqb_url):
    start_exam(page, istqb_url)
    page.get_by_test_id("exam-question").nth(5).scroll_into_view_if_needed()
    page.get_by_test_id("exam-submit").click()
    expect(page.get_by_test_id("exam-confirm")).to_be_in_viewport()
    expect(page.get_by_test_id("exam-confirm")).to_be_focused()


@pytest.mark.req("NFR-11")
def test_exam_submits_itself_when_time_runs_out(page, istqb_url):
    start_exam(page, istqb_url)
    page.get_by_test_id("exam-question").first.locator("input").nth(0).check()
    page.evaluate(
        """() => {
          const data = JSON.parse(localStorage.getItem("istqb-lab"));
          data.exam.startedAt = Date.now() - data.exam.minutes * 60000 + 1500;
          localStorage.setItem("istqb-lab", JSON.stringify(data));
        }"""
    )
    expect(page.get_by_test_id("exam-score")).to_be_visible(timeout=6000)
    expect(page.get_by_test_id("exam-score")).to_contain_text("/ 40")


@pytest.mark.req("NFR-11")
def test_reload_keeps_remaining_time(page, istqb_url):
    start_exam(page, istqb_url)
    page.evaluate(
        """() => {
          const data = JSON.parse(localStorage.getItem("istqb-lab"));
          data.exam.startedAt -= 15 * 60000;
          localStorage.setItem("istqb-lab", JSON.stringify(data));
        }"""
    )
    page.reload()
    expect(page.get_by_test_id("exam-timer")).to_have_text(re.compile(r"^(4[0-4]|45):\d\d$"))
