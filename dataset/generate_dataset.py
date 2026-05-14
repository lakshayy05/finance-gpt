"""
FinanceGPT Dataset Generator — Multi-key + Resume
===================================================
Fixes:
  1. API key rotation — add multiple keys, auto-switches when one hits limit
  2. Lenient JSON parser — fixes trailing comma errors from Gemini
  3. --start-batch — resume from any batch number

Setup:
  Add ALL your API keys to .env (one per line):
    GEMINI_API_KEY=key_from_account_1
    GEMINI_API_KEY_2=key_from_account_2
    GEMINI_API_KEY_3=key_from_account_3

  Get free keys at: https://aistudio.google.com
  Each Google account = 1 free key = 20 requests/day

Run:
  python dataset/generate_dataset.py --dry-run
  python dataset/generate_dataset.py --batches 50 --per-batch 20
  python dataset/generate_dataset.py --batches 50 --start-batch 19   # resume from batch 19
  python dataset/generate_dataset.py --batches 50 --start-batch 19 --resume  # keep existing examples too
"""

import os, json, re, time, argparse, random
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
    from google.genai import types
    GEMINI_OK = True
except ImportError:
    GEMINI_OK = False


# ══════════════════════════════════════════════════════════════════
# TOPIC BATCHES
# ══════════════════════════════════════════════════════════════════
TOPIC_BATCHES = [
    "Emergency fund building, first SIP, zero savings situation, fresh graduate finances",
    "Section 80C tax saving, ELSS vs PPF vs NPS comparison, last-minute March tax saving",
    "HRA exemption calculation, rent receipts, metro vs non-metro city rent rules",
    "Salary hike allocation, avoiding lifestyle inflation, increment investment strategy",
    "Credit card debt, personal loan EMI, repayment priority, snowball vs avalanche method",
    "Home loan planning, down payment saving, EMI affordability, Tier-2 city vs metro buying",
    "Old vs new tax regime comparison for different salary levels with real calculations",
    "SIP vs lump sum, market timing myths, Nifty 50 index fund basics for beginners",
    "Gold and silver investment, Sovereign Gold Bonds vs Gold ETF vs physical gold",
    "Budget planning, 50/30/20 rule adapted for Indian salaries and high-rent cities",
    "Swiggy Zomato OTT overspending, food budget cutting tips, subscription audit",
    "EPF VPF contribution, withdrawal rules, UAN activation, employer contribution match",
    "Term insurance coverage, health insurance, family floater vs individual plan",
    "First job financial mistakes, common money traps for freshers, avoiding EMI traps",
    "Freelancer self-employed tax filing, 44ADA presumptive scheme, advance tax payment",
    "NPS Tier 1 vs Tier 2, 80CCD extra 50k deduction on top of 80C, exit rules",
    "Mutual fund categories large cap mid cap ELSS liquid flexi cap explained simply",
    "Marriage financial planning, joint accounts, combining two incomes, wedding budget",
    "Car loan vs saving up, two-wheeler EMI decision, vehicle depreciation reality",
    "Retirement planning in mid-20s, compounding power, why starting small SIP early matters",
    "Bank FD vs debt mutual funds vs liquid funds, returns liquidity tax comparison",
    "Emergency fund placement, liquid fund vs savings account vs FD pros and cons",
    "Crypto allocation for Indians, max 5 percent rule, risk management, portfolio balance",
    "Step-up SIP increasing 10 percent annually, salary hike reinvestment strategy",
    "Annual bonus deployment, loan prepayment vs SIP vs emergency fund vs travel priority",
    "Rent vs buy decision in India, Bangalore renting vs hometown buying real analysis",
    "Side hustle income tax implications, how to declare, investing extra monthly income",
    "Goal-based investing, separate funds for vacation bike foreign trip home down payment",
    "Index funds for beginners, why avoid direct stocks, how index funds work in India",
    "Medical emergency fund vs regular emergency fund, health insurance gap coverage",
    "Supporting parents financially, sending money home while saving for own future goals",
    "CIBIL score improvement, how calculated, impact on loan interest, steps to fix it",
    "Salary structure optimisation, HRA LTA food coupons NPS employer contribution",
    "Income tax return filing, Form 16, ITR-1 for salaried employees, deadline refund",
    "Debt warning signs, when debt becomes dangerous, exit strategy for debt trap",
    "Liquid fund basics, better than savings account, T+1 redemption, low risk explained",
    "Windfall money deployment, received 1L to 5L unexpectedly, how to invest lump sum",
    "Moving cities for new job, financial checklist, rent budget reset, cost comparison",
    "Peer pressure spending, handling social expenses, destination weddings group trips",
    "Annual financial review checklist, what to review every March before tax year ends",
    "Health checkup savings vs avoiding preventive care, long-term cost of ignoring health",
    "Zero-based budgeting method, every rupee has a job, monthly reset for Indian families",
    "Fixed vs floating interest rate for home loan, which to choose in rising rate environment",
    "Dividend vs growth option in mutual funds, IDCW vs growth, tax implications India",
    "Children education planning, Sukanya Samriddhi recurring deposit ELSS for future",
    "Small cap vs large cap allocation, risk matching to age, 100 minus age rule",
    "EPF vs NPS vs PPF, which is best for long-term retirement, lock-in comparison",
    "UPI safety digital payment fraud, common scams, how to protect money online",
    "Term plan vs whole life insurance, why term is better, cost comparison with LIC",
    "Second salary spouse starts working, how to optimise combined household finances",
]

SYSTEM_INSTRUCTION = """You are FinanceGPT, a sharp personal finance coach for Indian salaried professionals aged 24-32.

PERSONALITY: Speak like a smart CA friend. Warm, direct, no jargon. Use Hinglish naturally. Never shame spending. Always encouraging.

RULES:
1. Use rupee symbol and Indian number system (lakhs crores not millions)
2. Reference user exact numbers in every calculation
3. Show step-by-step math
4. India-specific: PPF NPS ELSS 80C HRA EPF Nifty 50 Groww Zerodha liquid fund
5. Never recommend specific stocks, only index funds
6. Never claim SEBI registration
7. End EVERY response with: Next action today: [one specific step]"""


def make_prompt(topic: str, n: int) -> str:
    return f"""Generate {n} training examples for an Indian personal finance AI chatbot.

TOPIC: {topic}

Return a JSON array of exactly {n} objects. Each object has two fields only:
- "input": user message with specific rupee amounts, Indian city, job, age
- "output": FinanceGPT response, detailed and India-specific

EVERY example must follow ALL these rules:
1. Input has specific numbers: salary expenses savings in rupees
2. Output uses those exact numbers in step-by-step calculations
3. Output mentions at least 2 of: PPF NPS ELSS 80C Nifty 50 Groww Zerodha HRA EPF liquid fund index fund
4. Output is 100-200 words
5. Use different Indian cities: Mumbai Bangalore Delhi Hyderabad Pune Chennai Jaipur Kolkata
6. Different personas: ages 24-32, male and female names, varied jobs
7. Different salaries: 28000 to 150000 per month
8. Some inputs have emotion: I am stressed feel behind parents pressuring me
9. Output ends with: Next action today: followed by one specific action

IMPORTANT: Return valid JSON only. No trailing commas. No comments inside JSON.
Start with [ and end with ] only. No text before or after."""


# ══════════════════════════════════════════════════════════════════
# API KEY ROTATION
# ══════════════════════════════════════════════════════════════════
def load_api_keys() -> list:
    """Load all API keys from .env — supports up to 10 keys."""
    keys = []
    # Primary key
    k = os.getenv("GEMINI_API_KEY", "")
    if k: keys.append(k)
    # Additional keys
    for i in range(2, 11):
        k = os.getenv(f"GEMINI_API_KEY_{i}", "")
        if k: keys.append(k)
    return keys


class KeyRotator:
    """Rotates through API keys when one hits its daily limit."""
    def __init__(self, keys: list, model: str):
        self.keys        = keys
        self.model       = model
        self.current_idx = 0
        self.exhausted   = set()   # indices of keys that hit daily limit
        self.client      = self._make_client()

    def _make_client(self):
        from google import genai
        return genai.Client(api_key=self.keys[self.current_idx])

    def rotate(self) -> bool:
        """Try next available key. Returns False if all keys exhausted."""
        for i, _ in enumerate(self.keys):
            next_idx = (self.current_idx + i + 1) % len(self.keys)
            if next_idx not in self.exhausted:
                self.current_idx = next_idx
                self.client      = self._make_client()
                print(f"  Switched to API key #{self.current_idx + 1}")
                return True
        return False

    def mark_exhausted(self):
        """Mark current key as daily-limit-hit."""
        self.exhausted.add(self.current_idx)
        print(f"  Key #{self.current_idx + 1} daily limit reached. Exhausted: {len(self.exhausted)}/{len(self.keys)}")

    def all_exhausted(self) -> bool:
        return len(self.exhausted) >= len(self.keys)

    def test(self) -> bool:
        """Quick connectivity test."""
        try:
            resp = self.client.models.generate_content(
                model    = self.model,
                contents = 'Say only: OK',
                config   = types.GenerateContentConfig(max_output_tokens=5),
            )
            print(f"  Key #{self.current_idx + 1} response: {resp.text.strip()}")
            return True
        except Exception as e:
            print(f"  Key #{self.current_idx + 1} failed: {e}")
            return False


# ══════════════════════════════════════════════════════════════════
# LENIENT JSON PARSER
# ══════════════════════════════════════════════════════════════════
def fix_json(raw: str) -> str:
    """
    Fix common JSON issues from Gemini:
    - Trailing commas before } or ]
    - Single quotes instead of double quotes
    - Unescaped newlines inside strings
    """
    # Remove trailing commas before closing brackets/braces
    raw = re.sub(r',\s*([}\]])', r'\1', raw)
    # Remove trailing commas at end of lines before newline+bracket
    raw = re.sub(r',(\s*\n\s*[}\]])', r'\1', raw)
    return raw


def parse_json_lenient(raw: str) -> list:
    """Try strict parse first, then lenient fix, then manual extraction."""
    # Find JSON boundaries
    start = raw.find("[")
    end   = raw.rfind("]") + 1
    if start == -1 or end == 0:
        return []
    raw = raw[start:end]

    # Try 1: strict parse
    try:
        result = json.loads(raw)
        return result if isinstance(result, list) else []
    except json.JSONDecodeError:
        pass

    # Try 2: fix trailing commas then parse
    try:
        fixed  = fix_json(raw)
        result = json.loads(fixed)
        return result if isinstance(result, list) else []
    except json.JSONDecodeError:
        pass

    # Try 3: extract individual objects with regex
    try:
        objects = []
        # Find each {...} block
        depth = 0; start_pos = -1; in_string = False; escape = False
        for i, ch in enumerate(raw):
            if escape:
                escape = False; continue
            if ch == '\\' and in_string:
                escape = True; continue
            if ch == '"' and not escape:
                in_string = not in_string; continue
            if in_string:
                continue
            if ch == '{':
                if depth == 0: start_pos = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and start_pos != -1:
                    obj_str = raw[start_pos:i+1]
                    try:
                        obj = json.loads(fix_json(obj_str))
                        if isinstance(obj, dict): objects.append(obj)
                    except Exception:
                        pass
                    start_pos = -1
        return objects
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════
# GENERATE BATCH
# ══════════════════════════════════════════════════════════════════
def generate_batch(rotator: KeyRotator, topic: str, n: int) -> list:
    """Generate one batch, handling rate limits and key rotation."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = rotator.client.models.generate_content(
                model    = rotator.model,
                contents = make_prompt(topic, n),
                config   = types.GenerateContentConfig(
                    temperature       = 0.85,
                    max_output_tokens = 8192,
                ),
            )
            raw = response.text.strip()

            # Strip markdown fences
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            parsed = parse_json_lenient(raw)
            if parsed:
                return parsed
            else:
                print(f"  Could not parse JSON (attempt {attempt+1})")
                if attempt < max_retries - 1:
                    time.sleep(3)

        except Exception as e:
            err = str(e)
            print(f"  Error: {err[:150]}")

            is_daily_limit = "GenerateRequestsPerDay" in err or ("limit: 20" in err and "PerDay" in err)
            is_rate_limit  = "429" in err or "RESOURCE_EXHAUSTED" in err

            if is_daily_limit:
                rotator.mark_exhausted()
                if rotator.all_exhausted():
                    print("\n  All API keys have hit their daily limit.")
                    print("  Options:")
                    print("    1. Wait until tomorrow and run with --resume --start-batch <next_batch>")
                    print("    2. Add more API keys to .env as GEMINI_API_KEY_2, GEMINI_API_KEY_3 etc.")
                    return None   # None = stop generation entirely
                if rotator.rotate():
                    time.sleep(3)
                    continue  # retry with new key

            elif is_rate_limit:
                # Per-minute limit — just wait
                wait = 65
                # Try to extract actual wait time from error
                match = re.search(r'retry in (\d+)', err)
                if match: wait = int(match.group(1)) + 5
                print(f"  Per-minute rate limit — waiting {wait}s...")
                time.sleep(wait)
                continue

            else:
                print(f"  Unknown error on attempt {attempt+1}")
                if attempt < max_retries - 1:
                    time.sleep(5)

    return []


# ══════════════════════════════════════════════════════════════════
# QUALITY FILTER
# ══════════════════════════════════════════════════════════════════
INDIA_MARKERS = [
    "ppf","nps","nifty","groww","zerodha","80c","hra","epf","elss",
    "lakh","crore","mutual fund","index fund","80d","liquid fund",
    "sensex","sebi","sip","sovereign gold","kuvera"
]

def is_quality(item: dict) -> bool:
    inp = item.get("input",  "").strip()
    out = item.get("output", "").strip()
    if not inp or not out:                               return False
    if len(out.split()) < 50:                            return False
    if len(out.split()) > 400:                           return False
    if not any(c.isdigit() for c in inp + out):          return False
    if not any(m in out.lower() for m in INDIA_MARKERS): return False
    return True


# ══════════════════════════════════════════════════════════════════
# FORMATTERS
# ══════════════════════════════════════════════════════════════════
def to_chatml(item):
    return {"messages": [
        {"role": "system",    "content": SYSTEM_INSTRUCTION},
        {"role": "user",      "content": item["input"]},
        {"role": "assistant", "content": item["output"]},
    ]}

def to_alpaca(item):
    return {"instruction": SYSTEM_INSTRUCTION, "input": item["input"], "output": item["output"]}

def to_mistral(item):
    return {"text": f"<s>[INST] {item['input']} [/INST] {item['output']} </s>"}


# ══════════════════════════════════════════════════════════════════
# UTILS
# ══════════════════════════════════════════════════════════════════
def deduplicate(examples):
    seen, unique = set(), []
    for ex in examples:
        key = ex.get("input","")[:100].lower().strip()
        if key not in seen:
            seen.add(key); unique.append(ex)
    return unique

def save_jsonl(data, path):
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"  Saved {len(data):,} → {path}")

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def print_stats(examples):
    if not examples: return
    ol = [len(e.get("output","").split()) for e in examples]
    il = [len(e.get("input","").split())  for e in examples]
    kws = {
        "Tax":["80c","tax","regime","hra"],"SIP/MF":["sip","mutual fund","nifty"],
        "Emergency":["emergency","liquid fund"],"Budget":["budget","50/30"],
        "Debt":["loan","emi","debt"],"PPF/NPS":["ppf","nps","epf"],
        "Insurance":["insurance","term"],"Gold":["gold","silver","sgb"],
    }
    found = set()
    for ex in examples:
        t = (ex.get("input","") + ex.get("output","")).lower()
        for label, kw in kws.items():
            if any(k in t for k in kw): found.add(label)
    print(f"\n  Total:          {len(examples):,} examples")
    print(f"  Avg input:      {sum(il)/len(il):.0f} words")
    print(f"  Avg output:     {sum(ol)/len(ol):.0f} words")
    print(f"  Topics covered: {', '.join(sorted(found))}")


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batches",     type=int, default=50,        help="Total batches to run")
    parser.add_argument("--per-batch",   type=int, default=20,        help="Examples per batch (max 25)")
    parser.add_argument("--output",      type=str, default="dataset",  help="Output folder")
    parser.add_argument("--model", type=str, default="gemini-2.5-flash-lite", help="Model name")
    parser.add_argument("--dry-run",     action="store_true",          help="Test 1 batch only")
    parser.add_argument("--resume",      action="store_true",          help="Load existing raw_examples.json")
    parser.add_argument("--start-batch", type=int, default=1,          help="Start from this batch number (1-indexed)")
    args = parser.parse_args()

    if not GEMINI_OK:
        print("Install: pip install google-genai"); return

    # ── Load API keys ─────────────────────────────────────────────
    keys = load_api_keys()
    if not keys:
        print("No API keys found in .env")
        print("Add: GEMINI_API_KEY=your_key")
        print("Get free key at: https://aistudio.google.com"); return

    print(f"\nLoaded {len(keys)} API key(s)")

    # ── Auto-detect model ─────────────────────────────────────────
    model = args.model
    if model == "auto":
        # Try models in order of preference
        candidates = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash-lite-001",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
]
        from google import genai as _genai
        test_client = _genai.Client(api_key=keys[0])
        model = None
        print("Auto-detecting model...")
        for candidate in candidates:
            try:
                resp = test_client.models.generate_content(
                    model    = candidate,
                    contents = "Say OK",
                    config   = types.GenerateContentConfig(max_output_tokens=5),
                )
                _ = resp.text
                model = candidate
                print(f"  Using model: {model}")
                break
            except Exception as e:
                err = str(e)
                if "429" in err or "RESOURCE_EXHAUSTED" in err:
                    # Model exists but rate limited — use it anyway
                    model = candidate
                    print(f"  Using model: {model} (rate limited — will retry)")
                    break
                print(f"  {candidate}: not available")
        if not model:
            print("No working model found. Check your API key.")
            return

    # ── Init rotator ──────────────────────────────────────────────
    rotator = KeyRotator(keys, model)

    # ── Test connection ───────────────────────────────────────────
    print("\nTesting API connection...")
    if not rotator.test():
        # Try rotating to another key
        if not rotator.rotate() or not rotator.test():
            print("All keys failed. Check your .env and API access.")
            return
    print()

    # ── Setup paths ───────────────────────────────────────────────
    out_dir  = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / "raw_examples.json"

    # Load existing if resuming
    all_examples = []
    if args.resume and raw_path.exists():
        with open(raw_path) as f:
            all_examples = json.load(f)
        print(f"Resumed: loaded {len(all_examples):,} existing examples")

    # ── Settings ──────────────────────────────────────────────────
    batches_to_run = 1 if args.dry_run else args.batches
    per_batch      = min(args.per_batch, 25)
    start_idx      = max(0, args.start_batch - 1)   # convert to 0-indexed

    print(f"\n{'='*52}")
    print(f"  FinanceGPT Dataset Generator")
    print(f"{'='*52}")
    print(f"  Model:       {model}")
    print(f"  API keys:    {len(keys)} (auto-rotates on daily limit)")
    print(f"  Batches:     {start_idx+1} to {batches_to_run} (x{per_batch} each)")
    print(f"  Target:      ~{(batches_to_run - start_idx) * per_batch} new examples")
    print(f"  Output:      {out_dir}/")
    if args.dry_run: print(f"  Mode:        DRY RUN")
    print(f"{'='*52}\n")

    # Build topic list
    topics = []
    while len(topics) < batches_to_run:
        shuffled = TOPIC_BATCHES.copy()
        random.shuffle(shuffled)
        topics.extend(shuffled)
    topics = topics[:batches_to_run]

    # Slice to start_batch
    topics_to_run = topics[start_idx:]
    if args.dry_run:
        topics_to_run = topics_to_run[:1]

    passed_total = 0
    stop_signal  = False

    for i, topic in enumerate(tqdm(topics_to_run, desc="Generating")):
        actual_batch_num = start_idx + i + 1
        print(f"\nBatch {actual_batch_num}/{batches_to_run}: {topic[:60]}...")

        result = generate_batch(rotator, topic, per_batch)

        # None = all keys exhausted, stop everything
        if result is None:
            print("\nStopping — all API keys daily limit reached.")
            print(f"Progress saved. Tomorrow run:")
            print(f"  python dataset/generate_dataset.py --batches {batches_to_run} --start-batch {actual_batch_num} --resume")
            stop_signal = True
            break

        if not result:
            print(f"  Empty batch — skipping")
            continue

        clean  = [ex for ex in result if is_quality(ex)]
        failed = len(result) - len(clean)
        passed_total += len(clean)
        print(f"  {len(clean)}/{len(result)} passed", end="")
        if failed: print(f" ({failed} rejected)", end="")
        print()

        all_examples.extend(clean)
        save_json(all_examples, str(raw_path))   # save after every batch

        # Rate limiting: 4s between requests
        if i < len(topics_to_run) - 1:
            time.sleep(4)

    # ── Finalise ──────────────────────────────────────────────────
    print(f"\nTotal new examples: {passed_total:,}")

    before = len(all_examples)
    all_examples = deduplicate(all_examples)
    if before != len(all_examples):
        print(f"Duplicates removed: {before - len(all_examples)}")

    print(f"Total unique: {len(all_examples):,}")

    if not all_examples:
        print("No examples yet. Check errors above."); return

    print_stats(all_examples)

    # 90/10 split
    random.shuffle(all_examples)
    split     = int(len(all_examples) * 0.9)
    train_raw = all_examples[:split]
    val_raw   = all_examples[split:]
    print(f"\nSplit: {len(train_raw):,} train / {len(val_raw):,} validation")

    # Save all formats
    print("\nSaving...")
    for name, fn in [("chatml",to_chatml),("alpaca",to_alpaca),("mistral",to_mistral)]:
        d = out_dir / name
        d.mkdir(exist_ok=True)
        save_jsonl([fn(e) for e in train_raw], str(d/"train.jsonl"))
        save_jsonl([fn(e) for e in val_raw],   str(d/"val.jsonl"))

    save_json(train_raw, str(out_dir/"train_raw.json"))
    save_json(val_raw,   str(out_dir/"val_raw.json"))

    if stop_signal:
        print(f"\nPartial dataset saved ({len(all_examples):,} examples).")
        print(f"Add more API keys or wait until tomorrow, then run --resume --start-batch to continue.")
    else:
        print(f"\nDone! {len(all_examples):,} examples saved to {out_dir}/")
        print(f"Next: python dataset/validate_dataset.py --data {out_dir}/chatml/train.jsonl")


if __name__ == "__main__":
    main()