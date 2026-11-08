import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <main className="page" data-testid="not-found">
      <h1>Not found</h1>
      <p className="muted">This page does not exist or belongs to someone else.</p>
      <Link to="/">Back to your accounts</Link>
    </main>
  );
}
