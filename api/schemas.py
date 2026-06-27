"""
schemas.py
==========
Pydantic models defining the request and response shapes for the
Portfolio Advisor API. FastAPI uses these for automatic validation,
serialization, and OpenAPI docs generation.
"""

from enum import Enum
from typing import List

from pydantic import BaseModel, Field, ConfigDict


# ── Enums (mirror the Literal types in core/risk_engine.py) ──────────────────

class Goal(str, Enum):
    retirement = "retirement"
    house = "house"
    education = "education"
    vacation = "vacation"
    emergency = "emergency"
    wealth = "wealth"


class Mode(str, Enum):
    sip = "sip"
    lumpsum = "lumpsum"


class RiskPref(str, Enum):
    auto = "auto"
    conservative = "conservative"
    moderate = "moderate"
    aggressive = "aggressive"


# ── Request ────────────────────────────────────────────────────────────────

class AdviceRequest(BaseModel):
    age: int = Field(..., ge=18, le=80, description="Investor's age in years")
    goal: Goal = Field(..., description="Primary financial goal")
    horizon: int = Field(..., ge=1, le=50, description="Investment horizon in years")
    amount: float = Field(..., gt=0, description="Investment amount in dollars")
    mode: Mode = Field(..., description="SIP (recurring) or lump-sum investment")
    risk_pref: RiskPref = Field(
        default=RiskPref.auto,
        description="Optional explicit risk preference; 'auto' lets the engine decide",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "age": 28,
                "goal": "retirement",
                "horizon": 30,
                "amount": 500,
                "mode": "sip",
                "risk_pref": "auto",
            }
        }
    )


# ── Response: risk assessment ─────────────────────────────────────────────

class ScoreBreakdownOut(BaseModel):
    base_score: float
    age_adjustment: float
    goal_adjustment: float
    horizon_adjustment: float
    mode_adjustment: float
    raw_score: float
    final_score: float
    profile: str
    rationale: List[str]


class RiskProfileOut(BaseModel):
    score: float
    profile: str
    equity_baseline: int
    breakdown: ScoreBreakdownOut


# ── Response: allocation ──────────────────────────────────────────────────

class AssetSliceOut(BaseModel):
    name: str
    description: str
    pct: float
    amount: float


class AllocationOut(BaseModel):
    slices: List[AssetSliceOut]
    profile: str
    total_amount: float
    mode: str
    horizon_years: int
    adjustments: List[str]


# ── Combined response ──────────────────────────────────────────────────────

class AdviceResponse(BaseModel):
    risk_profile: RiskProfileOut
    allocation: AllocationOut


# ── Error response ─────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
