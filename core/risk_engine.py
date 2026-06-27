"""
Portfolio Advisor — Risk Assessment Engine
==========================================
Converts user profile inputs into a composite Risk Score (1–10)
using a weighted multi-factor model.

Risk Score bands:
  1–3  →  Conservative
  4–6  →  Moderate
  7–10 →  Aggressive
"""

from dataclasses import dataclass, field
from typing import Literal

# ── Type aliases ──────────────────────────────────────────────────────────────

GoalType   = Literal["retirement", "house", "education", "vacation", "emergency", "wealth"]
ModeType   = Literal["sip", "lumpsum"]
RiskPref   = Literal["auto", "conservative", "moderate", "aggressive"]
ProfileTag = Literal["Conservative", "Moderate", "Aggressive"]


# ── Score contribution constants ──────────────────────────────────────────────

GOAL_ADJUSTMENTS: dict[GoalType, float] = {
    "retirement": +1.5,   # Long-term; can ride out volatility
    "wealth":     +1.5,   # General growth; long horizon assumed
    "education":  +1.0,   # Medium-to-long term
    "house":      -0.5,   # Medium term; needs capital preservation
    "vacation":   -2.0,   # Short-term; liquidity priority
    "emergency":  -2.5,   # Immediate safety net; near-zero risk
}

MODE_ADJUSTMENTS: dict[ModeType, float] = {
    "sip":     +0.5,   # Rupee/dollar-cost averaging reduces timing risk
    "lumpsum":  0.0,   # No smoothing benefit
}

HORIZON_THRESHOLDS: list[tuple[int, float]] = [
    (20, +1.5),   # 20+ years: full growth orientation
    (10, +0.8),   # 10–19 years: moderate growth
    (5,   0.0),   # 5–9 years: neutral
    (3,  -1.5),   # 3–4 years: reduce risk
    (0,  -2.5),   # Under 3 years: capital preservation
]

# Hard clamps applied when the user sets an explicit risk preference
RISK_PREF_CLAMPS: dict[str, tuple[float, float]] = {
    "conservative": (1.0, 4.0),
    "moderate":     (4.0, 7.0),
    "aggressive":   (7.0, 10.0),
    "auto":         (1.0, 10.0),   # No clamp; engine decides
}


# ── Result containers ─────────────────────────────────────────────────────────

@dataclass
class ScoreBreakdown:
    """Detailed audit trail of every adjustment applied to the risk score."""
    base_score:        float = 5.0
    age_adjustment:    float = 0.0
    goal_adjustment:   float = 0.0
    horizon_adjustment: float = 0.0
    mode_adjustment:   float = 0.0
    raw_score:         float = 0.0   # Sum before clamping
    final_score:       float = 0.0   # After clamping to [1, 10]
    profile:           ProfileTag = "Moderate"
    rationale:         list[str] = field(default_factory=list)


@dataclass
class RiskProfile:
    """Public-facing result returned by the engine."""
    score:     float          # 1–10
    profile:   ProfileTag     # "Conservative" | "Moderate" | "Aggressive"
    breakdown: ScoreBreakdown
    equity_baseline: int      # % from 100-minus-age rule


# ── Core engine ───────────────────────────────────────────────────────────────

class RiskEngine:
    """
    Calculates an investor's composite risk score.

    Model:
        score = BASE
              + age_adjustment          (from 100-minus-age rule)
              + goal_adjustment         (from goal type)
              + horizon_adjustment      (from time horizon)
              + mode_adjustment         (from SIP vs lump-sum)

        Final score is clamped to [1, 10], then optionally
        bounded by the user's stated risk preference.

    Usage:
        engine = RiskEngine()
        profile = engine.assess(age=28, goal="retirement",
                                horizon=30, mode="sip")
        print(profile.score)   # e.g. 8.5
    """

    BASE_SCORE = 5.0
    AGE_MIDPOINT = 50      # Equity % above this → positive adjustment
    AGE_SCALE    = 20.0    # Sensitivity divisor for age delta

    def assess(
        self,
        age:      int,
        goal:     GoalType,
        horizon:  int,
        mode:     ModeType,
        risk_pref: RiskPref = "auto",
    ) -> RiskProfile:
        """Run the full risk assessment and return a RiskProfile."""

        b = ScoreBreakdown(base_score=self.BASE_SCORE)

        # ── Step 1: Age adjustment (100-minus-age rule) ───────────────────
        # Traditional rule: equity % = 100 - age
        # We centre on 50% equity (midpoint) and scale the deviation.
        # A 25-year-old gets +1.25; a 65-year-old gets −0.75.
        equity_pct = max(0, min(100, 100 - age))
        b.age_adjustment = (equity_pct - self.AGE_MIDPOINT) / self.AGE_SCALE
        b.rationale.append(
            f"Age {age}: 100−age rule → {equity_pct}% equity baseline → "
            f"adjustment {b.age_adjustment:+.2f}"
        )

        # ── Step 2: Goal adjustment ───────────────────────────────────────
        b.goal_adjustment = GOAL_ADJUSTMENTS.get(goal, 0.0)
        b.rationale.append(
            f"Goal '{goal}': adjustment {b.goal_adjustment:+.1f}"
        )

        # ── Step 3: Time horizon adjustment ──────────────────────────────
        # Walk thresholds from highest to lowest; first match wins.
        b.horizon_adjustment = HORIZON_THRESHOLDS[-1][1]   # default: shortest
        for min_years, adj in HORIZON_THRESHOLDS:
            if horizon >= min_years:
                b.horizon_adjustment = adj
                break
        b.rationale.append(
            f"Time horizon {horizon} yr: adjustment {b.horizon_adjustment:+.1f}"
        )

        # ── Step 4: Mode adjustment ───────────────────────────────────────
        b.mode_adjustment = MODE_ADJUSTMENTS.get(mode, 0.0)
        if mode == "sip":
            b.rationale.append("SIP mode: cost-averaging benefit → +0.5")
        else:
            b.rationale.append("Lump-sum mode: no timing-risk smoothing → 0.0")

        # ── Step 5: Sum and clamp to [1, 10] ─────────────────────────────
        b.raw_score = (
            b.base_score
            + b.age_adjustment
            + b.goal_adjustment
            + b.horizon_adjustment
            + b.mode_adjustment
        )
        b.final_score = round(max(1.0, min(10.0, b.raw_score)), 1)

        # ── Step 6: Apply explicit risk-preference clamp ──────────────────
        if risk_pref != "auto":
            lo, hi = RISK_PREF_CLAMPS[risk_pref]
            clamped = round(max(lo, min(hi, b.final_score)), 1)
            if clamped != b.final_score:
                b.rationale.append(
                    f"User preference '{risk_pref}' clamped score "
                    f"{b.final_score} → {clamped}"
                )
                b.final_score = clamped

        # ── Step 7: Derive profile label ──────────────────────────────────
        b.profile = self._score_to_profile(b.final_score)
        b.rationale.append(f"Final score: {b.final_score}/10 → {b.profile}")

        return RiskProfile(
            score=b.final_score,
            profile=b.profile,
            breakdown=b,
            equity_baseline=equity_pct,
        )

    @staticmethod
    def _score_to_profile(score: float) -> ProfileTag:
        if score >= 7.0:
            return "Aggressive"
        if score >= 4.0:
            return "Moderate"
        return "Conservative"
