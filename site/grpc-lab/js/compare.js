// Lesson 00 sandbox: the same CheckPaymentRequest as JSON text and as protobuf bytes.
// Field numbers come from proto/fraudpb/fraud.proto.

export const FIELDS = [
  [1, "transaction_id"], [2, "user_id"], [3, "card_last4"], [4, "amount"],
  [5, "currency"], [6, "merchant_name"], [7, "merchant_category"],
];

const encoder = new TextEncoder();

function varint(n) {
  const out = [];
  while (n > 0x7f) {
    out.push((n & 0x7f) | 0x80);
    n >>>= 7;
  }
  out.push(n);
  return out;
}

/** protobuf encoding of string fields: tag (number << 3 | 2), length, UTF-8 bytes. */
export function encode(message) {
  const parts = [];
  for (const [number, name] of FIELDS) {
    const value = message[name];
    if (!value) continue; // proto3 skips empty strings
    const bytes = [...encoder.encode(value)];
    parts.push({ number, name, value, bytes: [(number << 3) | 2, ...varint(bytes.length), ...bytes] });
  }
  return parts;
}

const hex = (bytes) => bytes.map((b) => b.toString(16).padStart(2, "0")).join(" ");

export function renderCompare(t) {
  const message = {
    transaction_id: "tx-1",
    user_id: "u-1",
    card_last4: "4242",
    amount: "10.00",
    currency: "EUR",
    merchant_name: "Shop",
    merchant_category: "GROCERIES",
  };
  const root = document.createElement("div");
  root.className = "compare";
  root.innerHTML = `<h2>${t("cmp.title")}</h2><p>${t("cmp.lead")}</p>`;

  const inputs = document.createElement("div");
  inputs.className = "compare__inputs sandbox";
  const letters = document.createElement("div");
  letters.className = "compare__letters";

  const draw = () => {
    const json = JSON.stringify(message, null, 1);
    const jsonBytes = encoder.encode(JSON.stringify(message)).length;
    const parts = encode(message);
    const protoBytes = parts.reduce((n, p) => n + p.bytes.length, 0);
    letters.innerHTML = `
      <section class="compare__letter">
        <h3>${t("cmp.json")}</h3>
        <p class="compare__size"><span data-testid="compare-json-bytes">${jsonBytes}</span> <small>${t("cmp.bytes")}</small></p>
        <pre data-testid="compare-json"></pre>
      </section>
      <section class="compare__letter">
        <h3>${t("cmp.proto")}</h3>
        <p class="compare__size"><span data-testid="compare-proto-bytes">${protoBytes}</span> <small>${t("cmp.bytes")}</small></p>
        <pre data-testid="compare-proto"></pre>
      </section>
      <section class="compare__letter">
        <h3>${t("cmp.fields")}</h3>
        <ul class="compare__fields" data-testid="compare-fields"></ul>
      </section>`;
    letters.querySelector("[data-testid=compare-json]").textContent = json;
    letters.querySelector("[data-testid=compare-proto]").textContent = parts
      .map((p) => `${hex(p.bytes.slice(0, 2))} | ${hex(p.bytes.slice(2))}  → "${p.value}"`)
      .join("\n");
    const ul = letters.querySelector("[data-testid=compare-fields]");
    for (const p of parts) {
      const li = document.createElement("li");
      li.innerHTML = `<b>${p.number}</b> ${p.name} — ${t("cmp.field")} ${p.number}: <span></span>`;
      li.querySelector("span").textContent = p.value;
      ul.append(li);
    }
  };

  for (const [name, testid] of [["amount", "compare-amount"], ["merchant_name", "compare-merchant"], ["merchant_category", "compare-category"]]) {
    const label = document.createElement("label");
    label.className = "field";
    label.innerHTML = `<span class="field__label">${name}</span>`;
    const input = document.createElement("input");
    input.type = "text";
    input.value = message[name];
    input.dataset.testid = testid;
    input.addEventListener("input", () => {
      message[name] = input.value;
      draw();
    });
    label.append(input);
    inputs.append(label);
  }
  root.append(inputs, letters);
  draw();
  return root;
}
