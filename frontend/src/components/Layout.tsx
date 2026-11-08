import { Link, Navigate, Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../auth";

/** Header for signed-in pages; sends visitors without a session to the login page. */
export default function Layout() {
  const { user, loading, logout } = useAuth();
  const navigate = useNavigate();

  if (loading) return <p className="page muted">Loading…</p>;
  if (!user) return <Navigate to="/login" replace />;

  return (
    <>
      <header className="topbar">
        <Link to="/" className="brand">Card Wallet</Link>
        <nav>
          <Link to="/pay" data-testid="nav-pay">Pay with card</Link>
          <span data-testid="user-name">{user.name}</span>
          <button
            className="quiet"
            data-testid="logout-button"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            Log out
          </button>
        </nav>
      </header>
      <Outlet />
    </>
  );
}
