"""
triage_lib.py — the triage agent, refactored into a pipeline component.

WHAT CHANGED vs. triage_agent_ollama.py, and WHY (this is lesson #0 + #2):

  * Lesson #0 — deterministic orchestration vs. model judgment.
    In the tool-use version, the MODEL decided which logs to read (and we had
    to nudge it to read them all). But "read every log in logs/" isn't a
    judgment call — it's mechanical. So we move it into CODE: read_all_logs()
    reads everything, guaranteed, no nudging. The model is now left with the
    ONE thing that actually needs reasoning: classifying each log. Hardcode
    what you can; spend the model only on judgment.

  * Lesson #2 — structured output is the contract between pipeline stages.
    The model no longer prints a Markdown table for a human. It emits JSON
    matching TRIAGE_SCHEMA, enforced by Ollama's `format=` AND re-validated in
    our own code (never trust the producer — validate the contract). The
    return value is a list[dict] the next stage can consume directly.

This module has NO print()s and NO __main__ side effects: it's a library.
triage_agent_ollama.py is still the "watch the loop" teaching script;
this is the "use it in a pipeline" version.
"""

import json
import os

import ollama

MODEL = "qwen2.5:7b"
LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")

CATEGORIES = [
    "PASS",            # test passed — explicitly modeled so we can catch false flags
    "COMPILE",
    "ASSERTION",
    "SCOREBOARD",
    "X_PROPAGATION",
    "TIMEOUT",
    "OTHER",
]

# --- THE CONTRACT ----------------------------------------------------------
# A JSON Schema describing exactly what a triage result must look like. This is
# the interface between this stage and whatever consumes it (a dashboard, a
# Jira filer, a fix-proposing agent). Ollama enforces it at generation time;
# we ALSO check it ourselves in validate() below.
TRIAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "filename":    {"type": "string"},
                    "category":    {"type": "string", "enum": CATEGORIES},
                    "root_cause":  {"type": "string"},
                    "evidence_line": {"type": "string"},
                    "confidence":  {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": ["filename", "category", "root_cause", "evidence_line", "confidence"],
            },
        }
    },
    "required": ["findings"],
}

SYSTEM_PROMPT = """\
You are a senior RTL verification engineer triaging an overnight VCS \
regression. You are precise and never invent details not present in a log.

Classify EVERY test into exactly one category:
  PASS           - the test passed; do not treat as a failure
                   (shows "TEST PASSED", or UVM_ERROR:0 and UVM_FATAL:0 with $finish)
  COMPILE        - syntax/elaboration error; sim never started
                   (Error-[SE], "syntax error", make Error)
  ASSERTION      - a SystemVerilog Assertion (SVA) fired
                   ("Assertion ... failed", "assert failed")
  SCOREBOARD     - data mismatch from the testbench/scoreboard
                   (UVM_ERROR [MISMATCH], exp= vs got=)
  X_PROPAGATION  - unknown (X) values, often after reset
                   (RTL_X_CHECK, [X_PROP], signal is X)
  TIMEOUT        - sim hung / global timeout; no natural $finish
                   ([TIMEOUT], deadlock, "did not complete")
  OTHER          - a real failure fitting none of the above

For EACH log you are given, return one finding object with: filename, category,
the single most likely root_cause in one sentence, the exact key evidence_line
copied verbatim from the log, and confidence (high/medium/low).
"""


# ===========================================================================
# DETERMINISTIC STAGE — code, not model. Guaranteed full coverage.
# ===========================================================================
def read_all_logs():
    """Return {filename: contents} for every log. The orchestration layer."""
    logs = {}
    for name in sorted(os.listdir(LOGS_DIR)):
        if name.endswith(".log"):
            with open(os.path.join(LOGS_DIR, name)) as f:
                logs[name] = f.read()
    return logs


# ===========================================================================
# CONTRACT VALIDATION — never trust the producer, even with format= set.
# ===========================================================================
def validate(obj, expected_files):
    """Raise ValueError if obj doesn't satisfy the contract. Returns findings."""
    if not isinstance(obj, dict) or "findings" not in obj:
        raise ValueError("missing top-level 'findings' array")
    findings = obj["findings"]
    if not isinstance(findings, list):
        raise ValueError("'findings' is not a list")

    seen = set()
    for i, f in enumerate(findings):
        for key in ("filename", "category", "root_cause", "evidence_line", "confidence"):
            if key not in f:
                raise ValueError(f"finding[{i}] missing '{key}'")
        if f["category"] not in CATEGORIES:
            raise ValueError(f"finding[{i}] bad category {f['category']!r}")
        if f["confidence"] not in ("high", "medium", "low"):
            raise ValueError(f"finding[{i}] bad confidence {f['confidence']!r}")
        seen.add(f["filename"])

    # Coverage check (the verification instinct): every log accounted for.
    missing = set(expected_files) - seen
    if missing:
        raise ValueError(f"no finding for: {', '.join(sorted(missing))}")
    return findings


# ===========================================================================
# MODEL JUDGMENT STAGE — the one place we actually need reasoning.
# ===========================================================================
def classify(logs, model=MODEL, max_retries=2):
    """Send all logs to the model, get back validated findings (list[dict])."""
    blob = "\n\n".join(
        f"===== {name} =====\n{content}" for name, content in logs.items()
    )
    user_msg = (
        "Triage tonight's regression. Here are all the logs:\n\n"
        + blob
        + "\n\nReturn one finding for EACH log above."
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]

    last_err = None
    for attempt in range(max_retries + 1):
        resp = ollama.chat(
            model=model,
            messages=messages,
            format=TRIAGE_SCHEMA,        # <-- structured output enforced here
            options={"temperature": 0},
        )
        raw = resp["message"]["content"]
        try:
            obj = json.loads(raw)
            return validate(obj, set(logs.keys()))
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e
            # Feed the error back and let the model repair its own output.
            messages.append({"role": "assistant", "content": raw})
            messages.append({
                "role": "user",
                "content": f"That output was invalid: {e}. Re-emit valid JSON matching the schema.",
            })
    raise RuntimeError(f"model failed to produce valid output after retries: {last_err}")


def triage(model=MODEL):
    """Full pipeline component: deterministic read -> model classify -> validated."""
    return classify(read_all_logs(), model=model)
