export default function Login() {
  return (
    <main className="auth">
      <h1>Log in</h1>
      <form className="form">
        <label>
          Email
          <input data-testid="login-email" type="email" autoComplete="email" />
        </label>
        <label>
          Password
          <input data-testid="login-password" type="password" autoComplete="current-password" />
        </label>
        <button data-testid="login-submit" type="submit">Log in</button>
      </form>
    </main>
  );
}
