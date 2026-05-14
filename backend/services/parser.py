import io, json, re
from typing import List, Dict

try:
    import pdfplumber
    PDF_OK = True
except ImportError:
    PDF_OK = False

from langchain_core.messages import HumanMessage


CATEGORY_MAP = {
    "food":          ["swiggy","zomato","dunzo","blinkit","zepto","bigbasket","restaurant","cafe","food","pizza","burger","domino","mcdonald","kfc","subway"],
    "transport":     ["ola","uber","rapido","redbus","irctc","railway","metro","petrol","fuel","indigo","spicejet","airindia","makemytrip","ixigo","fastag","toll"],
    "subscriptions": ["netflix","hotstar","spotify","prime","youtube","disney","zee5","sonyliv","apple","microsoft","adobe","canva","notion"],
    "shopping":      ["amazon","flipkart","myntra","ajio","nykaa","meesho","snapdeal","h&m","zara","decathlon","croma","dmart","jiomart"],
    "utilities":     ["electricity","bescom","tata power","msedcl","bses","airtel","jio","vi","vodafone","broadband","wifi","water","gas","igl"],
    "health":        ["pharmacy","medical","apollo","medplus","netmeds","1mg","practo","hospital","clinic","doctor","lab","diagnostic","gym","cult"],
    "entertainment": ["pvr","inox","bookmyshow","gaming","steam","playstation","xbox","concert","event"],
    "investment":    ["groww","zerodha","kuvera","sip","mutual fund","nps","ppf","lic","policy","insurance","fd","deposit","elss"],
    "rent":          ["rent","landlord","society","maintenance","housing","apartment","flat","pg"],
    "salary":        ["salary","payroll","credited","bonus","incentive","reimbursement","refund"],
    "transfer":      ["neft","imps","upi","transfer","sent","received","atm","withdrawal","self transfer"],
}

CAT_TO_EXPENSE = {
    "food":"food","transport":"transport","rent":"rent",
    "utilities":"electricity","subscriptions":"subscriptions",
    "entertainment":"entertainment","shopping":"other_expenses",
    "health":"other_expenses","other":"other_expenses",
    "transfer":"other_expenses","investment":"other_expenses",
}


def categorise_local(description: str) -> str:
    desc = description.lower()
    for cat, keywords in CATEGORY_MAP.items():
        if any(kw in desc for kw in keywords):
            return cat
    return "other"


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    if not PDF_OK:
        raise RuntimeError("pdfplumber not installed. Run: pip install pdfplumber")
    pages = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
    return "\n".join(pages)


def parse_transactions_with_ai(raw_text: str, llm) -> List[Dict]:
    truncated = raw_text[:6000]
    prompt = f"""You are a bank statement parser for Indian banks.
Extract ALL transactions from the text below.

Return ONLY a valid JSON array. No explanation, no markdown, no backticks.
Each item must have exactly:
- "date": string (DD/MM/YYYY or as found)
- "description": string (merchant/narration)
- "amount": number (always positive)
- "type": "debit" or "credit"

Rules:
- Debits = money going OUT
- Credits = money coming IN (salary, refunds)
- Skip balance rows and headers
- Parse amounts like 1,500.00 as 1500.0
- Max 50 transactions

Bank statement text:
{truncated}

JSON array only:"""

    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()
    raw = re.sub(r"```json|```", "", raw).strip()

    try:
        transactions = json.loads(raw)
        clean = []
        for t in transactions:
            if all(k in t for k in ["date", "description", "amount", "type"]):
                t["amount"]   = float(str(t["amount"]).replace(",", ""))
                t["category"] = categorise_local(t["description"])
                clean.append(t)
        return clean
    except Exception:
        return []


def aggregate_to_expenses(transactions: List[Dict]) -> Dict[str, float]:
    totals = {}
    for txn in transactions:
        if txn["type"] == "debit":
            key = CAT_TO_EXPENSE.get(txn["category"], "other_expenses")
            totals[key] = totals.get(key, 0) + txn["amount"]
    return {k: round(v) for k, v in totals.items()}