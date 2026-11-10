// Texts in Russian and English. All UI text comes from i18n/{ru,en}.json.

import { getPref, setPref } from "./progress.js";

const texts = {};
let current = "ru";

export async function loadI18n() {
  const [ru, en] = await Promise.all(
    ["ru", "en"].map((l) => fetch(new URL(`../i18n/${l}.json`, import.meta.url)).then((r) => r.json())),
  );
  texts.ru = ru;
  texts.en = en;
  current = getPref("lang", navigator.language?.startsWith("ru") ? "ru" : "en");
  if (!texts[current]) current = "ru";
}

export function lang() {
  return current;
}

export function setLang(value) {
  current = value;
  setPref("lang", value);
}

/** Text for a key; {name} placeholders are filled from vars. */
export function t(key, vars = {}) {
  const text = texts[current]?.[key] ?? texts.ru?.[key] ?? key;
  return text.replace(/\{(\w+)\}/g, (_, name) => String(vars[name] ?? `{${name}}`));
}

/** Fill [data-i18n] (text) and [data-i18n-aria] (aria-label) inside root. */
export function applyStatic(root = document) {
  root.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  root.querySelectorAll("[data-i18n-aria]").forEach((el) => {
    el.setAttribute("aria-label", t(el.dataset.i18nAria));
  });
}

/** A term in both languages: "current (other)", e.g. "граничное значение (boundary value)". */
export function term(pair, language = current) {
  const other = language === "ru" ? "en" : "ru";
  return `${pair[language]} (${pair[other]})`;
}

/** Pick the current language from a {ru, en} pair. */
export function pick(pair, language = current) {
  return pair?.[language] ?? pair?.ru ?? "";
}
