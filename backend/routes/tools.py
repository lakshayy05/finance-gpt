from fastapi import APIRouter, UploadFile, File, HTTPException
from ..models import SIPRequest, SIPResponse, TaxRequest, TaxResponse, StatementResponse, Transaction
from ..services.finance import calc_sip, sip_yearly_data, calc_tax_new, calc_tax_old
from ..services.parser import extract_text_from_pdf, parse_transactions_with_ai, aggregate_to_expenses
from ..services.ai import get_llm

router = APIRouter(prefix="/api", tags=["tools"])


# ── SIP Calculator ────────────────────────────────────────────────
@router.post("/sip/calculate", response_model=SIPResponse)
def calculate_sip(req: SIPRequest):
    invested, fv, gain = calc_sip(req.monthly_amount, req.annual_return, req.years)
    yearly             = sip_yearly_data(req.monthly_amount, req.annual_return, req.years)
    return SIPResponse(
        total_invested = round(invested, 2),
        final_value    = round(fv, 2),
        wealth_gained  = round(gain, 2),
        yearly_data    = yearly,
    )


# ── Tax Calculator ────────────────────────────────────────────────
@router.post("/tax/calculate", response_model=TaxResponse)
def calculate_tax(req: TaxRequest):
    tn, cn, totn, bdn, rbn = calc_tax_new(req.annual_income)
    to, co, toto, bdo, rbo, taxable, total_ded = calc_tax_old(
        req.annual_income, req.deductions_80c,
        req.deductions_80d, req.hra_exemption, req.other_deductions
    )
    better  = "new" if totn <= toto else "old"
    savings = abs(toto - totn)

    return TaxResponse(
        new_regime_tax   = tn,
        new_regime_cess  = cn,
        new_regime_total = totn,
        old_regime_tax   = to,
        old_regime_cess  = co,
        old_regime_total = toto,
        recommended      = better,
        savings          = round(savings, 2),
        new_breakdown    = bdn,
        old_breakdown    = bdo,
    )


# ── Bank Statement Parser ─────────────────────────────────────────
@router.post("/statement/parse", response_model=StatementResponse)
async def parse_statement(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    pdf_bytes = await file.read()
    if len(pdf_bytes) > 10 * 1024 * 1024:   # 10MB limit
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

    try:
        raw_text = extract_text_from_pdf(pdf_bytes)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    if len(raw_text.strip()) < 100:
        raise HTTPException(
            status_code=422,
            detail="Could not extract text. PDF may be scanned/image-based. Use a text PDF from net banking."
        )

    llm          = get_llm(temperature=0)
    transactions = parse_transactions_with_ai(raw_text, llm)

    if not transactions:
        raise HTTPException(
            status_code=422,
            detail="Could not parse transactions. Statement format may not be supported."
        )

    debits  = [t for t in transactions if t["type"] == "debit"]
    credits = [t for t in transactions if t["type"] == "credit"]

    return StatementResponse(
        transactions    = [Transaction(**t) for t in transactions],
        total_debit     = round(sum(t["amount"] for t in debits), 2),
        total_credit    = round(sum(t["amount"] for t in credits), 2),
        expense_summary = aggregate_to_expenses(transactions),
        txn_count       = len(transactions),
    )