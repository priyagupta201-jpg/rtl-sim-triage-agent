# Interview Prep — VCS Triage Agent Project

A running study doc of mock-interview questions, my answers, coaching notes, and
polished "model" answers. Refresh this before interviews. (Built incrementally —
new Q&A gets appended as we practice.)

---

## The 30-second project summary (memorize the shape: WHAT → WHY → HOW)

> "It's an **AI agent pipeline** that automatically triages chip-simulation
> regression failures. **[what]** When a verification engineer has dozens of
> failing tests overnight, they spend hours just *categorizing* what broke
> before any real fixing starts — so I built a system that does that first pass
> automatically, to cut that turnaround time. **[why]** It works in three
> stages: it **retrieves** relevant reference knowledge for each failure (RAG),
> a first **agent classifies** the failure type, and a second **agent proposes
> a fix** — all on a **local model** so confidential logs never leave the
> machine. And it **grades itself** against a known-answer key so I can measure
> accuracy. **[how]**"

Four words that make an AI interviewer lean in: **RAG, multi-agent, local model,
self-evaluation.**

---

## Q1 — "Walk me through your project: what does it do and why did you build it?"

**My first answer (the gist):** Reduces turnaround time and makes verification
engineers' work easier by identifying failure categories and proposing fixes for
VCS regression failures — cutting time R&D engineers spend debugging before a
code fix is even needed.

**Coaching:**
- ✅ Strong: led with *impact/value* (turnaround time, easing engineer effort).
- ⚠️ Gap: didn't say *what it technically is* (an AI agent pipeline). For an AI
  role, front-load the technical identity in the first 20 seconds.
- ⚠️ Jargon: spell out "TAT" → "turnaround time"; give 1 line of context on what
  VCS is, for a non-EDA interviewer. Calibrate to the listener.
- Structure to use: **WHAT it is → WHY it matters → HOW it works** (see the
  30-second summary above).

---

## Questions still to practice (answer in own words, no peeking at code)

## Q2 — What makes it an "agent" rather than just calling an LLM once? What is "tool use"?

**My answer (the gist):** It's an agent because it automatically takes a log
path and classifies the failure from reference docs, with no manual
intervention — like an assistant doing that job for me.

**Coaching:**
- ⚠️ Big trap: "automated" ≠ "agent." A bash script is automated too. Don't
  define agent as "runs by itself" — an interviewer will pounce.
- ✅ Name the two real things: (1) the **model makes judgment calls** (classify
  is reasoning, not a hardcoded if-rule); (2) **tool use in a reason→act→observe
  loop** — the model can call tools (read_log/list_logs), observe results, and
  decide next steps.
- **Tool use** = giving the LLM functions it can call (it can't read files
  itself); it *asks* to call one, your code runs it and feeds the result back.
- Senior nuance to flex: project has BOTH a true agent loop
  (triage_agent_ollama.py) AND a refactored pipeline (triage_lib) where
  mechanical work is hardcoded and the model is spent only on judgment —
  "not everything needs an agent."

**Model answer:**
> "It's an agent because the **model makes the judgment calls** — classifying an
> ambiguous failure isn't a hardcoded rule, it's reasoning over evidence. In the
> tool-use version it runs a **reason→act→observe loop**: it can call tools like
> read_log to pull info, observe the result, and decide its next step, instead
> of me scripting every move. Tool use just means giving the LLM functions it
> can call, since it can't read files itself. That said, I deliberately kept the
> mechanical parts in plain code and spent the model only on the judgment part."

## Q3 — Why force JSON matching a schema instead of free text?

**My answer (the gist):** Structured format so we know which part of the result
to extract for display, and so the 2nd agent that consumes the 1st agent's
output knows which part is useful and understands its input well.

**Coaching:**
- ✅ Strong: nailed the core — structured output is a **contract** for reliable
  extraction, both for display and for feeding the next agent.
- ➕ Add the **failure mode** (interviewers want the concrete "what goes wrong"):
  with prose you'd be **fragile-parsing a paragraph** to get the category, and
  the format would vary every time — no dependable field for the next agent /
  dashboard / DB.
- ➕ Mention the **enum**: schema constrains *values*, not just shape — category
  must be one of the 7 valid labels, so the model can't invent one.
- ➕ Broaden consumers: not just agent 2 — dashboards, bug tracker (auto-file
  Jira), database, metrics ("how many TIMEOUTs this week?"). Can't count prose.

**Model answer:**
> "I force JSON to a schema so the output is a reliable **contract** — same
> fields, same place, every time. The output isn't just read by a human; it's
> consumed by the **next agent**, and could feed a dashboard, bug tracker, or
> metrics. With prose I'd be stuck **fragile-parsing a paragraph** to extract the
> category, and the format would vary each time. The schema also **constrains
> values** — category must be one of my valid labels via an enum, so the model
> can't invent one. Structure is what makes it a pipeline, not a chatbot."

## Q4 — What is RAG, and why use it when you already have a system prompt?

**My answer (the gist):** RAG = Retrieval Augmented Generation — the agent picks
up references / source of truth from a knowledge base. System prompt says how the
model behaves in general + baseline context; RAG is consulted as the latest
source for domain-specific questions when needed.

**Coaching:**
- ✅ Strong: correct definition + good system-prompt-vs-RAG distinction
  (general/baseline vs specific/current knowledge).
- ➕ Make the **mechanism** explicit: Retrieve → **Augment (insert the note INTO
  the prompt)** → Generate. "Augment" = augmenting the prompt.
- ➕ Add the **scale** argument: can't fit 500 failure playbooks + history +
  specs in a prompt (megabytes, slow, costly every call); RAG pulls only the
  relevant slice. Plus freshness: KB updates by adding a file — no code change.
- 🔧 Terminology: say "**knowledge base**" (or vector/document store), not "RAG
  dictionary."

**Model answer:**
> "RAG is Retrieval-Augmented Generation. Before the model answers, I **retrieve**
> the most relevant note from a **knowledge base**, **augment** the prompt by
> inserting it, and the model **generates** grounded in it. The system prompt is
> general, stable rules — behavior + baseline taxonomy. RAG is for specific,
> deep, or changing knowledge that can't fit in a prompt: you can't put 500
> failure playbooks plus historical bugs in every call, so RAG pulls only the
> relevant slice for this log, and updates by just adding a file. Different
> layers: prompt = the rules, RAG = the reference shelf."

## Q5 — How do the two agents hand off, and what makes it reliable?

**My answer (the gist):** Fix the output shape of agent 1 so we know what fields
it provides; agent 2 takes that input and reads the relevant information.

**Coaching:**
- ✅ Strong: got the central idea — fixed output shape (known fields) = the
  contract that lets agent 2 consume it.
- ➕ Be concrete about the **mechanism**: agent 1 **returns a dict** → code
  **passes it as an argument** (`propose_fix(finding, text)`) → agent 2
  **json.dumps it into its own prompt** as text.
- ➕ Name what **guarantees** the shape: `format=TRIAGE_SCHEMA` enforces it →
  reliable because the shape is a **contract**, not hoped-for.
- ➕ Killer analogy (use your background): "like a function signature or a
  module's **port list** — a fixed interface both sides agree on."
- ➕ Senior bonus: contract is currently **implicit** (producer guarantees,
  consumer trusts); hardening = validate agent 2's input against the same schema.

**Model answer:**
> "Agent 1 returns a **structured dict** whose shape is **guaranteed** by
> `format=TRIAGE_SCHEMA`. My orchestration code stores it and **passes it as an
> argument** into the second agent, which **dumps it into its own prompt** as
> text. It's reliable because the shape is a **contract** both agents agree on —
> like a function signature or a module's port list: a fixed interface, so the
> consumer always knows the fields. Right now that contract is implicit — the
> producer guarantees the shape, the consumer trusts it — so a hardening step is
> to validate agent 2's input against the same schema."

## Q6 (THE DIFFERENTIATOR) — How do you know the agent is correct?

**This is the question to own — slow down and nail it. Most AI candidates can
build something that produces output; few can measure correctness. You can,
because rigorous correctness IS your career. Lead with the verification mapping.**

**Model answer:**
> "I treat the agent like a **design under test**. You'd never sign off RTL
> without a regression suite scoring it against expected results — an LLM agent
> is no different. So I built an **eval harness**: a **golden answer key**
> (golden.json) with the hand-labeled correct category for every log, and the
> harness runs the agent over all of them and **scores against that key** for an
> **accuracy** number. 'I improved the prompt' means nothing until accuracy says
> so. I also don't treat all errors equally: a **missed failure** (calling a
> failing test PASS) is an **escaped bug** — the dangerous one; a **false flag**
> (passing test called a failure) just wastes triage. So I track them
> asymmetrically. And on every prompt change or model swap, I **re-run the eval
> and compare numbers** — catches regressions, lets me A/B models objectively.
> It's regression-testing discipline from verification, applied to AI."

**Short version:**
> "I score the agent against a hand-labeled golden key with an eval harness —
> accuracy plus asymmetric error tracking — and re-run it on every prompt/model
> change. Regression testing from verification, applied to AI."

**The mapping to lead with (translates AI into your home turf):**
| Verification | This project |
|---|---|
| DUT | the triage agent |
| Golden / expected results | golden.json |
| Scoreboard | eval_triage.py |
| Regression run | re-running the eval after a change |
| Coverage hole (dangerous) | missed-fail (escaped bug) |
| Redundant test (noise) | false-flag (wasted triage) |

### Q6 follow-up — "golden.json is manual effort; if you label it by hand, why need the agent at all?"
(A sharp question — great to *ask* an interviewer, and to answer crisply.)

**Answer:** The golden set is a small, **one-time labeled sample** used to
**measure** the agent — NOT the workload. The agent's real job is the
**thousands of new, UNLABELED logs** every night that nobody will hand-label.
Two different runs on different data:
- **Eval run** → agent runs on the ~30 *labeled* logs, only to compute accuracy
  / prove it works (no new value — answers already known).
- **Production run** → agent runs on ~thousands of *unlabeled* logs, doing the
  real work.

**Verification analogy (lead with this):** you write a regression suite with
expected results (a finite labeled sample) once, confirm the DUT passes, then the
chip **ships and runs billions of real cycles you never hand-checked**. You don't
verify every real input — you build confidence on a representative labeled
sample, then trust the validated design on the huge unlabeled workload.
golden.json = the regression suite; nightly logs = the chip in the field.

**Economics:** without agent = human triages all 500 failures every night
forever. With agent = label ~30 once, validate accuracy, then agent triages all
500 nightly automatically. One-time labeling cost amortized over thousands of
runs. Bonus: golden is reusable forever (regression guard on prompt/model
changes), and the agent **generalizes** to unseen logs.

**One-liner:** "The golden set is a small one-time sample to *measure* the agent,
like a regression suite. The agent's real job is the thousands of unlabeled logs
nobody will ever hand-label — same as signing off a chip on a test suite, then
trusting it on billions of real cycles."

---

# HARDER ROUND (judgment & self-awareness)

## Q7 — Limitations / where would I poke holes?

**My answer (the gist):** propose_fix only suggests RTL changes to by-pass a
failure; the real need is root-cause code-level fixes — e.g. a simulator/RTL
optimization causing a sim mismatch, where we should triage which optimization
broke it and fix the tool code.

**Coaching:**
- ✅ Real, domain-smart limitation (workaround vs root-cause; thinking from the
  VCS-R&D seat). Great as a *closer*.
- ⚠️ Q7 wants you to **enumerate several** weaknesses (breadth = self-awareness),
  not one. Also drifted toward "future enhancement" vs "current flaw."
- Lead with the strongest: **output is UNVERIFIED** — proposes a fix but nothing
  applies it + re-runs the sim to confirm → suggestion engine, not solver.
- Limitations list to rattle off: unverified output; **synthetic data** (real
  logs messier/longer/multi-failure); **tiny eval set** (6 logs, not significant);
  **single-failure assumption**; **crude keyword RAG** (can grab wrong note);
  **local 7B model ceiling**; workaround-not-root-cause (your point).

**Model answer:**
> "A few. Biggest: the output is **unverified** — it proposes a triage and fix
> but never applies it and re-runs the sim to confirm, so it's a suggestion
> engine, not a solver. Second, it's built on **synthetic logs**; real ones are
> messier and often have multiple cascading failures, while I assume one finding
> per log. Third, my **eval set is tiny** (6 logs) so accuracy isn't significant
> yet. Retrieval is just **keyword matching**, which can grab the wrong
> reference. And domain-specifically, it proposes **workaround fixes, not
> root-cause code fixes** — e.g. a simulator optimization causing a mismatch
> where the real fix is in the tool's code. That gap is where I'd go next."

## Q8 — How would you scale this to production?

**Organize by dimension (don't ramble). Dimensions:**
| Axis | Key move |
|---|---|
| Integration & volume | hook into nightly regression infra; queue + parallelize; auto-file Jira/dashboard |
| Cost & model | keep local (confidential, free/call); **tier** cheap→big model; cache repeats |
| Knowledge base | keyword → **embeddings/vector search**; assign an owner to keep current |
| Monitoring | run eval continuously; **alert on accuracy drop**; grow golden set |
| Human-in-loop | propose→approve; **route by confidence**; feed corrections back to golden |
| Robustness | validate outputs; handle huge logs (grep/chunk); retries |

**Two stand-out points:** (1) monitor accuracy over time + alert on drops (AI
silently degrades) — your regression mindset = "continuous regression testing of
the agent." (2) human corrections feed back into the golden set = a **data
flywheel / active learning** — the system measurably improves with use.

**One-liner:** "Hook into the nightly regression flow, parallelize, tier models
for cost, upgrade retrieval to embeddings, human-in-the-loop routed by
confidence — and above all continuously **monitor accuracy and alert on
regressions**, feeding human corrections back into the golden set."

## Q9 — Why a local model instead of a cloud API?

**My answer (the gist):** local = cheap + design logs stay secure (no data leaves
the machine); for low-confidence failures, escalate to a premium model (which
would be expensive for 100s of overnight failures).

**Coaching:**
- ✅ Strong: nailed security + cost + smart tiered escalation (carried the
  tiering idea from Q8 — good cross-linking).
- ➕ Make **confidentiality the headline AND a hard requirement**: real VCS logs
  can contain customers' proprietary RTL/IP; cloud API could breach contracts.
  Local = compliance need, not preference.
- ➕ Name the **trade-off explicitly**: small 7B local model is weaker than a
  frontier model → accuracy ceiling. (Plus: you manage infra. Upsides: no rate
  limits, no latency, reproducible if pinned.)
- 💡 Impressive nuance: escalating to a *cloud* premium model **reopens the
  confidentiality problem** → escalate to a bigger *local* model or send only
  sanitized data.

**Model answer:**
> "Headline reason is **confidentiality** — real VCS logs can contain customers'
> proprietary RTL and IP; a third-party API could breach contracts, so local
> (nothing leaves the machine) is often a hard requirement. It's also **free per
> call** at hundreds of failures/night, no rate limits or latency. The
> **trade-off** is quality: a small local model is weaker, so accuracy has a
> ceiling — hence **tiering**: local for the bulk, escalate low-confidence cases.
> Though escalating to a *cloud* model reintroduces the confidentiality issue, so
> ideally escalate to a bigger *local* model or send only sanitized data."

## Q10 — Hallucination / confident mistakes

**My answer (the gist):** self-verify and self-correct; if confidence is low,
escalate to a human or ask pinpointed questions instead of guessing.

**Coaching:**
- ✅ Good: self-verification, confidence-gated human escalation, "ask not guess."
- ⚠️ Self-verification is limited — a model checking itself is the SAME fallible
  model (can be confidently wrong in answer AND check).
- 🌟 Lead with **external ground-truth verification**: for a fix, **apply it and
  re-run the sim** — objective truth, not the model's opinion. This is the closed
  loop that fixes the Q7 "unverified output" weakness. Pure verification DNA:
  don't trust a claim, re-run the test.
- ➕ **Evidence-grounding (already built!):** schema forces `evidence_line` (cite
  the exact log line); prompt forbids inventing details → unsupported claims
  stand out.
- ➕ **Measure, don't eliminate:** eval tells you the error rate (e.g. 8%); set
  confidence threshold for human review; agent is **advisory, human approves,
  never auto-apply**. Design so wrong answers are caught & cheap.
- ⚠️ Caveat: self-reported confidence isn't calibrated — pair it with
  eval-measured accuracy, don't trust it alone.

**Model answer:**
> "A few layers. First, I don't trust the model's word — for a fix, the real
> check is to **apply it and re-run the sim**: objective ground truth. That
> closed loop is the strongest defense. Second, I **ground it in evidence** — the
> schema forces it to cite the exact log line and the prompt forbids inventing
> details, so unsupported claims stand out. Third, I **measure the error rate**
> with my eval, route low-confidence cases to a human, and keep the agent
> **advisory** — a human approves before any fix is applied; never auto-apply.
> I'm careful with self-reported confidence since it isn't calibrated, so I pair
> it with measured accuracy. You can't stop a model being wrong; you design so
> wrong answers are caught cheaply."

**Theme:** external verification + measurement + human gate > "trust the model to
check itself." This is your verification DNA — the most credible possible answer.

---

# CONCEPT NOTES (deep-dives)

## Prompting vs RAG vs Fine-tuning — "when would you use each?"
- **Prompting** = tell it HOW to behave (instructions/examples). Changes the input.
- **RAG** = give it WHAT to know (facts). Adds knowledge at runtime.
- **Fine-tuning** = change the model's weights so behavior/skill is internalized.
- **Order to try (cheapest first): prompt → RAG → fine-tune.**
- **Golden rule: RAG for knowledge, fine-tuning for behavior.**
- **Classic trap:** "model doesn't know our docs, should we fine-tune?" → NO,
  that's a knowledge problem → RAG. Fine-tuning is bad at facts + facts change.
- My project: used prompting (taxonomy) + RAG (kb notes), did NOT fine-tune —
  correct call (no behavior wall; fine-tuning needs data + goes stale).

## Fine-tuning / LoRA — I actually did one (hands-on)
- Ran a real LoRA fine-tune locally (MLX, Apple M5), Qwen2.5-0.5B, 180 synthetic
  log→category examples, ~2 min. Val loss 5.4→0.17.
- **0.6% trainable params** = `2.9M / 494M` — LoRA trains only a tiny adapter,
  freezes the rest. That's why it's laptop-fast (vs full fine-tuning).
- Result: base 4/12 (33%) → fine-tuned 8/12 (67%) on held-out cases.
- **Key lesson learned:** fine-tuning only learns the TRAINING DISTRIBUTION —
  both models still missed plain-English paraphrases not in the data. Fix =
  more varied data, or RAG / bigger base model. Validated with a held-out eval.

## How do you measure accuracy on FRESH (unlabeled) logs?
- **You don't — and can't.** Accuracy is measured ONLY on a labeled test set
  (golden), where a human expert created the "truth" once.
- Fresh production logs = where the agent WORKS (you act on output), not where
  it's GRADED. Two different activities on different data.
- Test-set accuracy is your ESTIMATE for production — valid if the test set is
  representative. (Same as: measure a chip on a regression suite, then trust it
  on billions of real cycles you never hand-check.)
- Monitor over time WITHOUT full labels: (1) spot-check — label a small random
  sample of real logs periodically; (2) human corrections feed back into golden
  (flywheel / regression-after-bug); (3) proxy signals (low confidence, model
  disagreement) flag likely-wrong cases.

## The confidence field — how/why
- It's a **self-reported** field the model writes (like the category) — NOT a
  calculated probability. (Rigorous alternative = token logprobs.)
- **Not calibrated** — model can say "high" and be wrong. Don't trust it alone;
  pair with eval-measured accuracy.
- **Why it exists = routing:** high-confidence → auto-process; low-confidence →
  human / escalate. You don't want "only high confidence" — you want honest
  flagging of shaky cases, because a wrong answer with fake-high confidence is
  the dangerous one.
