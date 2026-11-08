import { useState, type FormEvent } from "react";

import { request } from "../api";
import ErrorBanner from "./ErrorBanner";

export default function TopUpForm({ accountId, onDone }: { accountId: string; onDone(): void }) {
  const [amount, setAmount] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await request("POST", `/accounts/${accountId}/top-up`, { amount });
      setAmount("");
      onDone();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="form">
      <form className="form inline" onSubmit={submit}>
        <label>
          Amount
          <input data-testid="topup-amount" inputMode="decimal" placeholder="100.00" required
            value={amount} onChange={(e) => setAmount(e.target.value)} />
        </label>
        <button data-testid="topup-submit" type="submit" disabled={busy}>Top up</button>
      </form>
      <ErrorBanner error={error} />
    </div>
  );
}
