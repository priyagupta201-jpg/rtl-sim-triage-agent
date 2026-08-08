# RTL Simulation Log Triage Agent

An **AI agent pipeline** that automatically triages chip-simulation regression failures: it retrieves relevant reference knowledge for each failure, classifies *what broke*, proposes *how to fix it*, and **grades its own accuracy** against a known-answer key — all running on a **local model** so confidential logs never leave the machine.

> **Why:** when a verification engineer has dozens of failing tests overnight, they spend hours just *categorizing* what broke before any real fixing starts. This automates that first pass to cut turnaround time.

Built by an EDA verification engineer to apply 15+ years of domain expertise to agentic AI. The logs are synthetic (no proprietary data), but the failure signatures and the engineering are real.

---

## What it demonstrates

| Capability | Where |
|---|---|
| **Agent + tool use + structured output** | `triage_agent_ollama.py`, `triage_lib.py` |
| **RAG** (retrieve → augment → generate) | `rag.py`, `kb/` |
| **Multi-agent orchestration** (triage → fix hand-off) | `fix_agent.py`, `app.py` |
| **Automated evaluation harness** (self-grading vs a golden key) | `eval_triage.py`, `golden.json` |
| **Local-first / privacy** (Ollama, nothing leaves the machine) | all of it |
| **Web app** (Streamlit demo UI) | `app.py` |

## Architecture

```
            ┌─────────────────────── app.py (Streamlit UI) ───────────────────────┐
            │                                                                       │
 a sim log ─┼─▶ RAG retrieve ─▶ Agent 1: TRIAGE ─▶ finding ─▶ Agent 2: PROPOSE FIX ─┼─▶ fix
            │   (kb/ notes)      (what broke?)     (contract)   (how to fix?)        │
            └───────────────────────────────────────────────────────────────────────┘

 eval_triage.py ─▶ runs the agent over golden.json ─▶ accuracy + missed-fail/false-flag
 (a testbench for the agent: DUT = agent, golden.json = expected results, score = scoreboard)
```

The design deliberately separates **deterministic code** (reading logs — mechanical)
from **model judgment** (classification — needs reasoning): hardcode what you can,
spend the model only on judgment.

## Files

| File | Role |
|---|---|
| `gen_logs.py` | generates 6 synthetic simulation logs (compile, scoreboard, SVA, timeout, X-prop, pass) |
| `triage_lib.py` | the triage agent as a pipeline component: schema contract + validation |
| `triage_agent_ollama.py` | the tool-use agent loop (reason→act→observe) version |
| `rag.py` | retrieval + RAG-grounded triage |
| `kb/` | knowledge base — reference notes per failure type |
| `fix_agent.py` | second agent: proposes a fix from a triage finding |
| `eval_triage.py` + `golden.json` | automated eval harness + hand-labeled answer key |
| `app.py` | Streamlit web app tying it together |

## Run it

**Prereqs:** [Ollama](https://ollama.com) running locally with a model pulled.
```bash
brew install ollama && brew services start ollama
ollama pull qwen2.5:7b
```

**The web app:**
```bash
.venv/bin/streamlit run app.py
```
Pick a log → "Triage this log" → see the retrieved reference note, the triage
verdict (Agent 1), and the proposed fix (Agent 2).

**The evaluation harness** (score the agent against the golden key):
```bash
.venv/bin/python eval_triage.py
```
Prints accuracy plus two asymmetric error counts: **missed-fails** (a failing
test called PASS — an escaped bug, the dangerous one) and **false-flags** (a
passing test flagged — wasted triage).

## The verification mindset, applied to AI

This project treats the agent like a **design under test**: you never sign off
RTL without a regression suite scoring it against expected results, so the agent
gets the same. `golden.json` is the expected-results file, `eval_triage.py` is
the scoreboard, and re-running it after any prompt or model change is regression
testing for the agent.

## Limitations & next steps

- **Unverified output** — proposes a fix but doesn't yet apply it and re-run the
  sim to confirm. The next step is closing that loop (agent proposes → tooling
  verifies).
- **Synthetic, small data** — built on 6 synthetic logs; a production version
  needs a larger, representative golden set grown from real corrected failures.
- **Keyword retrieval** — RAG uses keyword overlap; upgrading to embeddings /
  vector search would retrieve by meaning.
- **Workaround vs root-cause fixes** — proposes symptom-level fixes; identifying
  root-cause code fixes is the bigger goal.
