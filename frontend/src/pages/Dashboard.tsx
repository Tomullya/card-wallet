import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { request, type Account } from "../api";
import ErrorBanner from "../components/ErrorBanner";
import { formatMoney } from "../money";

const CURRENCIES = ["EUR", "USD", "PLN"];

export default function Dashboard() {
  const [accounts, setAccounts] = useState<Account[] | null>(null);
  const [currency, setCurrency] = useState("EUR");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    request<Account[]>("GET", "/accounts").then(setAccounts).catch(setError);
  }, []);
  useEffect(load, [load]);

  async function open(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await request<Account>("POST", "/accounts", { currency });
      load();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page">
      <div className="page-head">
        <h1>Your accounts</h1>
        <form className="form inline" onSubmit={open}>
          <label>
            Currency
            <select data-testid="open-account-currency" value={currency}
              onChange={(e) => setCurrency(e.target.value)}>
              {CURRENCIES.map((c) => <option key={c}>{c}</option>)}
            </select>
          </label>
          <button data-testid="open-account-submit" type="submit" disabled={busy}>Open account</button>
        </form>
      </div>
      <ErrorBanner error={error} />
      {accounts === null ? (
        <p className="muted">Loading…</p>
      ) : accounts.length === 0 ? (
        <div className="panel" data-testid="empty-accounts">
          <h2>No accounts yet</h2>
          <p className="muted">Open an account in EUR, USD or PLN to top it up and issue cards.</p>
        </div>
      ) : (
        <section aria-label="Accounts">
          {accounts.map((a) => (
            <Link key={a.id} to={`/accounts/${a.id}`} className="account-row"
              data-testid={`account-card-${a.currency}`}>
              <span className="currency">{a.currency} account</span>
              <span className="balance" data-testid={`account-balance-${a.currency}`}>
                {formatMoney(a.balance, a.currency)}
              </span>
            </Link>
          ))}
        </section>
      )}
    </main>
  );
}
