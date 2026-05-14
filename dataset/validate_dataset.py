"""
Dataset Quality Validator
==========================
Run this after generating your dataset to check quality
before spending time on QLoRA training.

Usage:
  python validate_dataset.py --data dataset/chatml/train.jsonl
"""
import json, sys, argparse
from pathlib import Path
from collections import Counter


def load_jsonl(path: str) -> list:
    data = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def extract_qa(item: dict) -> tuple:
    """Extract input/output regardless of format."""
    # ChatML format
    if "messages" in item:
        msgs  = item["messages"]
        user  = next((m["content"] for m in msgs if m["role"]=="user"), "")
        asst  = next((m["content"] for m in msgs if m["role"]=="assistant"), "")
        return user, asst
    # Alpaca format
    if "instruction" in item:
        return item.get("input",""), item.get("output","")
    # Prompt-completion
    if "prompt" in item:
        return item.get("prompt",""), item.get("completion","")
    return "", ""


def validate(data: list) -> dict:
    results = {
        "total":             len(data),
        "empty_input":       0,
        "empty_output":      0,
        "short_output":      0,   # < 40 words
        "long_output":       0,   # > 300 words
        "missing_numbers":   0,   # no ₹ or digits in output
        "missing_india":     0,   # no India-specific terms
        "missing_action":    0,   # no "next action" type ending
        "good":              0,
        "issues":            [],
    }

    india_markers = ["₹","sip","ppf","nps","nifty","groww","zerodha",
                     "80c","hra","epf","elss","lakh","crore","mutual fund",
                     "index fund","sebi","80d"]
    action_markers = ["next action","today","right now","start with",
                      "first step","open","download","activate","transfer"]

    output_lengths = []
    word_freq      = Counter()

    for i, item in enumerate(data):
        inp, out = extract_qa(item)
        issues   = []

        if not inp:
            results["empty_input"] += 1
            issues.append("empty input")

        if not out:
            results["empty_output"] += 1
            issues.append("empty output")
            continue

        words = out.split()
        output_lengths.append(len(words))
        word_freq.update(w.lower() for w in words[:5])  # track opening words

        if len(words) < 40:
            results["short_output"] += 1
            issues.append(f"short output ({len(words)} words)")

        if len(words) > 300:
            results["long_output"] += 1
            issues.append(f"long output ({len(words)} words)")

        has_numbers = any(c.isdigit() or c=="₹" for c in out)
        if not has_numbers:
            results["missing_numbers"] += 1
            issues.append("no numbers/₹ in output")

        has_india = any(m in out.lower() for m in india_markers)
        if not has_india:
            results["missing_india"] += 1
            issues.append("no India-specific terms")

        has_action = any(m in out.lower() for m in action_markers)
        if not has_action:
            results["missing_action"] += 1
            issues.append("no next action")

        if not issues:
            results["good"] += 1
        elif len(results["issues"]) < 10:  # show first 10 issues
            results["issues"].append({"index": i, "input_preview": inp[:60], "issues": issues})

    results["avg_output_words"] = sum(output_lengths)/len(output_lengths) if output_lengths else 0
    results["min_output_words"] = min(output_lengths) if output_lengths else 0
    results["max_output_words"] = max(output_lengths) if output_lengths else 0
    results["quality_score"]    = results["good"] / results["total"] * 100 if results["total"] else 0
    results["common_openers"]   = word_freq.most_common(10)

    return results


def print_report(r: dict):
    total = r["total"]
    score = r["quality_score"]
    grade = "🟢 Excellent" if score>=90 else "🟡 Good" if score>=75 else "🟠 Needs work" if score>=60 else "🔴 Poor"

    print(f"\n{'='*55}")
    print(f"  FinanceGPT Dataset Quality Report")
    print(f"{'='*55}")
    print(f"  Total examples:    {total}")
    print(f"  Quality score:     {score:.1f}% — {grade}")
    print(f"{'='*55}")
    print(f"\n📊 Output length:")
    print(f"   Average: {r['avg_output_words']:.0f} words (target: 120-200)")
    print(f"   Min:     {r['min_output_words']} words")
    print(f"   Max:     {r['max_output_words']} words")
    print(f"\n⚠️  Issues found:")
    print(f"   Empty inputs:          {r['empty_input']} ({r['empty_input']/total*100:.1f}%)")
    print(f"   Empty outputs:         {r['empty_output']} ({r['empty_output']/total*100:.1f}%)")
    print(f"   Short outputs (<40w):  {r['short_output']} ({r['short_output']/total*100:.1f}%)")
    print(f"   Long outputs (>300w):  {r['long_output']} ({r['long_output']/total*100:.1f}%)")
    print(f"   Missing ₹/numbers:     {r['missing_numbers']} ({r['missing_numbers']/total*100:.1f}%)")
    print(f"   Missing India context: {r['missing_india']} ({r['missing_india']/total*100:.1f}%)")
    print(f"   Missing next action:   {r['missing_action']} ({r['missing_action']/total*100:.1f}%)")
    print(f"\n✅ Clean examples:  {r['good']} / {total}")

    if r["issues"]:
        print(f"\n🔍 Sample issues (first {len(r['issues'])}):")
        for iss in r["issues"]:
            print(f"   [{iss['index']}] \"{iss['input_preview']}...\"")
            print(f"        Problems: {', '.join(iss['issues'])}")

    print(f"\n{'='*55}")
    if score >= 90:
        print("  ✅ Dataset looks great! Ready for QLoRA training.")
    elif score >= 75:
        print("  🟡 Dataset is good. Consider cleaning flagged examples.")
    elif score >= 60:
        print("  🟠 Dataset needs work. Re-generate flagged batches.")
    else:
        print("  🔴 Dataset quality too low. Review your GPT prompt.")
    print(f"{'='*55}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Path to train.jsonl")
    parser.add_argument("--save-report", type=str, default="", help="Save report to JSON file")
    args = parser.parse_args()

    path = Path(args.data)
    if not path.exists():
        print(f"❌ File not found: {path}")
        sys.exit(1)

    print(f"Loading {path}...")
    data = load_jsonl(str(path))
    print(f"Loaded {len(data)} examples.")

    report = validate(data)
    print_report(report)

    if args.save_report:
        report.pop("issues")  # too verbose for JSON
        with open(args.save_report, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved → {args.save_report}")


if __name__ == "__main__":
    main()