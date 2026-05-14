import math
from typing import Dict, List, Tuple

# ══════════════════════════════════════════════════════════════════
# HEALTH SCORE
# ══════════════════════════════════════════════════════════════════
def calc_health_score(income: float, total_expenses: float,
                      savings: float, invested: float,
                      debt: float) -> int:
    score = 0
    sr = (income - total_expenses) / income if income > 0 else 0

    # Savings rate — 30 pts
    if sr >= .3:    score += 30
    elif sr >= .2:  score += 22
    elif sr >= .1:  score += 12
    else:           score += 4

    # Emergency fund — 25 pts
    ef_ratio = savings / (total_expenses * 6) if total_expenses > 0 else 0
    score += min(25, int(ef_ratio * 25))

    # Investment rate — 25 pts
    ir = invested / income if income > 0 else 0
    if ir >= .2:    score += 25
    elif ir >= .1:  score += 16
    elif ir > 0:    score += 8

    # Debt burden — 20 pts
    dr = debt / income if income > 0 else 0
    if dr == 0:     score += 20
    elif dr < .2:   score += 15
    elif dr < .35:  score += 7
    else:           score += 1

    return min(100, score)


def get_score_label(score: int) -> str:
    if score >= 75: return "Excellent 🎉"
    if score >= 50: return "On Track 👍"
    if score >= 30: return "Needs Work ⚠️"
    return "Critical 🚨"


def get_priority(income: float, total_expenses: float,
                 savings: float, invested: float,
                 debt: float) -> Tuple[str, str]:
    surplus = income - total_expenses
    free    = max(0, surplus - invested)

    if debt > income * 0.35:
        return "CRITICAL", "Debt over 35% of income — clear high-interest debt first"
    if savings < total_expenses * 3:
        return "PRIORITY 1", "Emergency fund dangerously low — build this before investing"
    if invested == 0:
        return "PRIORITY 1", "No investments yet — start a SIP, even ₹500/month"
    if free > 5000:
        return "OPPORTUNITY", f"₹{free:,.0f}/month sitting idle — put it to work"
    return "OPTIMISE", "Profile looks healthy — grow investments and optimise tax saving"


# ══════════════════════════════════════════════════════════════════
# FORMATTING
# ══════════════════════════════════════════════════════════════════
def fmt(n: float) -> str:
    if n >= 10000000: return f"₹{n/10000000:.2f}Cr"
    if n >= 100000:   return f"₹{n/100000:.2f}L"
    if n >= 1000:     return f"₹{n/1000:.1f}k"
    return f"₹{int(n):,}"


# ══════════════════════════════════════════════════════════════════
# SIP CALCULATOR
# ══════════════════════════════════════════════════════════════════
def calc_sip(monthly: float, rate_pa: float, years: int) -> Tuple[float, float, float]:
    """Returns (total_invested, final_value, wealth_gained)"""
    r = rate_pa / 100 / 12
    n = years * 12
    fv = monthly * (((1 + r) ** n - 1) / r) * (1 + r) if r > 0 else monthly * n
    invested = monthly * n
    return invested, fv, fv - invested


def sip_yearly_data(monthly: float, rate_pa: float, years: int) -> List[Dict]:
    r = rate_pa / 100 / 12
    data = []
    for yr in range(1, years + 1):
        n = yr * 12
        fv = monthly * (((1 + r) ** n - 1) / r) * (1 + r) if r > 0 else monthly * n
        data.append({"year": yr, "invested": monthly * n, "value": round(fv, 2)})
    return data


# ══════════════════════════════════════════════════════════════════
# TAX CALCULATOR
# ══════════════════════════════════════════════════════════════════
def calc_tax_new(annual_income: float):
    slabs = [
        (300000, 0.00, "Up to ₹3L"),
        (300000, 0.05, "₹3L–₹6L"),
        (300000, 0.10, "₹6L–₹9L"),
        (300000, 0.15, "₹9L–₹12L"),
        (300000, 0.20, "₹12L–₹15L"),
        (float("inf"), 0.30, "Above ₹15L"),
    ]
    tax = 0; rem = annual_income; bd = []
    for lim, rate, label in slabs:
        if rem <= 0: break
        t = min(rem, lim); tx = t * rate
        tax += tx
        if t > 0: bd.append({"range": label, "rate": f"{rate*100:.0f}%", "tax": round(tx, 2)})
        rem -= t
    rebate = tax if annual_income <= 700000 else 0
    tax = max(0, tax - rebate)
    cess = tax * 0.04
    return round(tax, 2), round(cess, 2), round(tax + cess, 2), bd, round(rebate, 2)


def calc_tax_old(annual_income: float, d80c: float, d80d: float,
                 hra: float, other: float):
    std = 50000
    total_ded = std + d80c + d80d + hra + other
    taxable = max(0, annual_income - total_ded)
    slabs = [
        (250000, 0.00, "Up to ₹2.5L"),
        (250000, 0.05, "₹2.5L–₹5L"),
        (500000, 0.20, "₹5L–₹10L"),
        (float("inf"), 0.30, "Above ₹10L"),
    ]
    tax = 0; rem = taxable; bd = []
    for lim, rate, label in slabs:
        if rem <= 0: break
        t = min(rem, lim); tx = t * rate
        tax += tx
        if t > 0: bd.append({"range": label, "rate": f"{rate*100:.0f}%", "tax": round(tx, 2)})
        rem -= t
    rebate = min(tax, 12500) if taxable <= 500000 else 0
    tax = max(0, tax - rebate)
    cess = tax * 0.04
    return round(tax, 2), round(cess, 2), round(tax + cess, 2), bd, round(rebate, 2), round(taxable, 2), round(total_ded, 2)


# ══════════════════════════════════════════════════════════════════
# MONTHS TO GOAL
# ══════════════════════════════════════════════════════════════════
def months_to_goal(target: float, saved: float, monthly: float) -> int:
    gap = target - saved
    if gap <= 0: return 0
    if monthly <= 0: return 999
    return math.ceil(gap / monthly)