import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import api from "../api/client";
import Layout from "../components/Layout";
import { fmtCurrency, fmtMultiple, fmtPercent, fmtDate } from "../utils/format";

export default function InvestmentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [investment, setInvestment] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [csvMsg, setCsvMsg] = useState("");

  const [cfType, setCfType] = useState("capital_call");
  const [cfAmount, setCfAmount] = useState("");
  const [cfDate, setCfDate] = useState("");
  const [cfNote, setCfNote] = useState("");
  const [addingCf, setAddingCf] = useState(false);

  const [editingNav, setEditingNav] = useState(false);
  const [navValue, setNavValue] = useState("");

  async function loadAll() {
    setLoading(true);
    setError("");
    try {
      const [invRes, metricsRes, timelineRes] = await Promise.all([
        api.get(`/investments/${id}`),
        api.get(`/investments/${id}/metrics`),
        api.get(`/investments/${id}/cashflow-timeline`),
      ]);
      setInvestment(invRes.data);
      setMetrics(metricsRes.data);
      setTimeline(timelineRes.data);
      setNavValue(invRes.data.current_nav);
    } catch (err) {
      setError("Could not load this investment.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadAll(); }, [id]);

  async function handleAddCashflow(e) {
    e.preventDefault();
    setAddingCf(true);
    try {
      await api.post(`/investments/${id}/cashflows`, {
        type: cfType, amount: Number(cfAmount), date: cfDate, note: cfNote || null,
      });
      setCfAmount(""); setCfDate(""); setCfNote("");
      await loadAll();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not add cashflow.");
    } finally {
      setAddingCf(false);
    }
  }

  async function handleDeleteCashflow(cashflowId) {
    if (!confirm("Delete this cashflow?")) return;
    await api.delete(`/investments/${id}/cashflows/${cashflowId}`);
    await loadAll();
  }

  async function handleUpdateNav() {
    try {
      await api.patch(`/investments/${id}`, { current_nav: Number(navValue), nav_as_of: new Date().toISOString().slice(0, 10) });
      setEditingNav(false);
      await loadAll();
    } catch (err) {
      setError("Could not update NAV.");
    }
  }

  async function handleDeleteInvestment() {
    if (!confirm(`Delete "${investment.fund_name}"? This removes all its cashflow history too.`)) return;
    await api.delete(`/investments/${id}`);
    navigate("/");
  }

  async function handleCsvUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    setCsvMsg("");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await api.post(`/investments/${id}/cashflows/import-csv`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setCsvMsg(`Imported ${res.data.length} cashflow(s).`);
      await loadAll();
    } catch (err) {
      setCsvMsg(err.response?.data?.detail || "CSV import failed.");
    } finally {
      e.target.value = "";
    }
  }

  if (loading) return <Layout><div className="loading-text">Loading…</div></Layout>;
  if (error && !investment) return <Layout><div className="error-text">{error}</div></Layout>;
  if (!investment) return null;

  const allCashflows = [...investment.cashflows].sort((a, b) => new Date(b.date) - new Date(a.date));

  return (
    <Layout>
      <Link to="/" className="back-link">← Back to portfolio</Link>

      <div className="detail-header">
        <div>
          <h1>{investment.fund_name}</h1>
          <span className="asset-class-tag" style={{ marginTop: 8, display: "inline-block" }}>
            {investment.asset_class}{investment.vintage_year ? ` · ${investment.vintage_year} vintage` : ""}
          </span>
        </div>
        <div className="top-toolbar">
          <button className="btn btn-danger" onClick={handleDeleteInvestment}>Delete fund</button>
        </div>
      </div>

      {error && <div className="form-error">{error}</div>}

      {metrics && (
        <div className="metrics-row">
          <MetricBox label="Committed" value={fmtCurrency(investment.commitment_amount)} />
          <MetricBox label="Paid-In" value={fmtCurrency(metrics.paid_in)} />
          <MetricBox label="Distributed" value={fmtCurrency(metrics.distributions)} positive />
          <MetricBox label="DPI" value={fmtMultiple(metrics.dpi)} />
          <MetricBox label="TVPI / MOIC" value={fmtMultiple(metrics.tvpi)} />
          <MetricBox label="IRR" value={fmtPercent(metrics.irr)} colorByValue={metrics.irr} />
        </div>
      )}

      <div className="chart-panel">
        <div className="section-header" style={{ border: "none", marginBottom: 20 }}>
          <h2>Cashflow timeline</h2>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {editingNav ? (
              <>
                <input type="number" value={navValue} onChange={(e) => setNavValue(e.target.value)}
                  style={{ width: 120, background: "var(--bg)", border: "1px solid var(--border)", color: "var(--text)", padding: "6px 8px", borderRadius: 4 }} />
                <button className="btn btn-primary" onClick={handleUpdateNav}>Save NAV</button>
                <button className="btn btn-ghost" onClick={() => setEditingNav(false)}>Cancel</button>
              </>
            ) : (
              <button className="btn btn-ghost" onClick={() => setEditingNav(true)}>Update current NAV</button>
            )}
          </div>
        </div>

        {timeline.length > 0 ? (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={timeline} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <CartesianGrid stroke="#2A2F3A" strokeDasharray="3 3" />
              <XAxis dataKey="date" tickFormatter={fmtDate} stroke="#565D6B" fontSize={12} />
              <YAxis stroke="#565D6B" fontSize={12} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
              <Tooltip
                formatter={(value) => fmtCurrency(value)}
                labelFormatter={fmtDate}
                contentStyle={{ background: "#1A1E26", border: "1px solid #2A2F3A", borderRadius: 4 }}
              />
              <Legend />
              <Line type="stepAfter" dataKey="cumulative_paid_in" name="Paid-In" stroke="#C0564F" strokeWidth={2} dot={false} />
              <Line type="stepAfter" dataKey="cumulative_distributions" name="Distributions" stroke="#3FA772" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="loading-text">Add cashflows below to see the timeline.</div>
        )}
      </div>

      <div className="section-header">
        <h2>Cashflow ledger</h2>
      </div>

      <div className="ledger">
        {allCashflows.length === 0 ? (
          <div className="empty-state">No cashflows recorded yet.</div>
        ) : (
          allCashflows.map((cf) => (
            <div className="ledger-row" key={cf.id}>
              <div className="lr-left">
                <span className={`lr-type-dot ${cf.type === "capital_call" ? "dot-call" : "dot-dist"}`} />
                <div>
                  <div>{cf.type === "capital_call" ? "Capital call" : "Distribution"}</div>
                  <div className="lr-date">{fmtDate(cf.date)}{cf.note ? ` · ${cf.note}` : ""}</div>
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                <span className={`lr-amount ${cf.type === "capital_call" ? "figure-negative" : "figure-positive"}`}>
                  {cf.type === "capital_call" ? "-" : "+"}{fmtCurrency(cf.amount)}
                </span>
                <button className="btn btn-ghost" onClick={() => handleDeleteCashflow(cf.id)}>✕</button>
              </div>
            </div>
          ))
        )}

        <form className="inline-form" onSubmit={handleAddCashflow}>
          <div className="field">
            <label>Type</label>
            <select value={cfType} onChange={(e) => setCfType(e.target.value)}>
              <option value="capital_call">Capital call</option>
              <option value="distribution">Distribution</option>
            </select>
          </div>
          <div className="field">
            <label>Amount (USD)</label>
            <input type="number" required min="0" step="0.01" value={cfAmount}
              onChange={(e) => setCfAmount(e.target.value)} placeholder="50000" style={{ width: 140 }} />
          </div>
          <div className="field">
            <label>Date</label>
            <input type="date" required value={cfDate} onChange={(e) => setCfDate(e.target.value)} />
          </div>
          <div className="field">
            <label>Note (optional)</label>
            <input value={cfNote} onChange={(e) => setCfNote(e.target.value)} placeholder="e.g. Capital call #3" />
          </div>
          <button className="btn btn-primary" type="submit" disabled={addingCf}>
            {addingCf ? "Adding…" : "Add cashflow"}
          </button>
          <button type="button" className="btn" onClick={() => fileInputRef.current?.click()}>
            Import CSV
          </button>
          <input ref={fileInputRef} type="file" accept=".csv" onChange={handleCsvUpload} style={{ display: "none" }} />
        </form>
        {csvMsg && <div className="csv-hint" style={{ padding: "0 20px 14px" }}>{csvMsg}</div>}
      </div>
      <div className="csv-hint">
        CSV format: columns <code>type,amount,date,note</code> — type is <code>capital_call</code> or <code>distribution</code>, date as <code>YYYY-MM-DD</code>.
      </div>
    </Layout>
  );
}

function MetricBox({ label, value, positive, colorByValue }) {
  let colorClass = "";
  if (positive) colorClass = "figure-positive";
  if (colorByValue !== undefined && colorByValue !== null) {
    colorClass = colorByValue >= 0 ? "figure-positive" : "figure-negative";
  }
  return (
    <div className="metric-box">
      <div className="summary-label">{label}</div>
      <div className={`metric-value ${colorClass}`}>{value}</div>
    </div>
  );
}
