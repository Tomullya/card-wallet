import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { request, type Account, type Card, type Payment } from "../api";
import ErrorBanner from "../components/ErrorBanner";
import { formatMoney } from "../money";

const CATEGORIES = ["GROCERIES", "ELECTRONICS", "TRAVEL", "RESTAURANTS", "GAMBLING", "OTHER"];

interface CardOption {
  card: Card;
  account: Account;
}

/** A simulated merchant checkout: pay with one of your active cards. */
export default function Pay() {
  const [options, setOptions] = useState<CardOption[] | null>(null);
  const [cardId, setCardId] = useState("");
  const [cvv, setCvv] = useState("");
  const [amount, setAmount] = useState("");
  const [merchant, setMerchant] = useState("");
  const [category, setCategory] = useState("GROCERIES");
  const [result, setResult] = useState<Payment | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  // One Idempotency-Key per payment attempt: reused on a retry of the same values,
  // renewed when anything changes. Together with inFlight this makes a double click safe.
  const idempotencyKey = useRef<string | null>(null);
  const inFlight = useRef(false);

  useEffect(() => {
    (async () => {
      const accounts = await request<Account[]>("GET", "/accounts");
      const lists = await Promise.all(
        accounts.map((a) => request<Card[]>("GET", `/accounts/${a.id}/cards`)),
      );
      const active = lists.flatMap((cards, i) =>
        cards.filter((c) => c.status === "ACTIVE").map((card) => ({ card, account: accounts[i] })),
      );
      setOptions(active);
      if (active.length > 0) setCardId(active[0].card.id);
    })().catch(setError);
  }, []);

  function edit<T>(setter: (v: T) => void) {
    return (value: T) => {
      setter(value);
      idempotencyKey.current = null;
      setResult(null);
    };
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    setError(null);
    idempotencyKey.current ??= crypto.randomUUID();
    try {
      const payment = await request<Payment>(
        "POST",
        "/payments",
        { card_id: cardId, cvv, amount, merchant_name: merchant, merchant_category: category },
        { "Idempotency-Key": idempotencyKey.current },
      );
      setResult(payment);
    } catch (e) {
      setError(e);
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }

  const selected = options?.find((o) => o.card.id === cardId);

  return (
    <main className="page">
      <h1>Pay with card</h1>
      {options === null ? (
        <p className="muted">Loading…</p>
      ) : options.length === 0 ? (
        <div className="panel" data-testid="no-cards">
          <h2>No active cards</h2>
          <p className="muted">Open an account and issue a card first.</p>
        </div>
      ) : (
        <div className="split">
          <form className="form panel" onSubmit={submit}>
            <label>
              Card
              <select data-testid="pay-card" value={cardId} onChange={(e) => edit(setCardId)(e.target.value)}>
                {options.map(({ card, account }) => (
                  <option key={card.id} value={card.id}>
                    {card.masked_pan} · {account.currency}
                  </option>
                ))}
              </select>
            </label>
            <label>
              CVV
              <input data-testid="pay-cvv" inputMode="numeric" maxLength={3} autoComplete="cc-csc"
                value={cvv} onChange={(e) => edit(setCvv)(e.target.value)} />
            </label>
            <label>
              Amount{selected ? ` (${selected.account.currency})` : ""}
              <input data-testid="pay-amount" inputMode="decimal" placeholder="10.00"
                value={amount} onChange={(e) => edit(setAmount)(e.target.value)} />
            </label>
            <label>
              Shop
              <input data-testid="pay-merchant" placeholder="Coffee Shop"
                value={merchant} onChange={(e) => edit(setMerchant)(e.target.value)} />
            </label>
            <label>
              Category
              <select data-testid="pay-category" value={category}
                onChange={(e) => edit(setCategory)(e.target.value)}>
                {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
              </select>
            </label>
            <button data-testid="pay-submit" type="submit" disabled={busy}>
              {busy ? "Paying…" : "Pay"}
            </button>
            <ErrorBanner error={error} />
          </form>

          {result && selected && (
            <section className="receipt" data-testid="pay-result" aria-live="polite">
              <span className={`verdict status-${result.status}`} data-testid="pay-status">{result.status}</span>
              {result.decline_reason && <span data-testid="pay-reason">{result.decline_reason}</span>}
              <div className="row"><span>Shop</span><span>{merchant}</span></div>
              <div className="row"><span>Card</span><span>{selected.card.masked_pan.slice(-4)}</span></div>
              <div className="row"><span>Amount</span><span>{formatMoney(result.amount, result.currency)}</span></div>
              <div className="row">
                <span>Commission</span>
                <span data-testid="pay-commission">
                  {result.commission ? formatMoney(result.commission, result.currency) : "none"}
                </span>
              </div>
              <Link to={`/accounts/${selected.account.id}`} data-testid="pay-account-link">
                See the account
              </Link>
            </section>
          )}
        </div>
      )}
    </main>
  );
}
