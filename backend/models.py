from pydantic import BaseModel
from typing import Optional, List, Dict

# ── Expenses ──────────────────────────────────────────────────────
class Expenses(BaseModel):
    rent:           float = 0
    electricity:    float = 0
    wifi:           float = 0
    mobile:         float = 0
    loan_emi:       float = 0
    credit_card:    float = 0
    food:           float = 0
    transport:      float = 0
    entertainment:  float = 0
    subscriptions:  float = 0
    other_expenses: float = 0

# ── Investments ───────────────────────────────────────────────────
class Investments(BaseModel):
    mutual_funds:   float = 0
    stocks:         float = 0
    crypto:         float = 0
    ppf:            float = 0
    nps:            float = 0
    fixed_deposits: float = 0
    gold_silver:    float = 0
    real_estate:    float = 0
    other:          float = 0

# ── User Profile ──────────────────────────────────────────────────
class UserProfile(BaseModel):
    name:        str
    age:         int
    income:      float
    savings:     float
    owns_home:   bool = False
    goals:       str = "not specified"
    expenses:    Expenses
    investments: Investments

class ProfileResponse(BaseModel):
    profile_id:    str
    health_score:  int
    total_expenses: float
    surplus:       float
    message:       str

# ── Chat ──────────────────────────────────────────────────────────
class ChatMessage(BaseModel):
    role:    str   # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    profile:  UserProfile
    messages: List[ChatMessage]
    user_input: str

class ChatResponse(BaseModel):
    reply:    str
    messages: List[ChatMessage]   # updated history

# ── Analysis ─────────────────────────────────────────────────────
class AnalysisRequest(BaseModel):
    profile: UserProfile

class AnalysisResponse(BaseModel):
    health_score:  int
    score_label:   str
    priority_tag:  str
    priority_text: str
    opening_message: str
    insights:      List[Dict]

# ── SIP Calculator ────────────────────────────────────────────────
class SIPRequest(BaseModel):
    monthly_amount: float
    annual_return:  float  # percentage e.g. 12.0
    years:          int

class SIPResponse(BaseModel):
    total_invested:  float
    final_value:     float
    wealth_gained:   float
    yearly_data:     List[Dict]

# ── Tax Calculator ────────────────────────────────────────────────
class TaxRequest(BaseModel):
    annual_income:    float
    deductions_80c:   float = 0
    deductions_80d:   float = 0
    hra_exemption:    float = 0
    other_deductions: float = 0

class TaxResponse(BaseModel):
    new_regime_tax:   float
    new_regime_cess:  float
    new_regime_total: float
    old_regime_tax:   float
    old_regime_cess:  float
    old_regime_total: float
    recommended:      str   # "new" or "old"
    savings:          float
    new_breakdown:    List[Dict]
    old_breakdown:    List[Dict]

# ── Statement Parser ──────────────────────────────────────────────
class Transaction(BaseModel):
    date:        str
    description: str
    amount:      float
    type:        str      # "debit" or "credit"
    category:    str

class StatementResponse(BaseModel):
    transactions:   List[Transaction]
    total_debit:    float
    total_credit:   float
    expense_summary: Dict[str, float]
    txn_count:      int