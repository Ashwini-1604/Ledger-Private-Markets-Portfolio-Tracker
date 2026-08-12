import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import Layout from "../components/Layout";
import AddInvestmentModal from "../components/AddInvestmentModal";
import { fmtCurrency, fmtMultiple, fmtPercent } from "../utils/format";

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [investments, setInvestments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);
  const navigate = useNavigate();

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const [summaryRes, investmentsRes] = await Promise.all([
        api.get("/portfolio/summary"),
        api.get("/investments"),
      ]);
      setSummary(summaryRes.data);
      setInvestments(investmentsRes.data);
    } catch (err) {
      setError("Could not load your portfolio. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadData(); }, []);

  function handleCreated(newInvestment) {
    setShowAddModal(false);
    navigate(`/investments/${newInvestment.id}`);
  }

  return (
    <Layout>
      {error && <div className="form-error">{error}</div>}

      {summary && (
        <div className="summary-grid">
          <div className="summary-cell">
            <div className="summary-label">Total Committed</div>
            <div className="summary-value">{fmtCurrency(summary.total_committed)}</div>
          </div>
          <div className="summary-cell">
            <div className="summary-label">Paid-In Capital</div>
            <div className="summary-value">{fmtCurrency(summary.total_paid_in)}</div>
          </div>
          <div className="summary-cell">
            <div className="summary-label">Distributions</div>
            <div className="summary-value figure-positive">{fmtCurrency(summary.total_distributions)}</div>
          </div>
          <div className="summary-cell">
            <div className="summary-label">Current NAV</div>
            <div className="summary-value">{fmtCurrency(summary.total_nav)}</div>
          </div>
          <div className="summary-cell">
            <div className="summary-label">Portfolio TVPI</div>
            <div className="summary-value small">{fmtMultiple(summary.portfolio_tvpi)}</div>
          </div>
          <div className="summary-cell">
            <div className="summary-label">Portfolio IRR</div>
            <div className={`summary-value small ${summary.portfolio_irr >= 0 ? "figure-positive" : "figure-negative"}`}>
              {fmtPercent(summary.portfolio_irr)}
            </div>
          </div>
        </div>
      )}

      <div className="section-header">
        <h2>Fund positions ({investments.length})</h2>
        <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>+ Add fund</button>
      </div>

      {loading ? (
        <div className="loading-text">Loading your portfolio…</div>
      ) : investments.length === 0 ? (
        <div className="empty-state">
          <h3>No fund commitments yet</h3>
          <p>Add your first fund to start tracking capital calls, distributions, and returns.</p>
          <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={() => setShowAddModal(true)}>
            + Add fund
          </button>
        </div>
      ) : (
        <table className="investment-table">
          <thead>
            <tr>
              <th>Fund</th>
              <th>Vintage</th>
              <th className="num">Committed</th>
              <th className="num">NAV</th>
              <th className="num">TVPI</th>
              <th className="num">IRR</th>
            </tr>
          </thead>
          <tbody>
            {investments.map((inv) => (
              <InvestmentRow key={inv.id} investment={inv} onClick={() => navigate(`/investments/${inv.id}`)} />
            ))}
          </tbody>
        </table>
      )}

      {showAddModal && (
        <AddInvestmentModal onClose={() => setShowAddModal(false)} onCreated={handleCreated} />
      )}
    </Layout>
  );
}

function InvestmentRow({ investment, onClick }) {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    api.get(`/investments/${investment.id}/metrics`).then((res) => setMetrics(res.data)).catch(() => {});
  }, [investment.id]);

  return (
    <tr className="investment-row" onClick={onClick}>
      <td>
        <div className="fund-name">{investment.fund_name}</div>
        <span className="asset-class-tag">{investment.asset_class}</span>
      </td>
      <td>{investment.vintage_year || "—"}</td>
      <td className="num">{fmtCurrency(investment.commitment_amount)}</td>
      <td className="num">{fmtCurrency(investment.current_nav)}</td>
      <td className="num">{metrics ? fmtMultiple(metrics.tvpi) : "…"}</td>
      <td className={`num ${metrics?.irr >= 0 ? "figure-positive" : metrics?.irr < 0 ? "figure-negative" : ""}`}>
        {metrics ? fmtPercent(metrics.irr) : "…"}
      </td>
    </tr>
  );
}
