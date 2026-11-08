import { useState, type FormEvent } from "react";
import { Link, Navigate } from "react-router-dom";

import { useAuth } from "../auth";
import ErrorBanner from "../components/ErrorBanner";

export default function Login() {
  const { user, login, sessionMessage } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth">
      <p className="wordmark">Card Wallet</p>
      <h1>Log in</h1>
      {sessionMessage && (
        <div className="notice" data-testid="session-message">{sessionMessage}</div>
      )}
      <ErrorBanner error={error} />
      <form className="form" onSubmit={submit}>
        <label>
          Email
          <input data-testid="login-email" type="email" autoComplete="email" required
            value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label>
          Password
          <input data-testid="login-password" type="password" autoComplete="current-password" required
            value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        <button data-testid="login-submit" type="submit" disabled={busy}>Log in</button>
      </form>
      <p className="muted">
        No account yet? <Link to="/register">Create one</Link>
      </p>
    </main>
  );
}
