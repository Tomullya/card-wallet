// Tiny DOM helper: el("p", {className: "x", dataset: {testid: "y"}}, "text", child, …).

export function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  const { dataset, attrs, ...rest } = props;
  Object.assign(node, rest);
  Object.entries(dataset ?? {}).forEach(([k, v]) => (node.dataset[k] = v));
  Object.entries(attrs ?? {}).forEach(([k, v]) => node.setAttribute(k, v));
  node.append(...children.filter((c) => c !== null && c !== undefined && c !== false));
  return node;
}

/** 500001 → "5000.01" (dot, like the API). */
export function money(cents) {
  const sign = cents < 0 ? "−" : "";
  const abs = Math.abs(cents);
  return `${sign}${Math.floor(abs / 100)}.${String(abs % 100).padStart(2, "0")}`;
}
