import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";

import { request, type Card, type IssuedCard } from "../api";
import { formatMoney } from "../money";
import ErrorBanner from "./ErrorBanner";

function groupPan(pan: string): string {
  return pan.replace(/(\d{4})(?=\d)/g, "$1 ");
}

export default function Cards({ accountId, currency }: { accountId: string; currency: string }) {
  const [cards, setCards] = useState<Card[]>([]);
  const [limit, setLimit] = useState("");
  const [issued, setIssued] = useState<IssuedCard | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);

  const load = useCallback(() => {
    request<Card[]>("GET", `/accounts/${accountId}/cards`).then(setCards).catch(setError);
  }, [accountId]);
  useEffect(load, [load]);

  useEffect(() => {
    if (issued) dialog.current?.showModal();
  }, [issued]);

  async function issue(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const body = limit ? { daily_limit: limit } : {};
      setIssued(await request<IssuedCard>("POST", `/accounts/${accountId}/cards`, body));
      setLimit("");
      load();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }

  async function block(card: Card) {
    setError(null);
    try {
      await request("POST", `/cards/${card.id}/block`);
      load();
    } catch (e) {
      setError(e);
    }
  }

  function closeDialog() {
    dialog.current?.close();
    setIssued(null); // the full number and CVV are forgotten as soon as the dialog closes
  }

  return (
    <section className="wallet" aria-label="Cards">
      <h2>Cards</h2>
      {cards.length === 0 && <p className="muted">No cards yet. Issue a virtual card to pay with it.</p>}
      {cards.map((card) => (
        <div key={card.id} data-testid="card-row">
          <div className={`paycard ${card.status.toLowerCase()}`}>
            <div className="chip" aria-hidden="true" />
            <span className="pan" data-testid="card-masked">{card.masked_pan}</span>
            <div className="meta">
              <span>Valid thru {card.expiry}</span>
              <span className="state" data-testid="card-status">{card.status}</span>
            </div>
          </div>
          <div className="card-actions">
            <span className="muted">Daily limit {formatMoney(card.daily_limit, currency)}</span>
            {card.status === "ACTIVE" && (
              <button className="quiet" data-testid="card-block" onClick={() => block(card)}>
                Block card
              </button>
            )}
          </div>
        </div>
      ))}
      <form className="form" onSubmit={issue}>
        <label>
          Daily limit (optional, default 1000.00)
          <input data-testid="issue-limit" inputMode="decimal" placeholder="1000.00"
            value={limit} onChange={(e) => setLimit(e.target.value)} />
        </label>
        <button data-testid="issue-submit" type="submit" disabled={busy}>Issue virtual card</button>
      </form>
      <ErrorBanner error={error} />

      <dialog ref={dialog} onCancel={closeDialog} aria-labelledby="issued-title">
        {issued && (
          <div className="form">
            <h2 id="issued-title">Your new card</h2>
            <div className="paycard">
              <div className="chip" aria-hidden="true" />
              <span className="pan" data-testid="issued-pan">{groupPan(issued.pan)}</span>
              <div className="meta">
                <span>Valid thru {issued.expiry}</span>
                <span>CVV <b data-testid="issued-cvv">{issued.cvv}</b></span>
              </div>
            </div>
            <p className="notice">
              Write down the card number and CVV now. They are shown only once and cannot be
              recovered later.
            </p>
            <button data-testid="issued-close" onClick={closeDialog}>I have saved them</button>
          </div>
        )}
      </dialog>
    </section>
  );
}
