import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ApiError, request, type Account as AccountData } from "../api";
import Cards from "../components/Cards";
import ErrorBanner from "../components/ErrorBanner";
import Statement from "../components/Statement";
import TopUpForm from "../components/TopUpForm";
import { formatMoney } from "../money";
import NotFound from "./NotFound";

export default function Account() {
  const { id = "" } = useParams();
  const [account, setAccount] = useState<AccountData | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [version, setVersion] = useState(0);

  const load = useCallback(() => {
    request<AccountData>("GET", `/accounts/${id}`).then(setAccount).catch(setError);
  }, [id]);
  useEffect(load, [load]);

  if (error instanceof ApiError && (error.status === 404 || error.status === 422)) return <NotFound />;
  if (error) return <main className="page"><ErrorBanner error={error} /></main>;
  if (!account) return <p className="page muted">Loading…</p>;

  return (
    <main className="page">
      <Link to="/">All accounts</Link>
      <div className="split">
        <div className="form" style={{ gap: "2rem" }}>
          <section className="form">
            <h1>{account.currency} account</h1>
            <p className="balance-hero" data-testid="account-balance">
              {formatMoney(account.balance, account.currency)}
            </p>
            <TopUpForm accountId={account.id} onDone={() => { load(); setVersion((v) => v + 1); }} />
          </section>
          <Statement accountId={account.id} version={version} />
        </div>
        <Cards accountId={account.id} currency={account.currency} />
      </div>
    </main>
  );
}
