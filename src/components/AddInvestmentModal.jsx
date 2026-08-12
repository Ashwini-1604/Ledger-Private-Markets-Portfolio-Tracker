import { useState } from "react";
import api from "../api/client";

const ASSET_CLASSES = ["Private Equity", "Venture Capital", "Real Estate", "Private Credit", "Infrastructure"];

export default function AddInvestmentModal({ onClose, onCreated }) {
  const [form, setForm] = useState({
    fund_name: "",
    asset_class: "Private Equity",
    vintage_year: new Date().getFullYear(),
    commitment_amount: "",
    current_nav: "",
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      const res = await api.post("/investments", {
        fund_name: form.fund_name,
        asset_class: form.asset_class,
        vintage_year: form.vintage_year ? Number(form.vintage_year) : null,
        commitment_amount: Number(form.commitment_amount),
        current_nav: form.current_nav ? Number(form.current_nav) : 0,
      });
      onCreated(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not create investment.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <h3>Add a fund commitment</h3>
        {error && <div className="form-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Fund name</label>
            <input required value={form.fund_name}
              onChange={(e) => update("fund_name", e.target.value)}
              placeholder="e.g. Northbridge Real Estate Fund IV" />
          </div>
          <div className="field">
            <label>Asset class</label>
            <select value={form.asset_class} onChange={(e) => update("asset_class", e.target.value)}>
              {ASSET_CLASSES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="field">
            <label>Vintage year</label>
            <input type="number" value={form.vintage_year}
              onChange={(e) => update("vintage_year", e.target.value)} />
          </div>
          <div className="field">
            <label>Commitment amount (USD)</label>
            <input type="number" required min="0" step="0.01" value={form.commitment_amount}
              onChange={(e) => update("commitment_amount", e.target.value)} placeholder="1000000" />
          </div>
          <div className="field">
            <label>Current NAV (optional — you can update this later)</label>
            <input type="number" min="0" step="0.01" value={form.current_nav}
              onChange={(e) => update("current_nav", e.target.value)} placeholder="0" />
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Adding…" : "Add fund"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
