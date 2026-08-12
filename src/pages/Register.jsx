import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    try {
      await register(email, password);
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not create account.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <div className="brand" style={{ marginBottom: 24 }}>
          <span className="brand-mark">Ledger</span>
          <span className="brand-sub">Portfolio Tracker</span>
        </div>
        <h1 className="auth-title">Create your account</h1>
        <p className="auth-subtitle">Start tracking fund commitments and returns.</p>

        {error && <div className="form-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input id="email" type="email" required value={email}
              onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input id="password" type="password" required value={password}
              onChange={(e) => setPassword(e.target.value)} placeholder="At least 8 characters" />
          </div>
          <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: "100%" }}>
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>

        <div className="auth-switch">
          Already have an account? <Link to="/login">Sign in</Link>
        </div>
      </div>
    </div>
  );
}
