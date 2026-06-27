"""
Portfolio Advisor — Interactive CLI
====================================
Run with:
    python -m portfolio_advisor.cli.advisor_cli

Or pipe inputs:
    echo "28\nretirement\n30\n500\nsip\nauto" | python -m portfolio_advisor.cli.advisor_cli
"""

import sys
import os
import textwrap

# Allow running from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from portfolio_advisor.core import RiskEngine, AllocationEngine

# ── Terminal colour helpers (no external deps) ────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
RED    = "\033[31m"
BLUE   = "\033[34m"
WHITE  = "\033[37m"

BAR_FULL  = "█"
BAR_EMPTY = "░"
BAR_WIDTH = 30

ASSET_COLOURS = {
    "Equity":               BLUE,
    "Bonds / Debt":         GREEN,
    "Gold":                 YELLOW,
    "Real Estate (REITs)":  CYAN,
    "Crypto":               RED,
    "Cash / Liquid":        WHITE,
}

VALID_GOALS = ["retirement", "house", "education", "vacation", "emergency", "wealth"]
VALID_MODES = ["sip", "lumpsum"]
VALID_PREFS = ["auto", "conservative", "moderate", "aggressive"]


# ── Rendering helpers ─────────────────────────────────────────────────────────

def _bar(pct: float, width: int = BAR_WIDTH, colour: str = GREEN) -> str:
    filled = round(pct / 100 * width)
    return colour + BAR_FULL * filled + DIM + BAR_EMPTY * (width - filled) + RESET


def _divider(char: str = "─", width: int = 62) -> None:
    print(DIM + char * width + RESET)


def _header(text: str) -> None:
    _divider()
    print(BOLD + f"  {text}" + RESET)
    _divider()


def _profile_colour(profile: str) -> str:
    return {"Aggressive": RED, "Moderate": YELLOW, "Conservative": GREEN}.get(profile, WHITE)


# ── Input collection ──────────────────────────────────────────────────────────

def _ask(prompt: str, validate, error_msg: str):
    while True:
        raw = input(f"  {CYAN}{prompt}{RESET} ").strip()
        try:
            result = validate(raw)
            return result
        except (ValueError, KeyError):
            print(f"  {RED}✗ {error_msg}{RESET}")


def collect_inputs() -> dict:
    print()
    print(BOLD + "  ╔══════════════════════════════════════════╗" + RESET)
    print(BOLD + "  ║        PORTFOLIO ADVISOR  v1.0           ║" + RESET)
    print(BOLD + "  ╚══════════════════════════════════════════╝" + RESET)
    print()
    print(DIM + "  Answer a few questions to get your personalised allocation.\n" + RESET)

    age = _ask(
        "Your age:",
        lambda x: int(x) if 18 <= int(x) <= 80 else (_ for _ in ()).throw(ValueError()),
        "Enter a number between 18 and 80.",
    )

    print(f"  {DIM}Goals: {', '.join(VALID_GOALS)}{RESET}")
    goal = _ask(
        "Financial goal:",
        lambda x: x.lower() if x.lower() in VALID_GOALS else (_ for _ in ()).throw(ValueError()),
        f"Choose one of: {', '.join(VALID_GOALS)}",
    )

    horizon = _ask(
        "Investment horizon (years):",
        lambda x: int(x) if 1 <= int(x) <= 50 else (_ for _ in ()).throw(ValueError()),
        "Enter a number between 1 and 50.",
    )

    amount = _ask(
        "Investment amount ($):",
        lambda x: float(x) if float(x) > 0 else (_ for _ in ()).throw(ValueError()),
        "Enter a positive dollar amount.",
    )

    print(f"  {DIM}Options: sip (monthly) | lumpsum (one-time){RESET}")
    mode = _ask(
        "Investment mode:",
        lambda x: x.lower() if x.lower() in VALID_MODES else (_ for _ in ()).throw(ValueError()),
        "Enter 'sip' or 'lumpsum'.",
    )

    print(f"  {DIM}Options: auto | conservative | moderate | aggressive{RESET}")
    risk_pref = _ask(
        "Risk preference (or 'auto'):",
        lambda x: x.lower() if x.lower() in VALID_PREFS else (_ for _ in ()).throw(ValueError()),
        f"Choose one of: {', '.join(VALID_PREFS)}",
    )

    return dict(age=age, goal=goal, horizon=horizon,
                amount=amount, mode=mode, risk_pref=risk_pref)


# ── Output rendering ──────────────────────────────────────────────────────────

def render_risk_profile(profile) -> None:
    _header("RISK ASSESSMENT")
    b = profile.breakdown
    pc = _profile_colour(profile.profile)

    print(f"\n  Score   {BOLD}{pc}{profile.score:.1f} / 10{RESET}   "
          f"[{pc}{profile.profile.upper()}{RESET}]\n")
    print(f"  {_bar(profile.score * 10, colour=pc)}"
          f"  {DIM}{profile.score * 10:.0f}%{RESET}\n")

    print(BOLD + "  Score breakdown\n" + RESET)
    rows = [
        ("Base score",          f"{b.base_score:+.1f}"),
        ("Age adjustment",      f"{b.age_adjustment:+.2f}"),
        ("Goal adjustment",     f"{b.goal_adjustment:+.1f}"),
        ("Horizon adjustment",  f"{b.horizon_adjustment:+.1f}"),
        ("Mode adjustment",     f"{b.mode_adjustment:+.1f}"),
        ("Raw score",           f"{b.raw_score:.2f}"),
        ("Final score",         f"{BOLD}{b.final_score:.1f}{RESET}"),
    ]
    for label, val in rows:
        print(f"  {DIM}{label:<22}{RESET} {val}")

    print()
    print(BOLD + "  Rationale\n" + RESET)
    for i, note in enumerate(b.rationale, 1):
        wrapped = textwrap.wrap(note, width=56)
        print(f"  {DIM}{i}.{RESET} {wrapped[0]}")
        for cont in wrapped[1:]:
            print(f"     {cont}")
    print()


def render_allocation(alloc, mode_label: str) -> None:
    _header("ASSET ALLOCATION")
    print()

    for s in alloc.slices:
        colour = ASSET_COLOURS.get(s.name, WHITE)
        bar    = _bar(s.pct, width=24, colour=colour)
        amount_label = (
            f"${s.amount:>9,.2f}/month" if alloc.mode == "sip"
            else f"${s.amount:>9,.2f} lump"
        )
        print(f"  {colour}{s.name:<22}{RESET}")
        print(f"  {bar}  {BOLD}{s.pct:>5.1f}%{RESET}   {DIM}{amount_label}{RESET}")
        desc = textwrap.fill(s.description, width=54)
        for line in desc.splitlines():
            print(f"  {DIM}{line}{RESET}")
        print()

    if alloc.adjustments:
        print(BOLD + "  Context-specific adjustments\n" + RESET)
        for adj in alloc.adjustments:
            wrapped = textwrap.wrap(adj, width=56)
            print(f"  • {wrapped[0]}")
            for cont in wrapped[1:]:
                print(f"    {cont}")
        print()


def render_summary(inputs: dict, profile, alloc) -> None:
    _header("SUMMARY")
    total = alloc.total_amount
    pc    = _profile_colour(profile.profile)
    mode_str = "Monthly SIP" if inputs["mode"] == "sip" else "One-time lump sum"

    print(f"""
  Investor     Age {inputs['age']}
  Goal         {inputs['goal'].title()}
  Horizon      {inputs['horizon']} years
  Amount       ${total:,.2f} ({mode_str})
  Risk score   {pc}{BOLD}{profile.score:.1f}/10 — {profile.profile}{RESET}
""")

    equity = next((s for s in alloc.slices if s.name == "Equity"), None)
    bonds  = next((s for s in alloc.slices if s.name == "Bonds / Debt"), None)
    crypto = next((s for s in alloc.slices if s.name == "Crypto"), None)

    if equity:
        print(f"  {BLUE}▸ Equity drives growth at {equity.pct:.1f}% "
              f"(${equity.amount:,.2f}){RESET}")
    if bonds:
        print(f"  {GREEN}▸ Bonds stabilise the portfolio at {bonds.pct:.1f}%{RESET}")
    if crypto and crypto.pct > 0:
        print(f"  {RED}▸ Crypto capped at {crypto.pct:.1f}% — high-risk, high-reward{RESET}")
    print()
    _divider("═")
    print()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    try:
        inputs = collect_inputs()
    except (KeyboardInterrupt, EOFError):
        print("\n\n  Exiting. Goodbye!\n")
        sys.exit(0)

    print()
    risk_engine  = RiskEngine()
    alloc_engine = AllocationEngine()

    risk_profile = risk_engine.assess(
        age=inputs["age"],
        goal=inputs["goal"],
        horizon=inputs["horizon"],
        mode=inputs["mode"],
        risk_pref=inputs["risk_pref"],
    )

    allocation = alloc_engine.allocate(
        profile=risk_profile.profile,
        score=risk_profile.score,
        goal=inputs["goal"],
        mode=inputs["mode"],
        amount=inputs["amount"],
        horizon=inputs["horizon"],
    )

    render_risk_profile(risk_profile)
    render_allocation(allocation, inputs["mode"])
    render_summary(inputs, risk_profile, allocation)


if __name__ == "__main__":
    main()
