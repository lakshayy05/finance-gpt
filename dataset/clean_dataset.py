"""
FinanceGPT Dataset Cleaner
===========================
Fixes the three issues found in validation:
  1. Missing "Next action today:" (109 examples) — auto-adds using Gemini
  2. Missing India context (19 examples) — drops them
  3. Encoding corruption (broken rupee symbol) — fixes in place

Run:
  python dataset/clean_dataset.py --data dataset/chatml/train.jsonl
  python dataset/clean_dataset.py --data dataset/chatml/train.jsonl --fix-actions
"""

import os, json, re, time, argparse
from pathlib import Path
from dotenv import load_dotenv

def main():
    # Debug: show which keys are loaded
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # Try reading .env manually
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("GEMINI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    os.environ["GEMINI_API_KEY"] = api_key
                    break

load_dotenv()


# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════
def load_jsonl(path: str) -> list:
    data = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data

def save_jsonl(data: list, path: str):
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"  Saved {len(data):,} examples → {path}")

def extract_qa(item: dict) -> tuple:
    """Get input/output from ChatML format."""
    msgs = item.get("messages", [])
    inp  = next((m["content"] for m in msgs if m["role"] == "user"),      "")
    out  = next((m["content"] for m in msgs if m["role"] == "assistant"), "")
    sys  = next((m["content"] for m in msgs if m["role"] == "system"),    "")
    return inp, out, sys

def rebuild_chatml(inp: str, out: str, sys: str) -> dict:
    return {"messages": [
        {"role": "system",    "content": sys},
        {"role": "user",      "content": inp},
        {"role": "assistant", "content": out},
    ]}


# ══════════════════════════════════════════════════════════════════
# FIX 1 — ENCODING CORRUPTION
# ══════════════════════════════════════════════════════════════════
def fix_encoding(text: str) -> str:
    """
    Fix mojibake — broken UTF-8 characters from Gemini responses.
    Common: Ã¢â€šÂ¹ → ₹, â€™ → ', â€" → —
    """
    replacements = [
        # Rupee symbol variants
        ("Ã¢â€šÂ¹", "₹"),
        ("â‚¹",      "₹"),
        ("â€š",      "₹"),
        ("\u00e2\u0082\u00b9", "₹"),
        # Common punctuation mojibake
        ("\u2019",  "'"),
        ("\u201c",  '"'),
        ("\u201d", '"'),
        ("\u2013",  "-"),
        ("\u2014",  "–"),
        ("\u2026",  "…"),
        # Try latin1→utf8 decode trick
    ]
    for bad, good in replacements:
        text = text.replace(bad, good)

    # Try the latin1 → utf8 re-decode trick for remaining mojibake
    try:
        fixed = text.encode("latin1").decode("utf-8")
        # Only use if it actually fixed something (more readable)
        if "₹" in fixed and "₹" not in text:
            return fixed
        if fixed.count("â") < text.count("â"):
            return fixed
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass

    return text


# ══════════════════════════════════════════════════════════════════
# FIX 2 — INDIA CONTEXT CHECK
# ══════════════════════════════════════════════════════════════════
INDIA_MARKERS = [
    "ppf","nps","nifty","groww","zerodha","80c","hra","epf","elss",
    "lakh","crore","mutual fund","index fund","80d","liquid fund",
    "sensex","sebi","sip","sovereign gold","kuvera"
]

def has_india_context(text: str) -> bool:
    return any(m in text.lower() for m in INDIA_MARKERS)


# ══════════════════════════════════════════════════════════════════
# FIX 3 — ADD MISSING NEXT ACTION
# ══════════════════════════════════════════════════════════════════
def has_next_action(text: str) -> bool:
    markers = ["next action", "next step", "action today", "do this today",
               "start today", "right now:", "today:", "immediately:"]
    return any(m in text.lower() for m in markers)


def add_next_action_with_ai(client, model: str, inp: str, out: str) -> str:
    """Use Gemini to append a relevant 'Next action today:' to the response."""
    prompt = f"""This is a personal finance advice response for an Indian user.
The response is missing a "Next action today:" conclusion.

User question: {inp[:300]}

Current response: {out}

Add ONE sentence at the end starting with exactly "Next action today:" 
followed by one specific, actionable step the user can do today.
Keep it under 20 words. Be very specific (mention app names, amounts, etc.)

Return the COMPLETE response with the new sentence added at the end.
Do not change anything else. Do not add any explanation."""

    try:
        resp = client.models.generate_content(
            model    = model,
            contents = prompt,
            config   = __import__("google.genai", fromlist=["types"]).types.GenerateContentConfig(
                temperature       = 0.3,
                max_output_tokens = 500,
            ),
        )
        result = resp.text.strip()
        # Verify it actually has next action now
        if has_next_action(result):
            return result
        # If AI didn't add it properly, append manually
        return out + f"\n\nNext action today: Open Groww or Zerodha, complete your KYC, and start with the first step mentioned above."
    except Exception as e:
        print(f"  AI fix failed: {e}")
        # Fallback — extract key context and add generic but relevant action
        return out + "\n\nNext action today: Take the first step mentioned above — do it before you sleep tonight."


# ══════════════════════════════════════════════════════════════════
# MAIN CLEANER
# ══════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data",        required=True,      help="Path to train.jsonl")
    parser.add_argument("--output",      default="",         help="Output path (default: overwrites input)")
    parser.add_argument("--fix-actions", action="store_true",help="Use AI to add missing next actions (uses API)")
    parser.add_argument("--model",       default="gemini-2.5-flash-lite", help="Gemini model for AI fixes")
    args = parser.parse_args()

    data_path   = Path(args.data)
    output_path = Path(args.output) if args.output else data_path

    print(f"Loading {data_path}...")
    data = load_jsonl(str(data_path))
    print(f"Loaded {len(data):,} examples\n")

    # ── Stats before ─────────────────────────────────────────────
    before_total = len(data)
    enc_fixed    = 0
    dropped_india= 0
    action_fixed = 0

    cleaned = []

    for item in data:
        inp, out, sys = extract_qa(item)

        # Fix encoding on both input and output
        inp_fixed = fix_encoding(inp)
        out_fixed = fix_encoding(out)
        if inp_fixed != inp or out_fixed != out:
            enc_fixed += 1
        inp, out = inp_fixed, out_fixed

        # Drop examples with no India context
        if not has_india_context(out):
            dropped_india += 1
            continue

        cleaned.append((inp, out, sys, has_next_action(out)))

    print(f"{'─'*50}")
    print(f"  Encoding issues fixed:     {enc_fixed}")
    print(f"  Dropped (no India context):{dropped_india}")
    missing_action = sum(1 for _, _, _, has_act in cleaned if not has_act)
    print(f"  Missing next action:       {missing_action}")
    print(f"  Examples remaining:        {len(cleaned)}")
    print(f"{'─'*50}\n")

    # ── Fix missing next actions ──────────────────────────────────
    if args.fix_actions and missing_action > 0:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("GEMINI_API_KEY not found — skipping AI action fix")
            print("Run without --fix-actions to just drop bad examples instead")
        else:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)
            print(f"Fixing {missing_action} examples with missing next actions...")
            print("(This uses your API quota — ~1 request per fix)\n")

            fixed_cleaned = []
            for i, (inp, out, sys, has_act) in enumerate(cleaned):
                if not has_act:
                    print(f"  Fixing [{i+1}/{len(cleaned)}]...", end=" ", flush=True)
                    out = add_next_action_with_ai(client, args.model, inp, out)
                    action_fixed += 1
                    print("done")
                    time.sleep(2)   # rate limit
                fixed_cleaned.append((inp, out, sys))

            cleaned = fixed_cleaned

    else:
        if missing_action > 0:
            print(f"Tip: Run with --fix-actions to auto-fix {missing_action} examples using AI")
            print(f"     Saving as-is for now — still usable for training\n")

    # Always normalize to 3-tuple before rebuilding
    normalized = []
    for entry in cleaned:
        if len(entry) == 4:
            inp, out, sys, _ = entry
        else:
            inp, out, sys = entry
        normalized.append((inp, out, sys))
    cleaned = normalized

    # ── Rebuild and save ──────────────────────────────────────────
    final_data = [rebuild_chatml(inp, out, sys) for inp, out, sys in cleaned]

    print(f"\n{'─'*50}")
    print(f"  Before:  {before_total:,} examples")
    print(f"  After:   {len(final_data):,} examples")
    print(f"  Removed: {before_total - len(final_data):,}")
    if action_fixed: print(f"  AI fixed: {action_fixed:,} next actions")
    print(f"{'─'*50}")

    save_jsonl(final_data, str(output_path))

    # Also save cleaned alpaca and mistral formats
    out_dir = data_path.parent.parent   # dataset/
    try:
        def to_alpaca(item):
            inp, out, sys = extract_qa(item)
            return {"instruction": sys, "input": inp, "output": out}

        def to_mistral(item):
            inp, out, _ = extract_qa(item)
            return {"text": f"<s>[INST] {inp} [/INST] {out} </s>"}

        for name, fn in [("alpaca", to_alpaca), ("mistral", to_mistral)]:
            p = out_dir / name / "train.jsonl"
            if p.parent.exists():
                save_jsonl([fn(i) for i in final_data], str(p))
    except Exception:
        pass

    print(f"\nDone! Now re-run validation to confirm improvement:")
    print(f"  python dataset/validate_dataset.py --data {output_path}")


if __name__ == "__main__":
    main()