import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Layout({ children }) {
  const { logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" style={{ textDecoration: "none" }}>
          <div className="brand">
            <span className="brand-mark">Ledger</span>
            <span className="brand-sub">Portfolio Tracker</span>
          </div>
        </Link>
        <div className="topbar-actions">
          <button className="btn btn-ghost" onClick={handleLogout}>Sign out</button>
        </div>
      </header>
      <main className="main-content">{children}</main>
    </div>
  );
}
