import { useEffect, useState } from "react";

import { request, type Statement as StatementData } from "../api";
import { formatMoney } from "../money";
import ErrorBanner from "./ErrorBanner";

const PAGE = 10;
const TYPE_LABEL = { TOP_UP: "Top-up", PAYMENT: "Payment", COMMISSION: "Commission" } as const;

export default function Statement({ accountId, version }: { accountId: string; version: number }) {
  const [data, setData] = useState<StatementData | null>(null);
  const [status, setStatus] = useState("");
  const [type, setType] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    const params = new URLSearchParams({ limit: String(PAGE), offset: String(offset) });
    if (status) params.set("status", status);
    if (type) params.set("type", type);
    if (dateFrom) params.set("date_from", dateFrom);
    if (dateTo) params.set("date_to", dateTo);
    setError(null);
    request<StatementData>("GET", `/accounts/${accountId}/transactions?${params}`)
      .then(setData)
      .catch(setError);
  }, [accountId, version, status, type, dateFrom, dateTo, offset]);

  function filter(setter: (v: string) => void) {
    return (value: string) => {
      setter(value);
      setOffset(0);
    };
  }

  return (
    <section className="form" aria-label="Statement">
      <div className="page-head">
        <h2>Statement</h2>
        {data && <span className="muted" data-testid="statement-total">{data.total} operations</span>}
      </div>
      <div className="form inline">
        <label>
          Status
          <select data-testid="filter-status" value={status} onChange={(e) => filter(setStatus)(e.target.value)}>
            <option value="">All</option>
            <option value="APPROVED">Approved</option>
            <option value="DECLINED">Declined</option>
          </select>
        </label>
        <label>
          Type
          <select data-testid="filter-type" value={type} onChange={(e) => filter(setType)(e.target.value)}>
            <option value="">All</option>
            <option value="TOP_UP">Top-up</option>
            <option value="PAYMENT">Payment</option>
            <option value="COMMISSION">Commission</option>
          </select>
        </label>
        <label>
          From
          <input type="date" data-testid="filter-from" value={dateFrom}
            onChange={(e) => filter(setDateFrom)(e.target.value)} />
        </label>
        <label>
          To
          <input type="date" data-testid="filter-to" value={dateTo}
            onChange={(e) => filter(setDateTo)(e.target.value)} />
        </label>
      </div>
      <ErrorBanner error={error} />
      <div className="ledger-wrap">
        <table className="ledger">
          <thead>
            <tr>
              <th>Date (UTC)</th>
              <th>Operation</th>
              <th>Status</th>
              <th className="amount">Amount</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((tx) => (
              <tr key={tx.id} data-testid="statement-row">
                <td className="nowrap">{tx.created_at.slice(0, 16).replace("T", " ")}</td>
                <td>
                  <span data-testid="tx-type">{TYPE_LABEL[tx.type]}</span>
                  {tx.merchant_name && <span className="muted"> · {tx.merchant_name}</span>}
                  {tx.card_last4 && <span className="muted"> · card {tx.card_last4}</span>}
                </td>
                <td className={`status-${tx.status}`}>
                  <span data-testid="tx-status">{tx.status === "APPROVED" ? "Approved" : "Declined"}</span>
                  {tx.decline_reason && <div className="muted" data-testid="tx-reason">{tx.decline_reason}</div>}
                </td>
                <td className={`amount${tx.status === "DECLINED" ? " muted" : ""}`} data-testid="tx-amount">
                  {/* a declined payment moved no money, so it gets no minus sign */}
                  {tx.type !== "TOP_UP" && tx.status === "APPROVED" ? "−" : ""}
                  {formatMoney(tx.amount, tx.currency)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data && data.total > PAGE && (
        <div className="card-actions">
          <button className="quiet" data-testid="statement-prev" disabled={offset === 0}
            onClick={() => setOffset(Math.max(0, offset - PAGE))}>Newer</button>
          <span className="muted">
            {offset + 1}–{Math.min(offset + PAGE, data.total)} of {data.total}
          </span>
          <button className="quiet" data-testid="statement-next" disabled={offset + PAGE >= data.total}
            onClick={() => setOffset(offset + PAGE)}>Older</button>
        </div>
      )}
    </section>
  );
}
