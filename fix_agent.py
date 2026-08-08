"""
fix_agent.py — the SECOND agent. Takes a triage finding and proposes a fix.

This is multi-agent orchestration: agent 1 (triage) says WHAT broke, this
agent says HOW to fix it. They connect through the structured 'finding' dict.
Note it has its OWN role (RTL designer) and its OWN output contract (FIX_SCHEMA)
— separation of concerns: each agent is focused, so each is better.
"""

import json
import ollama

MODEL = "qwen2.5:7b"

# --- THIS AGENT'S OUTPUT CONTRACT ------------------------------------------
FIX_SCHEMA = {
    "type": "object",
    "properties": {
        "filename":         {"type": "string"},
        "fix_summary":      {"type": "string"},   # one line: what to change
        "suggested_change": {"type": "string"},   # the concrete fix / steps
        "risk":             {"type": "string", "enum": ["low", "medium", "high"]},
    },
    "required": ["filename", "fix_summary", "suggested_change", "risk"],
}

# --- THIS AGENT'S ROLE — a DIFFERENT persona than triage -------------------
SYSTEM_PROMPT = """\
You are a senior RTL designer. You are given a triaged VCS regression failure
(its category, root cause, and key evidence line) plus the raw log. Propose the
MINIMAL, safest fix.

Rules:
  - Suggest the smallest change that addresses the root cause. No rewrites.
  - Only reference signals, files, or modules that appear in the log. Never
    invent names.
  - Judge the risk of your own fix (low/medium/high) — a fix can be more
    dangerous than the bug it cures.

Return: filename, a one-line fix_summary, the concrete suggested_change, and risk.
"""


def propose_fix(finding, log_text, model=MODEL):
    """ONE triage finding + its log -> one fix proposal (dict)."""
    finding_text = json.dumps(finding)

    user_msg = (
        "The triage agent found this failure:\n" + finding_text +
        "\n\nHere is the full log:\n" + log_text +
        "\n\nPropose the minimal, safest fix."
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]

    resp = ollama.chat(model=model, messages=messages,
                       format=FIX_SCHEMA, options={"temperature": 0})
    return json.loads(resp["message"]["content"])


if __name__ == "__main__":
    # standalone test with a fake finding (like one triage would produce)
    fake = {"filename": "tc_handshake.log", "category": "TIMEOUT",
            "root_cause": "req asserted, ack never returned", "confidence": "high"}
    with open("logs/tc_handshake.log") as f:
        log = f.read()
    print(propose_fix(fake, log))
