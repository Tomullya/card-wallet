import { useState, type FormEvent } from "react";
import { Link, Navigate } from "react-router-dom";

import { useAuth } from "../auth";
import ErrorBanner from "../components/ErrorBanner";

export default function Register() {
  const { user, register } = useAuth();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await register(email, name, password);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth">
      <p className="wordmark">Card Wallet</p>
      <h1>Create your wallet</h1>
      <ErrorBanner error={error} />
      <form className="form" onSubmit={submit} noValidate>
        <label>
          Email
          <input data-testid="register-email" type="email" autoComplete="email"
            value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label>
          Name
          <input data-testid="register-name" autoComplete="name"
            value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <label>
          Password
          <input data-testid="register-password" type="password" autoComplete="new-password"
            value={password} onChange={(e) => setPassword(e.target.value)} />
          <span className="muted">At least 8 characters, with a letter and a digit</span>
        </label>
        <button data-testid="register-submit" type="submit" disabled={busy}>Create wallet</button>
      </form>
      <p className="muted">
        Already registered? <Link to="/login">Log in</Link>
      </p>
    </main>
  );
}
