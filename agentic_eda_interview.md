# Agentic AI in EDA — Interview Prep (the differentiator)

Your edge: most AI candidates can't spell "constraint random"; most EDA engineers
can't explain ReAct. You sit in the intersection. This doc is the industry-level
framing on top of your project-specific Q&A in `interview_prep.md`.

The mental anchor for everything below — say this in interviews:
> "An LLM *predicts text*. An **agent** wraps that LLM in a loop where it can
>  **use tools, observe real results, and decide the next step** — so it acts on
>  the world instead of just describing it. In EDA the 'tools' are the things we
>  already have: the simulator, the waveform DB, the linter, the log files."

---

## 1. Why EDA is a strong (and hard) fit for agents

WHY IT FITS:
- EDA is **drowning in text artifacts** an LLM is good at: logs, RTL, testbenches,
  constraints (SDC), reports, waveforms-as-text, spec PDFs.
- The work is **multi-step and tool-driven** — exactly the agentic loop: run sim →
  read log → form hypothesis → check waveform → propose fix → re-run.
- There are **ground-truth oracles** to check the agent against: did the test pass?
  did coverage close? did timing meet? The tool tells you if the agent was right.

WHY IT'S HARD (say these — it shows judgment):
- **Cost of being wrong is high.** A confidently-wrong triage wastes an engineer's
  day or masks a real bug. Hallucination isn't a cute failure here.
- **Scale & determinism.** Regressions have 10k+ tests; engineers need reproducible,
  auditable results, not a model that answers differently each run.
- **Proprietary, low-public-data domain.** Little EDA training data on the internet;
  internal IP can't leave the building → pushes you toward RAG + local/on-prem models.

---

## 2. The core agentic patterns (know these by name)

| Pattern | One-line | EDA example |
|---|---|---|
| **Tool use / function calling** | LLM emits a structured call; your code runs it | "read_log(tc_fifo)", "grep_waveform(signal)" |
| **ReAct** (Reason+Act) | loop: think → act → observe → repeat | hypothesize cause → check signal → revise |
| **Reflection / self-critique** | a second pass checks the first | "does this fix actually match the failing assertion?" |
| **Planning / decomposition** | break a goal into ordered sub-tasks | "close coverage" → list holes → write tests per hole |
| **Multi-agent** | specialized agents hand off | triage-agent → fix-agent (your project!) |
| **Human-in-the-loop** | agent proposes, engineer approves | agent drafts the waiver; human signs off |

Your project already demonstrates **tool use, structured output, multi-agent handoff,
and RAG** — name them explicitly when asked.

---

## 3. Where agents actually land in a chip flow (concrete use-cases)

- **Verification / regression triage** (your project): bucket 10k failing logs,
  cluster by root cause, point to the evidence line. Highest-ROI, lowest-risk entry.
- **Debug assistant:** given a failing test + waveform, hypothesize the cause and
  the signal to inspect. Agent drives the debugger as a tool.
- **RTL / testbench generation:** draft Verilog/UVM from a spec; the *oracle* is
  "does it compile + simulate", which the agent can check itself.
- **Coverage closure:** find uncovered bins → generate targeted stimulus → re-run.
- **Constraint / SDC + timing:** explain a timing violation, propose constraint edits.
- **Lint / CDC / DRC fixing:** explain a violation in English, propose the waiver/fix.
- **Spec & docs Q&A (RAG):** "what does this register field do?" over internal docs.

Rule of thumb to state: **start where being wrong is cheap and a tool can verify the
answer** (triage, coverage) — not where a wrong answer silently ships (sign-off).

---

## 4. The architecture principle that impresses (you already live this)

> **"Hardcode what you can; spend the model only on judgment."**

In your `triage_lib.py` you moved "read every log" out of the model and into plain
code, because *which logs to read isn't a judgment call — it's mechanical*. The model
is left with the one thing that needs reasoning: classifying. Interviewers love this
because juniors make the model do everything (slow, non-deterministic, expensive).

Corollaries to drop:
- **Determinism at the edges, judgment in the middle.** Orchestration in code;
  reasoning in the LLM; validation back in code.
- **Structured output is the contract between stages** — JSON schema, validated by
  your code, so the next stage (dashboard, Jira filer) can trust it.
- **Ground every claim in a tool result** (RAG / real log line) to fight hallucination.

---

## 5. The hard problems (where senior interviews live)

- **Correctness / eval:** "How do you know it's right?" → golden set + accuracy on a
  labeled holdout; for fresh logs, agreement/confidence + spot-checks + the oracle
  (did the proposed fix make the test pass?). This is your Q6 — the differentiator.
- **Hallucination:** force the model to cite the evidence line; if it can't ground a
  claim, it must say "OTHER / low confidence" rather than invent one.
- **Trust & adoption:** engineers won't trust a black box. Show the retrieved note,
  the evidence line, the confidence — make it *auditable*. Propose, don't auto-apply.
- **Data & IP:** can't send RTL to a public API → local model (Ollama) or on-prem;
  RAG over internal KB instead of fine-tuning on secrets.
- **Scale & cost:** 10k tests → cheap deterministic pre-filter (keyword/regex) first,
  spend the LLM only on the ambiguous remainder. Cache. Batch.

---

## 6. Likely interview questions (rehearse out loud)

1. "How would you apply LLM agents to chip verification?" → use-case ladder in §3,
   starting with triage because the oracle is cheap.
2. "What's the difference between an LLM and an agent?" → the loop + tools (top anchor).
3. "Your agent proposes an RTL fix — would you let it auto-commit? Why not?" →
   human-in-the-loop; cost-of-wrong; propose+verify, never silent sign-off.
4. "How do you stop it hallucinating a root cause?" → grounding/citation + structured
   output + a low-confidence/abstain path.
5. "Why not just fine-tune a model on all our logs?" → RAG vs fine-tune tradeoff
   (your concept note): RAG for fresh/changing facts + citations; fine-tune for
   format/style. You did a LoRA so you can speak to both.
6. "How would you scale this to a nightly 10k-test regression?" → deterministic
   pre-filter → LLM on the hard tail → cluster duplicates → dashboard. (your Q8)
7. "Design an agent that closes functional coverage." → plan→decompose pattern:
   parse coverage report → identify holes → generate targeted stimulus → re-run →
   loop until closed or budget hit. Name the oracle (coverage %).

---

## 7. Three sentences that make you sound senior

- "I push determinism to the edges and reserve the model for genuine judgment."
- "Every agent claim is grounded in a tool result and structured so the next stage
   can trust it — and there's always an abstain path for low confidence."
- "In EDA the cost of a confident wrong answer is high, so I start where a tool can
   verify the agent cheaply, keep a human in the loop for sign-off, and measure
   against a golden set."
