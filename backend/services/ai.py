import os
import requests
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from .finance import (calc_health_score, get_score_label, get_priority,
                      calc_tax_new, fmt)

# ── Environment variables ─────────────────────────────────────────
# Add these to your .env:
#   HF_TOKEN=hf_your_write_token_here
#   HF_MODEL_URL=https://api-inference.huggingface.co/models/your-username/FinanceGPT-Mistral-7B
#   MISTRAL_API_KEY=your_mistral_key  (used as fallback)

HF_TOKEN     = os.getenv("HF_TOKEN", "")
HF_MODEL_URL = os.getenv("HF_MODEL_URL", "")


# ══════════════════════════════════════════════════════════════════
# SYSTEM PROMPT BUILDER
# ══════════════════════════════════════════════════════════════════
def build_system_prompt(profile: dict) -> str:
    exp      = profile["expenses"]
    inv      = profile["investments"]
    inc      = profile["income"]
    texp     = profile["total_expenses"]
    sav      = profile["savings"]
    invested = sum(inv.values())
    surplus  = inc - texp
    free_cash= max(0, surplus - invested)
    ef_target= texp * 6
    ef_gap   = max(0, ef_target - sav)
    months_ef= round(ef_gap / surplus) if surplus > 0 else 999
    debt     = exp.get("loan_emi", 0) + exp.get("credit_card", 0)
    sr       = round((surplus / inc) * 100, 1) if inc > 0 else 0
    used_80c = (inv.get("ppf", 0) + inv.get("nps", 0) + inv.get("mutual_funds", 0)) * 12
    rem_80c  = max(0, 150000 - used_80c)
    living   = "owns home / with family" if profile.get("owns_home") else f"paying rent ₹{exp.get('rent', 0):,}/mo"
    inv_lines= "\n".join([
        f"  - {k.replace('_',' ').title()}: ₹{v:,}/mo"
        for k, v in inv.items() if v > 0
    ]) or "  - None yet"
    health   = profile.get("health_score", 0)
    _, prio  = get_priority(inc, texp, sav, invested, debt)
    _, _, total_tax, _, _ = calc_tax_new(inc * 12)

    stmt_note = ""
    if profile.get("statement_parsed"):
        stmt_note = f"\nNOTE: User uploaded a bank statement ({profile.get('txn_count', 0)} transactions). Expense data is from REAL spending, not estimates."

    return f"""You are FinanceGPT — a sharp, warm, deeply knowledgeable personal finance coach built specifically for Indian salaried professionals aged 24-32.{stmt_note}

PERSONALITY:
- Speak like a smart CA friend — warm, direct, no jargon
- Use Hinglish naturally when it fits ("yaar", "ekdum solid plan")
- Celebrate small wins. ₹500/month SIP is worth acknowledging
- Never shame spending habits. Money habits are hard to change
- Be encouraging — always

USER PROFILE:
Name: {profile['name']}, {profile.get('age', '')} yrs | Housing: {living}
Monthly income:  ₹{inc:,}
Total expenses:  ₹{texp:,}/mo ({100-sr:.0f}% of income)
Monthly surplus: ₹{surplus:,} ({sr}% savings rate)
Free cash:       ₹{free_cash:,}/mo (uninvested surplus)
Liquid savings:  ₹{sav:,}
Goals:           {profile.get('goals', 'not specified')}
Health score:    {health}/100

EXPENSE BREAKDOWN:
  Rent/housing:  ₹{exp.get('rent', 0):,}
  Food:          ₹{exp.get('food', 0):,}
  Transport:     ₹{exp.get('transport', 0):,}
  Mobile:        ₹{exp.get('mobile', 0):,}
  WiFi:          ₹{exp.get('wifi', 0):,}
  Electricity:   ₹{exp.get('electricity', 0):,}
  Subscriptions: ₹{exp.get('subscriptions', 0):,}
  Loan EMI:      ₹{exp.get('loan_emi', 0):,}
  Credit card:   ₹{exp.get('credit_card', 0):,}
  Entertainment: ₹{exp.get('entertainment', 0):,}
  Other:         ₹{exp.get('other_expenses', 0):,}

INVESTMENTS (monthly):
{inv_lines}

PRE-CALCULATED NUMBERS — use these exactly, never recalculate:
  Emergency fund target:  ₹{ef_target:,.0f} (6× monthly expenses)
  Emergency fund gap:     ₹{ef_gap:,.0f}
  Months to full EF:      {months_ef} months at current surplus
  Debt/month:             ₹{debt:,} ({debt/inc*100:.0f}% of income)
  80C used this year:     ₹{used_80c:,}
  80C remaining:          ₹{rem_80c:,}
  Annual tax estimate:    ₹{total_tax:,.0f}

CURRENT PRIORITY: {prio}

STRICT RULES:
1. ALWAYS use the pre-calculated numbers above — never invent figures
2. Show math step by step for any calculation
3. India-specific only: PPF, NPS, ELSS, 80C (₹1.5L limit), 80D, HRA, EPF, Nifty 50 index funds
4. For SIP: suggest Groww or Zerodha, minimum ₹500/month to start
5. Never recommend specific stocks — suggest index funds only
6. Never claim SEBI registration
7. Use ₹ and Indian number system (lakhs/crores, not millions)
8. End every reply with ONE clear "next action" the user can do TODAY
9. Keep replies under 200 words unless user explicitly asks for more detail
10. If user mentions a bonus or salary hike, recalculate plan with that new number
"""


# ══════════════════════════════════════════════════════════════════
# OPENING MESSAGE BUILDER
# ══════════════════════════════════════════════════════════════════
def build_opening_message(profile: dict) -> str:
    inc      = profile["income"]
    texp     = profile["total_expenses"]
    sav      = profile["savings"]
    inv      = profile["investments"]
    exp      = profile["expenses"]
    surplus  = inc - texp
    invested = sum(inv.values())
    free     = max(0, surplus - invested)
    ef_t     = texp * 6
    ef_pct   = min(100, sav / ef_t * 100) if ef_t > 0 else 0
    sr       = (surplus / inc * 100) if inc > 0 else 0
    score    = profile.get("health_score", 0)
    ptag, ptxt = get_priority(
        inc, texp, sav, invested,
        exp.get("loan_emi", 0) + exp.get("credit_card", 0)
    )

    stmt = ""
    if profile.get("statement_parsed"):
        stmt = f"\n\n📂 **Bank statement imported** — {profile.get('txn_count', 0)} real transactions analysed. Numbers below are from your actual spending."

    lines = []
    if sr < 10:   lines.append(f"🔴 **Savings rate: {sr:.0f}%** — very low. Target is 20%+. Expenses consuming {100-sr:.0f}% of income.")
    elif sr < 20: lines.append(f"🟡 **Savings rate: {sr:.0f}%** — decent start, but 20%+ is where you want to be.")
    else:         lines.append(f"🟢 **Savings rate: {sr:.0f}%** — solid! Most people your age save under 10%.")

    if sav < ef_t * 0.5:   lines.append(f"🔴 **Emergency fund: {ef_pct:.0f}% built** ({fmt(sav)} of {fmt(ef_t)} target). This is your #1 priority right now.")
    elif sav < ef_t:        lines.append(f"🟡 **Emergency fund: {ef_pct:.0f}% done** ({fmt(sav)} of {fmt(ef_t)}). Keep going!")
    else:                   lines.append(f"🟢 **Emergency fund: fully funded** at {fmt(sav)}. Excellent safety net.")

    if invested == 0:           lines.append(f"🔴 **No investments yet.** Even ₹500/month in a Nifty 50 SIP started today beats waiting.")
    elif invested < inc * 0.1:  lines.append(f"🟡 **Investing {fmt(invested)}/month** ({invested/inc*100:.0f}%). Try to reach 20% of income.")
    else:                       lines.append(f"🟢 **Investing {fmt(invested)}/month** — great habit. Let's optimise.")

    if free > 5000: lines.append(f"💡 **{fmt(free)}/month sitting idle** — that's money not working for you.")

    food_pct = exp.get("food", 0) / inc * 100
    if food_pct > 25: lines.append(f"🍕 **Food: {food_pct:.0f}% of income** ({fmt(exp.get('food',0))}). Small cuts here compound fast.")

    insights = "\n".join(lines[:5])
    surplus_line = (
        "That gives us solid room to work with! 💪" if surplus > 8000
        else "It's tight but workable — let's optimise." if surplus > 0
        else "Your expenses exceed income — this needs immediate attention."
    )

    # Show which model is powering the response
    model_note = ""
    if HF_TOKEN and HF_MODEL_URL:
        model_note = "\n\n_Powered by FinanceGPT-Mistral-7B — fine-tuned on Indian finance data_ 🤖"

    return f"""Hey {profile['name']}! 👋 I've analysed your complete financial picture.{stmt}

**Financial Health Score: {score}/100 — {get_score_label(score)}**

**What I see in your numbers:**
{insights}

---
**{ptag}: {ptxt}**

Your monthly surplus is **{fmt(surplus)}**. {surplus_line}

**What do you want to tackle first?**
1. 📋 Build a step-by-step plan to fix your top issues
2. 💰 Calculate your tax savings under 80C this year
3. 📈 Design a SIP strategy for your goals: _{profile.get('goals', 'not specified')}_
4. ✂️ Find where to cut expenses without killing your lifestyle

Just ask — I'll go deep on whatever you need. 🚀{model_note}"""


# ══════════════════════════════════════════════════════════════════
# HUGGING FACE INFERENCE — fine-tuned model
# ══════════════════════════════════════════════════════════════════
def _build_mistral_prompt(system_prompt: str, history: list, user_input: str) -> str:
    """Build Mistral instruct format prompt."""
    prompt = f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n"

    for msg in history:
        if msg["role"] == "user":
            prompt += f"{msg['content']} [/INST] "
        elif msg["role"] == "assistant":
            prompt += f"{msg['content']} </s><s>[INST] "

    prompt += f"{user_input} [/INST]"
    return prompt


def _call_hf_model(system_prompt: str, history: list, user_input: str) -> str | None:
    """
    Call the fine-tuned FinanceGPT model on Hugging Face.
    Returns None if unavailable (triggers Mistral fallback).
    """
    if not HF_TOKEN or not HF_MODEL_URL:
        return None

    prompt = _build_mistral_prompt(system_prompt, history, user_input)

    try:
        response = requests.post(
            HF_MODEL_URL,
            headers = {
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type":  "application/json",
            },
            json = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens":   300,
                    "temperature":      0.3,
                    "do_sample":        True,
                    "return_full_text": False,   # only return generated part
                    "repetition_penalty": 1.1,
                }
            },
            timeout = 60,   # HF cold start can take up to 60s
        )

        if response.status_code == 503:
            # Model is loading — cold start
            print("HF model loading (cold start) — falling back to Mistral")
            return None

        if response.status_code != 200:
            print(f"HF API error {response.status_code} — falling back to Mistral")
            return None

        result = response.json()

        # HF returns list: [{"generated_text": "..."}]
        if isinstance(result, list) and result:
            text = result[0].get("generated_text", "").strip()
            if text:
                return text

        # Sometimes returns dict directly
        if isinstance(result, dict):
            text = result.get("generated_text", "").strip()
            if text:
                return text

        return None

    except requests.Timeout:
        print("HF model timeout — falling back to Mistral")
        return None
    except Exception as e:
        print(f"HF model error: {e} — falling back to Mistral")
        return None


# ══════════════════════════════════════════════════════════════════
# MISTRAL FALLBACK
# ══════════════════════════════════════════════════════════════════
def _call_mistral(system_prompt: str, history: list, user_input: str) -> str:
    """Original Mistral API — used as fallback when HF model is unavailable."""
    llm = ChatMistralAI(
        model       = "mistral-large-latest",
        api_key     = os.getenv("MISTRAL_API_KEY"),
        temperature = 0.3,
        max_tokens  = 1024,
    )

    messages = [SystemMessage(content=system_prompt)]
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=user_input))

    return llm.invoke(messages).content


# ══════════════════════════════════════════════════════════════════
# MAIN CHAT FUNCTION — called by routes/chat.py
# ══════════════════════════════════════════════════════════════════
def chat(system_prompt: str, history: list, user_input: str) -> str:
    """
    Send message to AI and get response.
    Tries fine-tuned HF model first, falls back to Mistral API.

    Args:
        system_prompt: Built by build_system_prompt() with user's financial profile
        history:       List of {"role": "user"|"assistant", "content": str}
        user_input:    Current user message

    Returns:
        AI response string
    """
    # Try fine-tuned model first
    hf_response = _call_hf_model(system_prompt, history, user_input)
    if hf_response:
        print("Response from: FinanceGPT-Mistral-7B (fine-tuned)")
        return hf_response

    # Fallback to Mistral API
    print("Response from: Mistral API (fallback)")
    return _call_mistral(system_prompt, history, user_input)


# ══════════════════════════════════════════════════════════════════
# LEGACY — kept for backward compatibility
# ══════════════════════════════════════════════════════════════════
def get_llm(temperature: float = 0.3):
    """Legacy function — use chat() instead."""
    return ChatMistralAI(
        model       = "mistral-large-latest",
        api_key     = os.getenv("MISTRAL_API_KEY"),
        temperature = temperature,
        max_tokens  = 1024,
    )