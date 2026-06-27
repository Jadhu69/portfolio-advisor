"""
Portfolio Advisor — Asset Allocation Engine
===========================================
Maps a risk score + context to a percentage-based portfolio allocation
across six asset classes, then converts percentages to dollar amounts.
"""

from dataclasses import dataclass
from typing import Literal

from .risk_engine import GoalType, ModeType, ProfileTag


# ── Asset class definitions ───────────────────────────────────────────────────

ASSET_CLASSES = [
    "Equity",
    "Bonds / Debt",
    "Gold",
    "Real Estate (REITs)",
    "Crypto",
    "Cash / Liquid",
]

ASSET_DESCRIPTIONS = {
    "Equity":               "Large-cap, mid-cap, and small-cap stocks for long-term growth.",
    "Bonds / Debt":         "Government and corporate bonds for capital preservation and fixed income.",
    "Gold":                 "Physical gold or gold ETFs as an inflation hedge and crash buffer.",
    "Real Estate (REITs)":  "Real Estate Investment Trusts for passive income and diversification.",
    "Crypto":               "High-risk, high-reward digital assets (strictly capped at 5%).",
    "Cash / Liquid":        "Liquid funds and money-market instruments for immediate access.",
}

# Base allocation templates keyed by profile label.
# Crypto is the highest-risk component and is hard-capped at 5%.
BASE_ALLOCATIONS: dict[str, dict[str, int]] = {
    "Aggressive": {
        "Equity": 65, "Bonds / Debt": 8, "Gold": 5,
        "Real Estate (REITs)": 12, "Crypto": 5, "Cash / Liquid": 5,
    },
    "Moderate": {
        "Equity": 50, "Bonds / Debt": 18, "Gold": 8,
        "Real Estate (REITs)": 12, "Crypto": 3, "Cash / Liquid": 9,
    },
    "Conservative": {
        "Equity": 35, "Bonds / Debt": 30, "Gold": 10,
        "Real Estate (REITs)": 10, "Crypto": 0, "Cash / Liquid": 15,
    },
}


# ── Result containers ─────────────────────────────────────────────────────────

@dataclass
class AssetSlice:
    """A single asset class with its allocation and monetary amount."""
    name:        str
    description: str
    pct:         float   # Percentage of total portfolio
    amount:      float   # Dollar value


@dataclass
class Allocation:
    """Full portfolio allocation result."""
    slices:        list[AssetSlice]
    profile:       ProfileTag
    total_amount:  float
    mode:          ModeType
    horizon_years: int
    adjustments:   list[str]   # Human-readable notes on contextual tweaks


# ── Allocation engine ─────────────────────────────────────────────────────────

class AllocationEngine:
    """
    Derives a portfolio allocation from a risk profile and contextual inputs.

    Steps:
        1. Start from the base template for Conservative / Moderate / Aggressive.
        2. Apply contextual tweaks (goal-specific, SIP mode, fine-grained score).
        3. Normalise all percentages so they sum to exactly 100.
        4. Compute dollar amounts per slice.

    Usage:
        engine = AllocationEngine()
        alloc  = engine.allocate(
                     profile="Aggressive", score=8.5,
                     goal="retirement", mode="sip",
                     amount=500, horizon=30)
    """

    # Crypto is absolutely capped regardless of any other logic
    CRYPTO_CAP = 5

    def allocate(
        self,
        profile:  ProfileTag,
        score:    float,
        goal:     GoalType,
        mode:     ModeType,
        amount:   float,
        horizon:  int,
    ) -> Allocation:
        """Produce the full portfolio allocation."""

        alloc: dict[str, float] = {k: float(v) for k, v in BASE_ALLOCATIONS[profile].items()}
        adjustments: list[str] = []

        # ── Contextual tweaks ──────────────────────────────────────────────

        # 1. Emergency/vacation goals: force a minimum cash buffer
        if goal == "emergency":
            target_cash = max(alloc["Cash / Liquid"], 30.0)
            delta = target_cash - alloc["Cash / Liquid"]
            if delta > 0:
                alloc["Cash / Liquid"] = target_cash
                alloc["Equity"] = max(0, alloc["Equity"] - delta * 0.6)
                alloc["Bonds / Debt"] = max(0, alloc["Bonds / Debt"] - delta * 0.4)
                adjustments.append(
                    f"Emergency goal: cash buffer raised to {target_cash:.0f}%, "
                    "funded from equity and bonds."
                )

        elif goal in ("vacation", "house"):
            alloc["Cash / Liquid"] += 5.0
            alloc["Equity"] = max(0, alloc["Equity"] - 3.0)
            alloc["Bonds / Debt"] = max(0, alloc["Bonds / Debt"] - 2.0)
            adjustments.append(
                f"Goal '{goal}': +5% cash for near-term liquidity."
            )

        # 2. SIP mode: cost-averaging justifies slightly more equity
        if mode == "sip" and profile != "Conservative":
            boost = min(3.0, 75.0 - alloc["Equity"])
            if boost > 0:
                alloc["Equity"] += boost
                alloc["Cash / Liquid"] = max(0, alloc["Cash / Liquid"] - boost)
                adjustments.append(
                    f"SIP mode: equity boosted by {boost:.0f}% via cost-averaging benefit."
                )

        # 3. Fine-grained score sub-adjustments within profile bands
        #    (e.g., score 9.5 vs 7.0 within Aggressive)
        if profile == "Aggressive" and score >= 9.0:
            alloc["Equity"] = min(alloc["Equity"] + 3, 75)
            alloc["Cash / Liquid"] = max(0, alloc["Cash / Liquid"] - 3)
            adjustments.append("Score ≥ 9.0: maximum growth tilt (+3% equity).")
        elif profile == "Conservative" and score <= 2.0:
            alloc["Bonds / Debt"] += 5
            alloc["Equity"] = max(0, alloc["Equity"] - 5)
            adjustments.append("Score ≤ 2.0: maximum safety tilt (+5% bonds).")

        # 4. Enforce crypto cap absolutely
        if alloc["Crypto"] > self.CRYPTO_CAP:
            excess = alloc["Crypto"] - self.CRYPTO_CAP
            alloc["Crypto"] = float(self.CRYPTO_CAP)
            alloc["Equity"] += excess
            adjustments.append(
                f"Crypto hard-capped at {self.CRYPTO_CAP}%; "
                f"excess {excess:.1f}% redirected to equity."
            )

        # 5. Short horizon: eliminate crypto entirely
        if horizon <= 5 and alloc["Crypto"] > 0:
            alloc["Bonds / Debt"] += alloc["Crypto"]
            adjustments.append(
                f"Short horizon ({horizon} yr): crypto removed, added to bonds."
            )
            alloc["Crypto"] = 0.0

        # ── Normalise to 100% ──────────────────────────────────────────────
        alloc = self._normalise(alloc)

        # ── Build result slices ────────────────────────────────────────────
        slices = [
            AssetSlice(
                name=name,
                description=ASSET_DESCRIPTIONS[name],
                pct=round(pct, 1),
                amount=round(amount * pct / 100, 2),
            )
            for name, pct in alloc.items()
            if pct > 0
        ]

        return Allocation(
            slices=slices,
            profile=profile,
            total_amount=amount,
            mode=mode,
            horizon_years=horizon,
            adjustments=adjustments,
        )

    @staticmethod
    def _normalise(alloc: dict[str, float]) -> dict[str, float]:
        """Scale all values proportionally so they sum to exactly 100."""
        total = sum(alloc.values())
        if total == 0:
            return alloc
        factor = 100.0 / total
        return {k: round(v * factor, 2) for k, v in alloc.items()}
