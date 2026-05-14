from fastapi import APIRouter
from ..models import UserProfile, ProfileResponse, AnalysisRequest, AnalysisResponse
from ..services.finance import (calc_health_score, get_score_label,
                                 get_priority, fmt)
from ..services.ai import build_opening_message
import uuid

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _enrich_profile(profile: UserProfile) -> dict:
    """Convert profile model to dict and add derived fields."""
    p = profile.dict()
    exp  = p["expenses"]
    inv  = p["investments"]
    inc  = p["income"]
    texp = sum(exp.values())
    invested = sum(inv.values())
    debt = exp.get("loan_emi", 0) + exp.get("credit_card", 0)

    p["total_expenses"] = texp
    p["health_score"]   = calc_health_score(inc, texp, p["savings"], invested, debt)
    return p


@router.post("", response_model=ProfileResponse)
def save_profile(profile: UserProfile):
    """
    Receives user profile, calculates derived metrics, returns summary.
    In production this would save to Supabase.
    """
    p        = _enrich_profile(profile)
    surplus  = p["income"] - p["total_expenses"]
    score    = p["health_score"]

    return ProfileResponse(
        profile_id    = str(uuid.uuid4()),   # placeholder — Supabase will give real ID
        health_score  = score,
        total_expenses= p["total_expenses"],
        surplus       = surplus,
        message       = f"Profile saved. Health score: {score}/100 — {get_score_label(score)}",
    )


@router.post("/analyse", response_model=AnalysisResponse)
def analyse_profile(req: AnalysisRequest):
    """Full analysis: score, priority, insights, opening chat message."""
    p        = _enrich_profile(req.profile)
    inc      = p["income"]
    texp     = p["total_expenses"]
    sav      = p["savings"]
    invested = sum(p["investments"].values())
    exp      = p["expenses"]
    debt     = exp.get("loan_emi", 0) + exp.get("credit_card", 0)
    surplus  = inc - texp
    score    = p["health_score"]
    sr       = (surplus / inc * 100) if inc > 0 else 0

    ptag, ptxt = get_priority(inc, texp, sav, invested, debt)

    # Build insights list
    insights = []
    ef_t   = texp * 6
    ef_pct = min(100, sav / ef_t * 100) if ef_t > 0 else 0

    if sr < 10:
        insights.append({"type":"bad",  "title":"Savings rate","text":f"{sr:.0f}% — very low, target 20%+"})
    elif sr < 20:
        insights.append({"type":"warn", "title":"Savings rate","text":f"{sr:.0f}% — decent, push to 20%"})
    else:
        insights.append({"type":"good", "title":"Savings rate","text":f"{sr:.0f}% — solid!"})

    if sav < ef_t * 0.5:
        insights.append({"type":"bad",  "title":"Emergency fund","text":f"{ef_pct:.0f}% built ({fmt(sav)} of {fmt(ef_t)})"})
    elif sav < ef_t:
        insights.append({"type":"warn", "title":"Emergency fund","text":f"{ef_pct:.0f}% done — keep going"})
    else:
        insights.append({"type":"good", "title":"Emergency fund","text":f"Fully funded at {fmt(sav)}"})

    if invested == 0:
        insights.append({"type":"bad",  "title":"Investments","text":"None yet — start ₹500/month SIP"})
    elif invested < inc * 0.1:
        insights.append({"type":"warn", "title":"Investments","text":f"{fmt(invested)}/month — push to 20%"})
    else:
        insights.append({"type":"good", "title":"Investments","text":f"{fmt(invested)}/month invested"})

    food_pct = exp.get("food", 0) / inc * 100
    if food_pct > 25:
        insights.append({"type":"warn", "title":"Food spending","text":f"{food_pct:.0f}% of income — high"})

    used_80c = (p["investments"].get("ppf", 0) + p["investments"].get("nps", 0) + p["investments"].get("mutual_funds", 0)) * 12
    rem_80c  = max(0, 150000 - used_80c)
    if rem_80c > 0:
        insights.append({"type":"warn", "title":"80C opportunity","text":f"₹{rem_80c:,} unused — save ~₹{rem_80c*0.2:,.0f} in tax"})

    opening = build_opening_message(p)

    return AnalysisResponse(
        health_score    = score,
        score_label     = get_score_label(score),
        priority_tag    = ptag,
        priority_text   = ptxt,
        opening_message = opening,
        insights        = insights,
    )