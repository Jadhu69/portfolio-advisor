/**
 * App.jsx
 * =======
 * Portfolio Advisor frontend. Collects investor inputs, calls the
 * FastAPI backend's POST /api/advise endpoint, and renders the
 * risk assessment + asset allocation results.
 *
 * Expects the FastAPI backend running at REACT_APP_API_BASE
 * (defaults to http://localhost:8000).
 */

import React, { useState } from "react";
import "./App.css";

const API_BASE =
  import.meta.env.VITE_API_BASE ||
  "https://portfolio-advisor-oo13.onrender.com";

const GOALS = [
  { value: "", label: "Select goal" },
  { value: "retirement", label: "Retirement" },
  { value: "house", label: "Buy a house" },
  { value: "education", label: "Education fund" },
  { value: "vacation", label: "Vacation / travel" },
  { value: "emergency", label: "Emergency fund" },
  { value: "wealth", label: "General wealth building" },
];

const MODES = [
  { value: "", label: "Select mode" },
  { value: "sip", label: "SIP (monthly)" },
  { value: "lumpsum", label: "One-time lump sum" },
];

const RISK_PREFS = [
  { value: "auto", label: "Auto-detect from profile" },
  { value: "conservative", label: "Conservative" },
  { value: "moderate", label: "Moderate" },
  { value: "aggressive", label: "Aggressive" },
];

const ASSET_COLORS = {
  Equity: "#378ADD",
  "Bonds / Debt": "#1D9E75",
  Gold: "#BA7517",
  "Real Estate (REITs)": "#7F77DD",
  Crypto: "#D85A30",
  "Cash / Liquid": "#888780",
};

const initialForm = {
  age: "",
  goal: "",
  horizon: "",
  amount: "",
  mode: "",
  risk_pref: "auto",
};

export default function App() {
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(null);
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(false);

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  function validateLocally() {
    const errs = [];
    if (!form.age) errs.push("Age is required.");
    if (!form.goal) errs.push("Goal is required.");
    if (!form.horizon) errs.push("Time horizon is required.");
    if (!form.amount) errs.push("Investment amount is required.");
    if (!form.mode) errs.push("Investment mode is required.");
    return errs;
  }

  // Flattens FastAPI's 422 validation error array into readable strings
  function parseFastApiErrors(detail) {
    if (typeof detail === "string") return [detail];
    if (Array.isArray(detail)) {
      return detail.map((d) => {
        const field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : "field";
        return `${field}: ${d.msg}`;
      });
    }
    return ["Something went wrong."];
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setErrors([]);

    const localErrors = validateLocally();
    if (localErrors.length > 0) {
      setErrors(localErrors);
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/advise`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          age: Number(form.age),
          goal: form.goal,
          horizon: Number(form.horizon),
          amount: Number(form.amount),
          mode: form.mode,
          risk_pref: form.risk_pref,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setErrors(parseFastApiErrors(data.detail));
        setResult(null);
      } else {
        setResult(data);
      }
    } catch (err) {
      setErrors([
        `Could not reach the Portfolio Advisor API. Is the backend running on ${API_BASE}?`,
      ]);
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setForm(initialForm);
    setResult(null);
    setErrors([]);
  }

  return (
    <div className="pa-page">
      <div className="pa-container">
        <header className="pa-header">
          <h1 className="pa-h1">Portfolio Advisor</h1>
          <p className="pa-subtitle">
            Personalised risk assessment and asset allocation
          </p>
        </header>

        {!result && (
          <form onSubmit={handleSubmit} className="pa-card">
            <p className="pa-section-label">Your profile</p>

            <div className="pa-grid">
              <Field label="Age">
                <input
                  type="number"
                  name="age"
                  min="18"
                  max="80"
                  placeholder="e.g. 28"
                  value={form.age}
                  onChange={handleChange}
                  className="pa-input"
                />
              </Field>

              <Field label="Financial goal">
                <select
                  name="goal"
                  value={form.goal}
                  onChange={handleChange}
                  className="pa-input"
                >
                  {GOALS.map((g) => (
                    <option key={g.value} value={g.value}>
                      {g.label}
                    </option>
                  ))}
                </select>
              </Field>

              <Field label="Time horizon (years)">
                <input
                  type="number"
                  name="horizon"
                  min="1"
                  max="50"
                  placeholder="e.g. 30"
                  value={form.horizon}
                  onChange={handleChange}
                  className="pa-input"
                />
              </Field>

              <Field label="Investment amount ($)">
                <input
                  type="number"
                  name="amount"
                  min="1"
                  placeholder="e.g. 500"
                  value={form.amount}
                  onChange={handleChange}
                  className="pa-input"
                />
              </Field>

              <Field label="Investment mode">
                <select
                  name="mode"
                  value={form.mode}
                  onChange={handleChange}
                  className="pa-input"
                >
                  {MODES.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label}
                    </option>
                  ))}
                </select>
              </Field>

              <Field label="Risk tolerance">
                <select
                  name="risk_pref"
                  value={form.risk_pref}
                  onChange={handleChange}
                  className="pa-input"
                >
                  {RISK_PREFS.map((r) => (
                    <option key={r.value} value={r.value}>
                      {r.label}
                    </option>
                  ))}
                </select>
              </Field>
            </div>

            {errors.length > 0 && (
              <div className="pa-error-box">
                {errors.map((err, i) => (
                  <div key={i}>{err}</div>
                ))}
              </div>
            )}

            <button type="submit" disabled={loading} className="pa-button">
              {loading ? "Calculating..." : "Generate my portfolio →"}
            </button>
          </form>
        )}

        {result && <Results result={result} onReset={handleReset} />}
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div className="pa-field">
      <label className="pa-label">{label}</label>
      {children}
    </div>
  );
}

function Results({ result, onReset }) {
  const { risk_profile: riskProfile, allocation } = result;
  const b = riskProfile.breakdown;

  return (
    <>
      <div className="pa-card">
        <p className="pa-section-label">Asset allocation</p>
        <div className="pa-metric-grid">
          <Metric
            label="Total invested"
            value={`$${allocation.total_amount.toLocaleString()}`}
          />
          <Metric
            label="Mode"
            value={allocation.mode === "sip" ? "Monthly SIP" : "Lump sum"}
          />
          <Metric label="Horizon" value={`${allocation.horizon_years} yr`} />
        </div>

        {allocation.slices.map((s) => (
          <AllocRow key={s.name} slice={s} mode={allocation.mode} />
        ))}

        {allocation.adjustments.length > 0 && (
          <>
            <p className="pa-section-label pa-mt-16">
              Context-specific adjustments
            </p>
            <ul className="pa-rationale-list">
              {allocation.adjustments.map((a, i) => (
                <li key={i} className="pa-rationale-item">
                  {a}
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
      <div>
        <div className="pa-card">
          <p className="pa-section-label">Risk assessment</p>
          <div className="pa-score-row">
            <span className="pa-score-value">{riskProfile.score.toFixed(1)}</span>
            <span className="pa-score-suffix">/ 10 risk score</span>
            <Tag profile={riskProfile.profile} />
          </div>
          <RiskBar score={riskProfile.score} />

          <p className="pa-section-label pa-mt-20">Score breakdown</p>
          <table className="pa-table">
            <tbody>
              <Row label="Base score" value={b.base_score.toFixed(1)} />
              <Row label="Age adjustment" value={fmt(b.age_adjustment)} />
              <Row label="Goal adjustment" value={fmt(b.goal_adjustment)} />
              <Row label="Horizon adjustment" value={fmt(b.horizon_adjustment)} />
              <Row label="Mode adjustment" value={fmt(b.mode_adjustment)} />
              <Row label="Final score" value={b.final_score.toFixed(1)} bold />
            </tbody>
          </table>

          <p className="pa-section-label pa-mt-20">Rationale</p>
          <ol className="pa-rationale-list">
            {b.rationale.map((r, i) => (
              <li key={i} className="pa-rationale-item">
                {r}
              </li>
            ))}
          </ol>
        </div>

        <button onClick={onReset} className="pa-secondary-button">
          Start over
        </button>
      </div>
    </>
  );
}

function Tag({ profile }) {
  const cls =
    profile === "Aggressive"
      ? "pa-tag pa-tag-aggressive"
      : profile === "Moderate"
      ? "pa-tag pa-tag-moderate"
      : "pa-tag pa-tag-conservative";
  return <span className={cls}>{profile}</span>;
}

function RiskBar({ score }) {
  const pct = score * 10;
  const fillClass =
    score >= 7
      ? "pa-risk-fill pa-risk-fill-aggressive"
      : score >= 4
      ? "pa-risk-fill pa-risk-fill-moderate"
      : "pa-risk-fill pa-risk-fill-conservative";
  return (
    <div>
      <div className="pa-risk-labels">
        <span>Conservative</span>
        <span>Aggressive</span>
      </div>
      <div className="pa-risk-bar-bg">
        <div className={fillClass} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function Row({ label, value, bold }) {
  return (
    <tr>
      <td className="pa-row-label">{label}</td>
      <td className={bold ? "pa-row-value pa-row-value-bold" : "pa-row-value"}>
        {value}
      </td>
    </tr>
  );
}

function Metric({ label, value }) {
  return (
    <div className="pa-metric">
      <div className="pa-metric-label">{label}</div>
      <div className="pa-metric-value">{value}</div>
    </div>
  );
}

function AllocRow({ slice, mode }) {
  const color = ASSET_COLORS[slice.name] || "#999";
  const amountLabel =
    mode === "sip" ? `$${slice.amount.toFixed(2)}/month` : `$${slice.amount.toFixed(2)}`;
  return (
    <div className="pa-alloc-row">
      <div className="pa-alloc-dot" style={{ background: color }} />
      <div className="pa-alloc-text">
        <div className="pa-alloc-name">{slice.name}</div>
        <div className="pa-alloc-desc">{slice.description}</div>
      </div>
      <div className="pa-alloc-bar-bg">
        <div
          className="pa-alloc-bar-fill"
          style={{ width: `${slice.pct}%`, background: color }}
        />
      </div>
      <div className="pa-alloc-pct">{slice.pct}%</div>
      <div className="pa-alloc-amount">{amountLabel}</div>
    </div>
  );
}

function fmt(n) {
  return (n >= 0 ? "+" : "") + n.toFixed(2);
}
