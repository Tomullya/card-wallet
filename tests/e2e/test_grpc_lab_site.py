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


@pytest.mark.req("NFR-09")
def test_comic_has_panels_and_bubbles(page, lab_url):
    open_lab(page, lab_url, "#/05/comic")
    panels = page.get_by_test_id("comic-panel")
    expect(panels.first).to_be_visible()
    assert panels.count() >= 3
    for bubble in page.get_by_test_id("comic-bubble").all():
        assert bubble.inner_text().strip()
    for svg in page.locator("[data-testid=panel-comic] svg").all():
        assert svg.get_attribute("aria-label")


@pytest.mark.req("NFR-09")
@pytest.mark.parametrize(
    ("lesson", "steps"), [("01", 2), ("05", 4), ("06", 5), ("07", 6)]
)
def test_diagram_plays_for_each_call_type(page, lab_url, lesson, steps):
    open_lab(page, lab_url, f"#/{lesson}/diagram")
    expect(page.get_by_test_id("diagram-step")).to_have_count(steps)
    expect(page.get_by_test_id("diagram-replay")).to_be_visible()
    page.get_by_test_id("diagram-replay").click()
    expect(page.get_by_test_id("diagram-step")).to_have_count(steps)


@pytest.mark.req("NFR-09")
def test_reduced_motion_shows_final_state(page, lab_url):
    page.emulate_media(reduced_motion="reduce")
    open_lab(page, lab_url, "#/07/diagram")
    expect(page.get_by_test_id("diagram-step")).to_have_count(6)
    for step in page.get_by_test_id("diagram-step").all():
        assert step.evaluate("el => getComputedStyle(el).opacity") == "1"


SITE = __import__("pathlib").Path(__file__).resolve().parents[2] / "site/grpc-lab"
SCENARIOS = {
    s["id"]: s
    for s in __import__("json").loads((SITE / "scenarios.json").read_text(encoding="utf-8"))
}
LESSONS = {
    lesson["id"]: lesson
    for lesson in __import__("json").loads(
        (SITE / "content/lessons.json").read_text(encoding="utf-8")
    )
}


@pytest.mark.req("NFR-09", "NFR-10")
@pytest.mark.parametrize("preset", LESSONS["05"]["presets"])
def test_sandbox_presets_show_expected_rune(page, lab_url, preset):
    open_lab(page, lab_url, "#/05/sandbox")
    page.get_by_test_id(f"preset-{preset}").click()
    expect(page.get_by_test_id("sandbox-rune-code")).to_have_text(
        SCENARIOS[preset]["expect"]["code"]
    )


@pytest.mark.req("NFR-09")
def test_sandbox_timeline_rows(page, lab_url):
    open_lab(page, lab_url, "#/05/sandbox")
    page.get_by_test_id("preset-watch-sees-payment").click()
    rows = page.get_by_test_id("sandbox-row")
    expect(rows.first).to_be_visible()
    assert rows.count() >= 3  # call, subscription confirmed, event (+ the status row)
    expect(page.get_by_test_id("sandbox-timeline")).to_contain_text("80")


@pytest.mark.req("NFR-09")
def test_sandbox_code_view_toggle(page, lab_url):
    open_lab(page, lab_url, "#/05/sandbox")
    page.get_by_test_id("preset-watch-filter-50").click()
    page.get_by_test_id("sandbox-code-toggle").click()
    code = page.get_by_test_id("sandbox-code")
    expect(code).to_contain_text("WatchRiskEvents")
    expect(code).to_contain_text("x-api-key")
    expect(code).to_contain_text("min_risk_score")


@pytest.mark.req("NFR-09")
def test_quiz_scoring_marks_lesson_done(page, lab_url):
    open_lab(page, lab_url, "#/05/quiz")
    questions = page.get_by_test_id("quiz-question")
    expect(questions).to_have_count(5)
    for i, item in enumerate(LESSONS["05"]["quiz"]):
        questions.nth(i).get_by_test_id("quiz-option").nth(item["answer"]).click()
    expect(page.get_by_test_id("quiz-score")).to_contain_text("5")
    page.reload()
    expect(page.get_by_test_id("done-05")).to_be_visible()


@pytest.mark.req("NFR-09")
def test_quiz_explains_wrong_answer(page, lab_url):
    open_lab(page, lab_url, "#/05/quiz")
    first = page.get_by_test_id("quiz-question").first
    wrong = (LESSONS["05"]["quiz"][0]["answer"] + 1) % len(LESSONS["05"]["quiz"][0]["options"])
    first.get_by_test_id("quiz-option").nth(wrong).click()
    expect(first.get_by_test_id("quiz-option").nth(wrong)).to_have_attribute("data-state", "wrong")
    expect(first.get_by_test_id("quiz-why")).to_be_visible()


@pytest.mark.req("NFR-09")
def test_theory_and_practice_have_content(page, lab_url):
    open_lab(page, lab_url, "#/05/theory")
    assert len(page.get_by_test_id("panel-theory").inner_text()) > 400
    page.get_by_test_id("tab-practice").click()
    expect(page.get_by_test_id("practice-check")).to_contain_text("grpc_lab_check.py 5")
    expect(page.get_by_test_id("practice-link").first).to_have_attribute(
        "href", re.compile(r"^https://github.com/Tomullya/card-wallet/blob/main/")
    )


@pytest.mark.req("NFR-09")
def test_practice_explains_where_and_how(page, lab_url):
    """Author feedback: the practice tab did not say where to write tests or where to look."""
    open_lab(page, lab_url, "#/05/practice")
    steps = page.get_by_test_id("practice-steps").locator("li")
    assert steps.count() >= 5
    expect(page.get_by_test_id("practice-steps")).to_contain_text(
        "grpc-lab/exercises/test_lab_05_server_streaming.py"
    )
    expect(page.get_by_test_id("practice-example")).to_contain_text("Watch(stub")
    expect(page.get_by_test_id("practice-example")).to_contain_text("assert")
    expect(page.get_by_test_id("practice-helpers")).to_contain_text("lab.py")


TABS = ["comic", "theory", "diagram", "sandbox", "quiz", "practice"]


@pytest.mark.req("NFR-09")
@pytest.mark.parametrize("lesson", ["00", "01", "02", "03", "04", "06", "07", "08"])
@pytest.mark.parametrize("lang", ["ru", "en"])
def test_lesson_tabs_are_filled(page, lab_url, lesson, lang):
    open_lab(page, lab_url, f"#/{lesson}/comic")
    page.get_by_test_id(f"lang-{lang}").click()
    for tab in TABS:
        page.get_by_test_id(f"tab-{tab}").click()
        panel = page.get_by_test_id(f"panel-{tab}")
        expect(panel).to_be_visible()
        assert panel.locator(".placeholder-note:not(.sandbox *)").count() == 0, f"{tab} is empty"
    page.get_by_test_id("tab-quiz").click()
    expect(page.get_by_test_id("quiz-question")).to_have_count(5)


@pytest.mark.req("NFR-09", "NFR-10")
@pytest.mark.parametrize(
    ("lesson", "preset"),
    [(lid, p) for lid in ["01", "02", "03", "04", "06", "07"] for p in LESSONS[lid]["presets"]],
)
def test_lesson_presets_show_expected_rune(page, lab_url, lesson, preset):
    open_lab(page, lab_url, f"#/{lesson}/sandbox")
    page.get_by_test_id(f"preset-{preset}").click()
    expect(page.get_by_test_id("sandbox-rune-code")).to_have_text(SCENARIOS[preset]["expect"]["code"])


@pytest.mark.req("NFR-09")
def test_lesson_00_compares_json_and_protobuf(page, lab_url):
    open_lab(page, lab_url, "#/00/sandbox")
    json_size = int(page.get_by_test_id("compare-json-bytes").inner_text())
    proto_size = int(page.get_by_test_id("compare-proto-bytes").inner_text())
    assert 0 < proto_size < json_size
    page.get_by_test_id("compare-amount").fill("123456.78")
    expect(page.get_by_test_id("compare-proto")).to_contain_text("123456.78")
    expect(page.get_by_test_id("compare-fields")).to_contain_text("4")  # amount is field 4


@pytest.mark.req("NFR-09", "NFR-10")
@pytest.mark.parametrize("preset", ["bug17-forged-seal", "bug18-bidi-hangs", "bug19-no-trailer"])
def test_bug_hunt_switch_reveals_bugs(page, lab_url, preset):
    open_lab(page, lab_url, "#/08/sandbox")
    switch = page.get_by_test_id("buggy-switch")
    expect(switch).not_to_be_checked()
    page.get_by_test_id(f"preset-{preset}").click()
    expect(page.get_by_test_id("buggy-switch")).to_be_checked()
    expect(page.get_by_test_id("sandbox-rune-code")).to_have_text(SCENARIOS[preset]["expect"]["code"])
    page.get_by_test_id("buggy-switch").uncheck()
    page.get_by_test_id("sandbox-send").click()
    healthy = {
        "bug17-forged-seal": "UNAUTHENTICATED",
        "bug18-bidi-hangs": "OK",
        "bug19-no-trailer": "OK",
    }
    expect(page.get_by_test_id("sandbox-rune-code")).to_have_text(healthy[preset])


# --- found in final review ---------------------------------------------------


def contrast(page, locator) -> float:
    return locator.evaluate(
        """el => {
          const rgb = s => s.match(/\\d+(\\.\\d+)?/g).slice(0, 3).map(Number);
          const lum = c => { const [r, g, b] = c.map(v => { v /= 255;
            return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; });
            return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
          const cs = getComputedStyle(el);
          const a = lum(rgb(cs.color)), b = lum(rgb(cs.backgroundColor));
          return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
        }"""
    )


@pytest.mark.req("NFR-09")
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_buttons_and_quiz_marks_have_enough_contrast(page, lab_url, theme):
    open_lab(page, lab_url, "#/05/sandbox")
    if theme == "dark":
        page.get_by_test_id("theme-toggle").click()
    assert contrast(page, page.get_by_test_id("sandbox-send")) >= 4.5
    page.get_by_test_id("tab-quiz").click()
    first = page.get_by_test_id("quiz-question").first
    wrong = (LESSONS["05"]["quiz"][0]["answer"] + 1) % 3
    first.get_by_test_id("quiz-option").nth(wrong).click()
    assert contrast(page, first.locator("[data-state=wrong]")) >= 4.5
    assert contrast(page, first.locator("[data-state=right]")) >= 4.5


@pytest.mark.req("NFR-09")
def test_arrow_keys_move_between_tabs(page, lab_url):
    open_lab(page, lab_url, "#/05/comic")
    page.get_by_test_id("tab-comic").focus()
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowRight")
    expect(page).to_have_url(re.compile(r"#/05/diagram$"))
    expect(page.get_by_test_id("tab-diagram")).to_be_focused()


@pytest.mark.req("NFR-09")
def test_skip_link_keeps_the_lesson(page, lab_url):
    open_lab(page, lab_url, "#/05/sandbox")
    page.keyboard.press("Tab")
    page.keyboard.press("Enter")
    expect(page).to_have_url(re.compile(r"#/05/sandbox$"))
    expect(page.locator("#main")).to_be_focused()


@pytest.mark.req("NFR-09")
def test_preset_batch_size_does_not_leak_into_other_methods(page, lab_url):
    open_lab(page, lab_url, "#/06/sandbox")
    page.get_by_test_id("preset-batch-1001").click()
    expect(page.get_by_test_id("sandbox-batch-size")).to_have_value("1001")
    page.locator(".sandbox__form select").first.select_option("ScorePayments")
    page.get_by_test_id("sandbox-send").click()
    expect(page.get_by_test_id("sandbox-rune-code")).to_have_text("OK")


@pytest.mark.req("NFR-09")
def test_form_rejects_values_a_real_client_cannot_send(page, lab_url):
    open_lab(page, lab_url, "#/05/sandbox")
    page.get_by_test_id("sandbox-request-id").fill("лаб-1")
    page.get_by_test_id("sandbox-send").click()
    expect(page.get_by_test_id("sandbox-error")).to_be_visible()
    expect(page.get_by_test_id("sandbox-rune-code")).to_have_count(0)
    page.get_by_test_id("sandbox-request-id").fill("lab-1")
    page.get_by_test_id("sandbox-min-risk").fill("79.5")
    page.get_by_test_id("sandbox-send").click()
    expect(page.get_by_test_id("sandbox-error")).to_be_visible()


@pytest.mark.req("NFR-09")
@pytest.mark.parametrize("tab", ["theory", "practice", "sandbox"])
def test_no_horizontal_scroll_on_a_phone(page, lab_url, tab):
    page.set_viewport_size({"width": 375, "height": 800})
    open_lab(page, lab_url, f"#/05/{tab}")
    overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
    assert overflow <= 1


@pytest.mark.req("NFR-09")
def test_theory_lists_official_sources(page, lab_url):
    for lesson in ["00", "03", "05", "08"]:
        open_lab(page, lab_url, f"#/{lesson}/theory")
        links = page.get_by_test_id("theory-sources").locator("a")
        assert links.count() >= 2
        for href in links.evaluate_all("els => els.map(e => e.href)"):
            assert href.startswith(("https://grpc.io/", "https://protobuf.dev/"))
