from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Optional
from ..services.ai import get_llm, build_system_prompt
from ..services.finance import fmt, calc_health_score
from langchain_core.messages import HumanMessage, SystemMessage

router = APIRouter(prefix="/api/budget", tags=["budget"])

# ══════════════════════════════════════════════════════════════════
# MODELS
# ══════════════════════════════════════════════════════════════════
class BudgetLimits(BaseModel):
    food:           float = 0
    transport:      float = 0
    entertainment:  float = 0
    subscriptions:  float = 0
    shopping:       float = 0
    other_expenses: float = 0

class AlertConfig(BaseModel):
    category:       str
    limit:          float
    current_spend:  float
    alert_at_pct:   float = 80.0  # alert when 80% of budget used

class BudgetAnalyseRequest(BaseModel):
    income:         float
    expenses:       Dict[str, float]
    budget_limits:  Dict[str, float]

class BudgetAnalyseResponse(BaseModel):
    status:         List[Dict]   # per-category status
    total_budget:   float
    total_spent:    float
    total_remaining:float
    overall_status: str          # "on_track" | "warning" | "over"
    alerts:         List[Dict]

class WeeklyReportRequest(BaseModel):
    profile:        Dict
    budget_limits:  Dict[str, float]
    week_expenses:  Dict[str, float]   # actual this week

class WeeklyReportResponse(BaseModel):
    report:         str
    top_category:   str
    total_spent:    float
    vs_weekly_avg:  float   # % vs expected weekly spend

class SuggestBudgetRequest(BaseModel):
    income:         float
    expenses:       Dict[str, float]
    savings_goal:   float   # desired monthly savings

class SuggestBudgetResponse(BaseModel):
    suggested:      Dict[str, float]
    reasoning:      Dict[str, str]
    achievable_savings: float


# ══════════════════════════════════════════════════════════════════
# CATEGORY CONFIG
# ══════════════════════════════════════════════════════════════════
CATEGORY_LABELS = {
    "food":           "Food & Delivery",
    "transport":      "Transport",
    "entertainment":  "Entertainment",
    "subscriptions":  "Subscriptions",
    "shopping":       "Shopping",
    "other_expenses": "Other",
}

CATEGORY_TIPS = {
    "food":          "Try cooking 2 extra meals at home per week. Meal prep on Sundays saves ₹2-3k/month.",
    "transport":     "Carpool or use metro for 3 days/week. Switch to monthly metro card.",
    "entertainment": "Look for free events, OTT sharing, or set a fixed 'fun money' envelope.",
    "subscriptions": "Audit all subscriptions — cancel anything unused for 30+ days.",
    "shopping":      "Apply the 48-hour rule: wait 2 days before any non-essential purchase.",
    "other_expenses":"Track this category for 2 weeks to understand where it's actually going.",
}


# ══════════════════════════════════════════════════════════════════
# BUDGET ANALYSIS
# ══════════════════════════════════════════════════════════════════
@router.post("/analyse", response_model=BudgetAnalyseResponse)
def analyse_budget(req: BudgetAnalyseRequest):
    status    = []
    alerts    = []
    total_budget  = 0
    total_spent   = 0
    overall       = "on_track"

    for cat, limit in req.budget_limits.items():
        if limit <= 0:
            continue
        spent     = req.expenses.get(cat, 0)
        remaining = max(0, limit - spent)
        pct_used  = (spent / limit * 100) if limit > 0 else 0
        over      = spent > limit
        total_budget += limit
        total_spent  += spent

        if pct_used >= 100:
            cat_status = "over"
            if overall != "over": overall = "over"
        elif pct_used >= 80:
            cat_status = "warning"
            if overall == "on_track": overall = "warning"
        else:
            cat_status = "on_track"

        entry = {
            "category":   cat,
            "label":      CATEGORY_LABELS.get(cat, cat.title()),
            "limit":      limit,
            "spent":      spent,
            "remaining":  remaining,
            "pct_used":   round(pct_used, 1),
            "status":     cat_status,
            "tip":        CATEGORY_TIPS.get(cat, ""),
        }
        status.append(entry)

        # Generate alert if over 80%
        if pct_used >= 80:
            alerts.append({
                "category":  cat,
                "label":     CATEGORY_LABELS.get(cat, cat.title()),
                "pct_used":  round(pct_used, 1),
                "spent":     spent,
                "limit":     limit,
                "overspend": max(0, spent - limit),
                "severity":  "high" if over else "medium",
                "message":   (
                    f"⚠️ Over budget by ₹{spent-limit:,.0f}!" if over
                    else f"🔔 {pct_used:.0f}% of budget used — ₹{remaining:,.0f} left"
                ),
            })

    return BudgetAnalyseResponse(
        status          = status,
        total_budget    = round(total_budget, 2),
        total_spent     = round(total_spent, 2),
        total_remaining = round(max(0, total_budget - total_spent), 2),
        overall_status  = overall,
        alerts          = alerts,
    )


# ══════════════════════════════════════════════════════════════════
# AI SUGGEST BUDGET
# ══════════════════════════════════════════════════════════════════
@router.post("/suggest", response_model=SuggestBudgetResponse)
def suggest_budget(req: SuggestBudgetRequest):
    """
    Given income + current expenses + savings goal,
    suggest an optimised budget using the 50/30/20 framework.
    """
    inc  = req.income
    exp  = req.expenses
    goal = req.savings_goal

    # Fixed costs (non-negotiable)
    fixed = {k: exp.get(k, 0) for k in ["rent", "electricity", "wifi", "mobile", "loan_emi", "credit_card"]}
    fixed_total = sum(fixed.values())
    available   = inc - fixed_total - goal

    if available <= 0:
        # Income too tight — suggest minimum viable budgets
        suggested = {cat: round(exp.get(cat, 0) * 0.8) for cat in CATEGORY_LABELS}
        reasoning = {cat: "Tight budget — reduced by 20% to hit savings goal" for cat in CATEGORY_LABELS}
        return SuggestBudgetResponse(suggested=suggested, reasoning=reasoning, achievable_savings=max(0, inc-fixed_total-sum(suggested.values())))

    # Distribute available across variable categories using weights
    weights = {
        "food":          0.40,
        "transport":     0.20,
        "entertainment": 0.12,
        "subscriptions": 0.08,
        "shopping":      0.10,
        "other_expenses":0.10,
    }

    suggested  = {}
    reasoning  = {}
    current_total_var = sum(exp.get(cat, 0) for cat in CATEGORY_LABELS)

    for cat, weight in weights.items():
        budget  = round(available * weight)
        current = exp.get(cat, 0)
        suggested[cat] = budget

        if current == 0:
            reasoning[cat] = f"Suggested ₹{budget:,} ({weight*100:.0f}% of discretionary budget)"
        elif budget >= current:
            reasoning[cat] = f"You currently spend ₹{current:,} — budget gives you ₹{budget:,} of room"
        else:
            cut = current - budget
            reasoning[cat] = f"Currently ₹{current:,} — need to cut ₹{cut:,} to hit savings goal"

    achievable = inc - fixed_total - sum(suggested.values())
    return SuggestBudgetResponse(
        suggested        = suggested,
        reasoning        = reasoning,
        achievable_savings = round(max(0, achievable), 2),
    )


# ══════════════════════════════════════════════════════════════════
# WEEKLY REPORT (AI generated)
# ══════════════════════════════════════════════════════════════════
@router.post("/weekly-report", response_model=WeeklyReportResponse)
def generate_weekly_report(req: WeeklyReportRequest):
    p             = req.profile
    week_exp      = req.week_expenses
    budget_limits = req.budget_limits
    inc           = p.get("income", 0)
    monthly_exp   = p.get("expenses", {})

    total_week   = sum(week_exp.values())
    weekly_avg   = sum(monthly_exp.values()) / 4.3   # expected weekly spend
    vs_avg       = ((total_week - weekly_avg) / weekly_avg * 100) if weekly_avg > 0 else 0
    top_cat      = max(week_exp, key=week_exp.get) if week_exp else "other"

    # Build budget comparison lines
    budget_lines = []
    for cat, spent in week_exp.items():
        monthly_limit = budget_limits.get(cat, 0)
        weekly_limit  = monthly_limit / 4.3 if monthly_limit > 0 else 0
        label         = CATEGORY_LABELS.get(cat, cat.title())
        if weekly_limit > 0:
            pct = spent / weekly_limit * 100
            budget_lines.append(f"  - {label}: spent ₹{spent:,.0f} vs weekly budget ₹{weekly_limit:,.0f} ({pct:.0f}%)")
        else:
            budget_lines.append(f"  - {label}: spent ₹{spent:,.0f} (no budget set)")

    budget_summary = "\n".join(budget_lines) if budget_lines else "  - No budget limits set yet"

    prompt = f"""You are FinanceGPT. Generate a brief, friendly, personalised WEEKLY financial report.

USER: {p.get('name', 'User')}, income ₹{inc:,}/month
GOALS: {p.get('goals', 'not specified')}

THIS WEEK'S SPENDING:
{chr(10).join([f"  - {CATEGORY_LABELS.get(k,k)}: ₹{v:,.0f}" for k,v in week_exp.items() if v > 0])}

TOTAL SPENT THIS WEEK: ₹{total_week:,.0f}
EXPECTED WEEKLY SPEND: ₹{weekly_avg:,.0f}
VARIANCE: {"over" if vs_avg > 0 else "under"} by {abs(vs_avg):.0f}%

BUDGET vs ACTUAL:
{budget_summary}

Write a weekly report in this exact structure:
1. One opening line greeting them by name with a brief verdict (good week / tough week)
2. "📊 This week in numbers" — 3-4 bullet points with key stats
3. "🔥 Watch out for" — the one biggest concern (be specific with numbers)
4. "✅ Win of the week" — one positive thing (even small)
5. "🎯 Focus for next week" — one specific actionable tip

Keep it under 180 words. Be direct, friendly, use ₹ and Indian context. No generic advice."""

    llm      = get_llm(temperature=0.6)
    response = llm.invoke([HumanMessage(content=prompt)])

    return WeeklyReportResponse(
        report       = response.content,
        top_category = CATEGORY_LABELS.get(top_cat, top_cat),
        total_spent  = round(total_week, 2),
        vs_weekly_avg= round(vs_avg, 2),
    )