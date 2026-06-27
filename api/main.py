from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.risk_engine import RiskEngine
from core.allocation_engine import AllocationEngine
from api.schemas import (
    AdviceRequest,
    AdviceResponse,
    RiskProfileOut,
    ScoreBreakdownOut,
    AllocationOut,
    AssetSliceOut,
    ErrorResponse,
)

app = FastAPI(
    title="Portfolio Advisor API",
    description=(
        "Automated robo-advisor that calculates a composite risk score "
        "and a personalised asset allocation across Equity, Bonds, Gold, "
        "Real Estate, Crypto, and Cash."
    ),
    version="1.0.0",
)

# ── CORS — open for local development; restrict in production ──────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

risk_engine = RiskEngine()
alloc_engine = AllocationEngine()


@app.get("/api/health", tags=["meta"])
def health_check():
    """Simple liveness check."""
    return {"status": "ok", "service": "portfolio-advisor-api"}
@app.get("/")
def root():
    return {
        "message": "Portfolio Advisor API is running!",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.post(
    "/api/advise",
    response_model=AdviceResponse,
    responses={400: {"model": ErrorResponse}},
    tags=["advisor"],
    summary="Generate a risk profile and asset allocation",
)
def advise(request: AdviceRequest) -> AdviceResponse:
    """
    Run the full Portfolio Advisor pipeline:

    1. Assess risk score (1-10) from age, goal, horizon, and mode.
    2. Map the risk profile to a percentage-based asset allocation.
    3. Convert percentages into dollar amounts based on the investment amount.
    """
    try:
        risk_profile = risk_engine.assess(
            age=request.age,
            goal=request.goal.value,
            horizon=request.horizon,
            mode=request.mode.value,
            risk_pref=request.risk_pref.value,
        )

        allocation = alloc_engine.allocate(
            profile=risk_profile.profile,
            score=risk_profile.score,
            goal=request.goal.value,
            mode=request.mode.value,
            amount=request.amount,
            horizon=request.horizon,
        )
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return AdviceResponse(
        risk_profile=RiskProfileOut(
            score=risk_profile.score,
            profile=risk_profile.profile,
            equity_baseline=risk_profile.equity_baseline,
            breakdown=ScoreBreakdownOut(
                base_score=risk_profile.breakdown.base_score,
                age_adjustment=risk_profile.breakdown.age_adjustment,
                goal_adjustment=risk_profile.breakdown.goal_adjustment,
                horizon_adjustment=risk_profile.breakdown.horizon_adjustment,
                mode_adjustment=risk_profile.breakdown.mode_adjustment,
                raw_score=risk_profile.breakdown.raw_score,
                final_score=risk_profile.breakdown.final_score,
                profile=risk_profile.breakdown.profile,
                rationale=risk_profile.breakdown.rationale,
            ),
        ),
        allocation=AllocationOut(
            slices=[
                AssetSliceOut(
                    name=s.name,
                    description=s.description,
                    pct=s.pct,
                    amount=s.amount,
                )
                for s in allocation.slices
            ],
            profile=allocation.profile,
            total_amount=allocation.total_amount,
            mode=allocation.mode,
            horizon_years=allocation.horizon_years,
            adjustments=allocation.adjustments,
        ),
    )