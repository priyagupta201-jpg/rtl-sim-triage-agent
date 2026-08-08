"""
triage_agent_ollama.py — The SAME triage agent, powered by a LOCAL model.

This is the Anthropic version (triage_agent.py) ported to Ollama. Compare the
two side by side: the TOOLS, the SYSTEM_PROMPT, and the reason->act->observe
loop are *identical in shape*. Only the client call changes. That's the whole
point — the agentic pattern is portable; the "brain" behind it is swappable.

Why this matters for EDA: this runs entirely on your Mac. No data leaves the
machine — which is the model you'd need for real, confidential Synopsys logs.

Prereqs:
    brew install ollama && brew services start ollama
    ollama pull qwen2.5:7b
    .venv/bin/pip install ollama

Usage:
    .venv/bin/python gen_logs.py            # once, to create logs/
    .venv/bin/python triage_agent_ollama.py
"""

import json
import os

import ollama

# A local, tool-capable model running on your machine (not in a datacenter).
MODEL = "qwen2.5:7b"

LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")


# ===========================================================================
# 1. THE TOOLS  (Ollama uses OpenAI-style tool schemas — note the wrapping
#    "type"/"function" envelope vs. Anthropic's flatter shape. The inner JSON
#    schema is the same idea.)
# ===========================================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_logs",
            "description": (
                "List the regression log filenames available to triage. "
                "Call this first to discover what failed overnight."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_log",
            "description": (
                "Read the full contents of one regression log by filename. "
                "Use this to inspect a test's compile/elaboration/sim output."
            ),
            "parameters": {
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
    },
]


# --- Tool implementations (identical to the Anthropic version). ------------
def list_logs():
    return "\n".join(sorted(os.listdir(LOGS_DIR)))


def read_log(filename):
    safe = os.path.basename(filename)
    path = os.path.join(LOGS_DIR, safe)
    if not os.path.isfile(path):
        return f"ERROR: no such log '{safe}'. Call list_logs to see valid names."
    with open(path) as f:
        return f.read()


def run_tool(name, args):
    if name == "list_logs":
        return list_logs()
    if name == "read_log":
        return read_log(args.get("filename", ""))
    return f"ERROR: unknown tool '{name}'"


# ===========================================================================
# 2. THE SYSTEM PROMPT  (verbatim from the Anthropic version — your domain
#    knowledge doesn't change just because the model did.)
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
# 3. THE AGENT LOOP  (same reason->act->observe->repeat; Ollama message
#    bookkeeping differs slightly from Anthropic's.)
# ===========================================================================

def main():
    # Ollama keeps the system prompt as a normal "system" message.
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "Triage tonight's regression. Tell me what failed and why.",
        },
    ]

    # --- COMPLETENESS TRACKING (the harness fix) --------------------------
    # Our CODE knows the ground truth: every log must be read before the
    # agent is allowed to declare itself done. We don't trust the model to
    # remember this — we enforce it.
    all_logs = set(os.listdir(LOGS_DIR))
    read_logs = set()          # filled in as read_log() is actually called
    nudges_used = 0
    MAX_NUDGES = 5             # don't nag forever if the model keeps stalling

    max_turns = 30  # safety cap — local models can loop; always bound the loop
    for turn in range(1, max_turns + 1):
        response = ollama.chat(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            options={"temperature": 0},  # deterministic-ish; good for triage
        )
        msg = response["message"]

        # Show any text the model emitted.
        if msg.get("content"):
            print(f"\n\033[36m[agent]\033[0m {msg['content']}")

        # Append the assistant turn (with its tool_calls, if any).
        messages.append(msg)

        tool_calls = msg.get("tool_calls") or []

        if not tool_calls:
            # The model THINKS it's done. But does the harness agree?
            unread = sorted(all_logs - read_logs)
            if unread and nudges_used < MAX_NUDGES:
                # Coverage isn't real yet — push it to finish the job.
                nudges_used += 1
                print(
                    f"\033[35m[harness]\033[0m incomplete: {len(unread)} log(s) "
                    f"not yet read -> nudging the model to continue."
                )
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "You have NOT triaged every log yet. Still unread: "
                            + ", ".join(unread)
                            + ". Call read_log on each of these and triage them. "
                            "Do not produce the final summary until all logs are read."
                        ),
                    }
                )
                continue  # loop again — the model gets another turn
            # Coverage is real (or we've nudged enough). Accept the stop.
            print("\n" + "=" * 60)
            print(f"Done in {turn} turn(s) on local model '{MODEL}'.")
            print(f"Logs read: {len(read_logs)}/{len(all_logs)}")
            print("=" * 60)
            return

        # Run each requested tool and feed the result back as a 'tool' message.
        for call in tool_calls:
            name = call["function"]["name"]
            args = call["function"]["arguments"]  # already a dict in ollama
            if isinstance(args, str):
                args = json.loads(args)
            print(f"\033[33m[tool ]\033[0m {name}({json.dumps(args)})")
            result = run_tool(name, args)
            # Record coverage when a log is successfully read.
            if name == "read_log" and not result.startswith("ERROR"):
                read_logs.add(os.path.basename(args.get("filename", "")))
            messages.append(
                {"role": "tool", "name": name, "content": result}
            )

    print(f"\n[!] Hit the {max_turns}-turn safety cap without finishing.")


if __name__ == "__main__":
    main()
