"""
make_ft_data.py — generate a synthetic fine-tuning dataset for VCS log triage.

Fine-tuning needs MANY (input -> desired output) examples. This builds short
'log line -> category' pairs and writes them in the chat format MLX-LM expects:
each line is {"messages": [user turn, assistant turn]}.

Output: ft_data/train.jsonl  and  ft_data/valid.jsonl
"""

import os
import json
import random

random.seed(0)   # reproducible

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ft_data")
os.makedirs(OUT_DIR, exist_ok=True)

INSTRUCTION = (
    "Classify this VCS regression log line into exactly one category "
    "(COMPILE, ASSERTION, SCOREBOARD, X_PROPAGATION, TIMEOUT, PASS). "
    "Answer with only the category word.\n\n"
)

# For each category: templates with {placeholders} we fill randomly for variety.
SIGS = {
    "COMPILE": [
        "Error-[SE] Syntax error: \"rtl/{m}.sv\", {n}: token is ';'",
        "Expected ';' before 'endmodule' in rtl/{m}.sv line {n}",
        "make: *** [compile] Error 1",
        "Error-[SE] syntax error near '{sig}'",
        "Parsing design file 'rtl/{m}.sv' ... 1 error",
    ],
    "ASSERTION": [
        "\"Assertion {sig}_chk\" failed at time {t}",
        "Error: assert failed in scope top.dut.u_{m} at time {t}",
        "SVA {sig}_property failed (File: rtl/{m}.sv Line: {n})",
        "assert failed: {sig} violated at time {t}",
    ],
    "SCOREBOARD": [
        "UVM_ERROR [MISMATCH] {sig} exp=0x{h1} got=0x{h2}",
        "scoreboard compare mismatch at txn id={n}: exp=0x{h1} got=0x{h2}",
        "UVM_ERROR uvm_test_top.env.sb [MISMATCH] result exp vs got differ",
        "data mismatch on {sig}: expected 0x{h1}, observed 0x{h2}",
    ],
    "X_PROPAGATION": [
        "RTL_X_CHECK rtl/{m}.sv({n}): signal '{sig}' is X after reset",
        "[X_PROP] {sig} propagated X to output at time {t}",
        "Warning-[STASKW_CO] $display encountered 'x' on {sig}",
        "{sig} is X after reset deasserted at time {t}",
    ],
    "TIMEOUT": [
        "[TIMEOUT] Global timeout reached (set_global_timeout). Test did not complete.",
        "UVM_FATAL [TIMEOUT] deadlock: req asserted, ack never returned",
        "simulation hung at time {t}; no natural $finish",
        "{sig} stalled, still waiting after {t} ns - global timeout",
    ],
    "PASS": [
        "UVM_INFO [TEST_DONE] *** TEST PASSED ***",
        "All {n} transactions matched. UVM_ERROR:0 UVM_FATAL:0",
        "$finish at simulation time {t}; UVM_ERROR : 0",
        "TEST PASSED - scoreboard reports all matches",
    ],
}

MODULES = ["axi_master", "alu", "sync_fifo", "ctrl_fsm", "decoder", "handshake"]
SIGNALS = ["grant", "next_state", "awvalid", "rd_en", "ack", "data_out", "result"]


def fill(tmpl):
    return tmpl.format(
        m=random.choice(MODULES),
        sig=random.choice(SIGNALS),
        n=random.randint(20, 300),
        t=random.choice([100, 1450, 5000, 100050, 5000000]),
        h1=f"{random.randint(0, 65535):04x}",
        h2=f"{random.randint(0, 65535):04x}",
    )


def make_examples(per_category):
    rows = []
    for category, templates in SIGS.items():
        for _ in range(per_category):
            line = fill(random.choice(templates))
            rows.append({
                "messages": [
                    {"role": "user", "content": INSTRUCTION + line},
                    {"role": "assistant", "content": category},
                ]
            })
    random.shuffle(rows)
    return rows


def write_jsonl(path, rows):
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    train = make_examples(per_category=30)   # 6 categories * 30 = 180 train
    valid = make_examples(per_category=6)    # 6 * 6 = 36 valid
    write_jsonl(os.path.join(OUT_DIR, "train.jsonl"), train)
    write_jsonl(os.path.join(OUT_DIR, "valid.jsonl"), valid)
    print(f"wrote {len(train)} train + {len(valid)} valid examples to {OUT_DIR}/")
    print("\nExample training row:")
    print(json.dumps(train[0], indent=2))
