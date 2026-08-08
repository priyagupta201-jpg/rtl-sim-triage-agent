"""
triage_agent.py — A VCS regression-log triage agent.

This is the smallest *real* agent that demonstrates the whole pattern the
job posting is asking about. Read it top to bottom — every concept maps to
something in the "autonomous verification pipeline" they want to build:

    reason  -> Claude decides what to look at next
    act     -> Claude calls a TOOL (list_logs / read_log)
    observe -> we run the tool, hand the result back
    repeat  -> until Claude has triaged every failure and stops

The "design" and "regression" are synthetic (see gen_logs.py), but the
agent logic is identical to what you'd point at a real regression dir.

Usage:
    python gen_logs.py        # once, to create logs/
    python triage_agent.py
"""

import json
import os

import anthropic

# --- The model. Opus 4.8 is Anthropic's most capable model. ----------------
# Note: adaptive thinking is on; on Opus 4.8 you do NOT pass budget_tokens.
MODEL = "claude-opus-4-8"

LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")


# ===========================================================================
# 1. THE TOOLS
# ---------------------------------------------------------------------------
# An LLM can't touch your filesystem. We give it TOOLS: typed functions it
# can ask us to run. Each tool has a JSON schema describing its inputs so
# Claude knows how to call it. THIS is the core primitive of agentic AI.
# ===========================================================================

TOOLS = [
    {
        "name": "list_logs",
        "description": (
            "List the regression log filenames available to triage. "
            "Call this first to discover what failed overnight."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "read_log",
        "description": (
            "Read the full contents of one regression log by filename. "
            "Use this to inspect a test's compile/elaboration/simulation output."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Log filename, e.g. 'tc_alu_smoke.log'",
                }
            },
            "required": ["filename"],
        },
    },
]


# --- The actual implementations the harness (us) runs. ---------------------
def list_logs():
    return "\n".join(sorted(os.listdir(LOGS_DIR)))


def read_log(filename):
    # Guard against path traversal — the agent only ever names a basename.
    safe = os.path.basename(filename)
    path = os.path.join(LOGS_DIR, safe)
    if not os.path.isfile(path):
        return f"ERROR: no such log '{safe}'. Call list_logs to see valid names."
    with open(path) as f:
        return f.read()


def run_tool(name, tool_input):
    """Dispatch a tool_use request to the real Python function."""
    if name == "list_logs":
        return list_logs()
    if name == "read_log":
        return read_log(tool_input["filename"])
    return f"ERROR: unknown tool '{name}'"


# ===========================================================================
# 2. THE SYSTEM PROMPT
# ---------------------------------------------------------------------------
# This is the agent's "job description" + the verification domain knowledge
# YOU bring. It's big and stable, so we mark it with cache_control: across
# runs/turns the cached prefix is served at ~0.1x cost. (Prompt caching.)
# ===========================================================================

SYSTEM_PROMPT = """\
You are a senior RTL verification engineer triaging an overnight VCS \
regression. You are precise, never invent details not present in a log, \
and you classify each failing test so an engineer can route it fast.

Failure taxonomy — classify every NON-passing test into exactly one:
  COMPILE        - syntax/elaboration error; simulation never started
                   (look for: Error-[SE], "syntax error", make Error)
  ASSERTION      - a SystemVerilog Assertion (SVA) fired
                   (look for: "Assertion ... failed", "assert failed")
  SCOREBOARD     - data mismatch reported by the testbench/scoreboard
                   (look for: UVM_ERROR [MISMATCH], exp= vs got=)
  X_PROPAGATION  - unknown (X) values, often after reset
                   (look for: RTL_X_CHECK, [X_PROP], signal is X)
  TIMEOUT        - simulation hung / global timeout; no natural $finish
                   (look for: [TIMEOUT], deadlock, "did not complete")
  OTHER          - a real failure that fits none of the above

A test PASSED if it shows "TEST PASSED" or UVM_ERROR:0 and UVM_FATAL:0 with
a natural $finish. Do not flag passing tests.

Your workflow:
  1. list_logs to see everything.
  2. read_log on each one.
  3. For each FAILING test, give: filename, category, the single most likely
     root cause in one sentence, the key evidence line from the log, and a
     confidence (high/medium/low).

When you have triaged every log, output a final summary as a Markdown table
sorted by category, then STOP (do not call more tools).
"""


# ===========================================================================
# 3. THE AGENT LOOP
# ---------------------------------------------------------------------------
# This is the reason->act->observe->repeat loop. We keep calling the API,
# running any tools Claude requests, and feeding results back, until Claude
# stops asking for tools (stop_reason == "end_turn").
# ===========================================================================

def main():
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the env

    # The conversation. The API is stateless — we resend the full history
    # every turn. Claude's tool_use blocks and our tool_result blocks all
    # accumulate here.
    messages = [
        {
            "role": "user",
            "content": "Triage tonight's regression. Tell me what failed and why.",
        }
    ]

    turn = 0
    while True:
        turn += 1
        response = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            thinking={"type": "adaptive"},
            # cache the big stable system prompt (prefix) across turns:
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=TOOLS,
            messages=messages,
        )

        # Show any text Claude emitted this turn (its reasoning-out-loud).
        for block in response.content:
            if block.type == "text":
                print(f"\n\033[36m[agent]\033[0m {block.text}")

        # If Claude isn't asking for a tool, it's done.
        if response.stop_reason != "tool_use":
            break

        # Append Claude's turn (must include the tool_use blocks verbatim).
        messages.append({"role": "assistant", "content": response.content})

        # Run every tool Claude requested and collect the results.
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"\033[33m[tool ]\033[0m {block.name}({json.dumps(block.input)})")
                result = run_tool(block.name, block.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,  # MUST match the tool_use id
                        "content": result,
                    }
                )

        # Hand the observations back as the next user turn.
        messages.append({"role": "user", "content": tool_results})

    # --- A peek at the economics, so you build cost intuition. ------------
    u = response.usage
    print("\n" + "=" * 60)
    print(f"Turns: {turn}")
    print(f"Last-call tokens  in={u.input_tokens}  out={u.output_tokens}")
    print(
        f"Cache  write={getattr(u, 'cache_creation_input_tokens', 0)}  "
        f"read={getattr(u, 'cache_read_input_tokens', 0)}"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
