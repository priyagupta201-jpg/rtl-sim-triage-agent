"""
eval_triage.py — a TESTBENCH for the agent (lesson #1).

You would never sign off RTL without a regression suite scoring it against
expected results. An LLM agent is no different: before you trust it overnight,
or before you change a prompt / swap a model, you score it against a GOLDEN KEY
(golden.json) and look at the numbers.

This is the single most important habit to carry from verification into AI:
  the agent is a DUT; golden.json is your expected-value file; this is the
  scoreboard. "I improved the prompt" means nothing until accuracy says so.

Run:
    .venv/bin/python eval_triage.py
    .venv/bin/python eval_triage.py --model llama3.1:8b   # A/B a different brain
"""

import argparse
import json
import os
import sys

from triage_lib import triage, CATEGORIES, MODEL

ROOT = os.path.dirname(os.path.abspath(__file__))
GOLDEN_PATH = os.path.join(ROOT, "golden.json")

# ANSI colors for a readable scoreboard.
GRN, RED, YEL, DIM, BOLD, RST = (
    "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[1m", "\033[0m",
)


def load_golden():
    with open(GOLDEN_PATH) as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("_")}


def score(findings, golden):
    """Compare agent findings against the golden key. Returns a result dict."""
    by_file = {f["filename"]: f for f in findings}
    rows, correct = [], 0
    # Defect-routing metrics a verification lead actually cares about:
    false_flags = 0   # called a PASSING test a failure (noise -> wasted triage)
    missed = 0        # called a FAILING test a pass (escaped bug -> dangerous)

    for fname, truth in sorted(golden.items()):
        got = by_file.get(fname)
        got_cat = got["category"] if got else "<MISSING>"
        ok = got_cat == truth["category"]
        correct += ok

        if not ok:
            truth_is_pass = truth["category"] == "PASS"
            got_is_pass = got_cat == "PASS"
            if got_is_pass and not truth_is_pass:
                missed += 1
            elif truth_is_pass and not got_is_pass:
                false_flags += 1

        rows.append({
            "file": fname,
            "expected": truth["category"],
            "got": got_cat,
            "ok": ok,
            "confidence": got["confidence"] if got else "-",
        })

    n = len(golden)
    return {
        "rows": rows,
        "correct": correct,
        "total": n,
        "accuracy": correct / n if n else 0.0,
        "false_flags": false_flags,
        "missed": missed,
    }


def report(result, model):
    print(f"\n{BOLD}══ Triage eval — model '{model}' ══{RST}\n")
    print(f"  {'LOG':<24}{'EXPECTED':<16}{'GOT':<16}{'CONF':<8}")
    print(f"  {'─'*22:<24}{'─'*14:<16}{'─'*14:<16}{'─'*6:<8}")
    for r in result["rows"]:
        mark = f"{GRN}✓{RST}" if r["ok"] else f"{RED}✗{RST}"
        got_col = (GRN if r["ok"] else RED) + r["got"] + RST
        # pad accounting for invisible color codes
        pad = 16 + len(GRN) + len(RST)
        print(f"  {r['file']:<24}{r['expected']:<16}{got_col:<{pad}}{DIM}{r['confidence']}{RST}  {mark}")

    acc = result["accuracy"]
    acc_col = GRN if acc == 1.0 else (YEL if acc >= 0.7 else RED)
    print(f"\n  Accuracy:     {acc_col}{result['correct']}/{result['total']}  ({acc*100:.0f}%){RST}")
    # The two asymmetric errors — missed is worse than a false flag.
    mf = f"{RED}{result['missed']}{RST}" if result["missed"] else f"{GRN}0{RST}"
    ff = f"{YEL}{result['false_flags']}{RST}" if result["false_flags"] else f"{GRN}0{RST}"
    print(f"  Missed fails: {mf}   {DIM}(failing test called PASS — escaped bug, the dangerous error){RST}")
    print(f"  False flags:  {ff}   {DIM}(passing test called a failure — wasted triage){RST}\n")
    return acc == 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=MODEL, help="ollama model to evaluate")
    args = ap.parse_args()

    golden = load_golden()
    print(f"{DIM}Running agent over {len(golden)} logs on '{args.model}'… (local model, ~30-90s){RST}")
    findings = triage(model=args.model)
    result = score(findings, golden)
    passed = report(result, args.model)
    sys.exit(0 if passed else 1)   # exit code so CI / a loop can gate on it


if __name__ == "__main__":
    main()
