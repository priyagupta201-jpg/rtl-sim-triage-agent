"""
eval_ft.py — measure base model vs LoRA-fine-tuned model on HELD-OUT test cases.

Your eval-harness instinct, applied to fine-tuning: don't eyeball one example,
score both models on a test set (including PARAPHRASED lines the base model
hasn't seen) and compare accuracy.
"""

from mlx_lm import load, generate

BASE = "mlx-community/Qwen2.5-0.5B-Instruct-4bit"
ADAPTER = "adapters"

CATEGORIES = ["COMPILE", "ASSERTION", "SCOREBOARD", "X_PROPAGATION", "TIMEOUT", "PASS"]

INSTRUCTION = (
    "Classify this VCS regression log line into exactly one category "
    "(COMPILE, ASSERTION, SCOREBOARD, X_PROPAGATION, TIMEOUT, PASS). "
    "Answer with only the category word.\n\n"
)

# Held-out test set — many are PARAPHRASED (no obvious keywords) on purpose.
TESTS = [
    # (log line, correct category)
    ("the simulation appears frozen and never produced an end-of-test marker", "TIMEOUT"),
    ("a control register came up unknown and never resolved to 0 or 1", "X_PROPAGATION"),
    ("the predicted value and the observed value diverge for that transaction", "SCOREBOARD"),
    ("the build aborted before any simulation cycles ran", "COMPILE"),
    ("a property the designer specified was violated mid-run", "ASSERTION"),
    ("everything checked out, zero errors, run finished normally", "PASS"),
    ("Error-[SE] Syntax error: \"rtl/alu.sv\", 90: token is ';'", "COMPILE"),
    ("UVM_FATAL [TIMEOUT] deadlock: req asserted, ack never returned", "TIMEOUT"),
    ("RTL_X_CHECK rtl/ctrl_fsm.sv(73): signal 'grant' is X after reset", "X_PROPAGATION"),
    ("UVM_ERROR [MISMATCH] result exp=0x00ff got=0x00fe", "SCOREBOARD"),
    ("\"Assertion no_overflow_chk\" failed at time 1450", "ASSERTION"),
    ("All 64 transactions matched. UVM_ERROR:0 UVM_FATAL:0", "PASS"),
]


def predict(model, tokenizer, line):
    """Ask the model to classify one line; return the category it picked."""
    messages = [{"role": "user", "content": INSTRUCTION + line}]
    prompt = tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, tokenize=False
    )
    out = generate(model, tokenizer, prompt=prompt, max_tokens=10, verbose=False)
    out_upper = out.upper()
    # find which category word the model produced (first one wins)
    for cat in CATEGORIES:
        if cat in out_upper:
            return cat
    return "?(" + out.strip()[:20] + ")"


def score(model, tokenizer, label):
    correct = 0
    print(f"\n===== {label} =====")
    for line, truth in TESTS:
        pred = predict(model, tokenizer, line)
        ok = pred == truth
        correct += ok
        mark = "OK " if ok else "XX "
        print(f"  {mark} got={pred:<16} truth={truth:<16} | {line[:45]}")
    print(f"  Accuracy: {correct}/{len(TESTS)} ({correct/len(TESTS)*100:.0f}%)")
    return correct


if __name__ == "__main__":
    print("Loading BASE model...")
    m, t = load(BASE)
    base_correct = score(m, t, "BASE (no fine-tuning)")

    print("\nLoading FINE-TUNED model (base + LoRA adapter)...")
    m2, t2 = load(BASE, adapter_path=ADAPTER)
    ft_correct = score(m2, t2, "FINE-TUNED (LoRA adapter)")

    print("\n" + "=" * 50)
    print(f"BASE:       {base_correct}/{len(TESTS)}")
    print(f"FINE-TUNED: {ft_correct}/{len(TESTS)}")
    print("=" * 50)
