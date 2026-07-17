# LESSONS.md — What to do correctly

Companion to MISTAKES.md. Where MISTAKES.md documents what went wrong,
this file states the directives — positive rules for a cold reader setting up
or extending this pipeline. Each entry is grounded in measured results.

---

## L-01 · Decompose by model strength: route each slot to the model that actually wins it

Sub-2B models are not weaker versions of larger models — they have sharp capability
cliffs that shift by task:

- **Purpose classification**: Gemma4 E2B is the only model in this project to achieve
  21/21 on the validation set's action-required emails (password reset, verify identity,
  assessment required). Qwen3 1.7B caps at 17/21 on those exact categories regardless
  of prompt — it's a ceiling, not a prompt problem. Assign purpose to the strongest
  available model.
- **Stage-1 free summarization**: Gemma4 E2B for quality; Falconsai T5-60M (CPU)
  for the compress stage. These are complementary — Gemma comprehends, Falconsai
  condenses. Swapping them produces worse results (065 Falconsai-only: summary 20→16
  on validation; body facts drift toward echo on transactional emails).
- **Entity extraction**: GLiNER small (166M, CPU, in-process) matches Gemma's
  10/10 train / 21/21 validation at ~1/30 the compute cost. Use the right tool
  for the task; generative listing is not inherently better.
- **Sender type**: code rules (noreply/footer heuristics) short-circuit before any
  model call for the majority of emails. Spend model budget only where rules fail.

The champion (076) is a three-specialist stack precisely because no single model
dominates all four slots.

---

## L-02 · Make cheating structurally impossible, not just discouraged

The most durable quality fix in this project was architectural, not prompt-based.
When Qwen3 was subject-echoing (70% echo rate, 30% genuine summaries), no prompt
change fixed it reliably. The fix was two-stage: summarize the email freely in
stage-1, then compress that summary in stage-2 without the email in context.

Once the email is absent from stage-2, echoing the subject is impossible — the
model cannot copy what it cannot see. This is the difference between "telling the
model not to cheat" (unreliable at ≤2B) and making the cheat path architecturally
unavailable (always reliable).

Apply this principle whenever you catch a model exploiting a shortcut: redesign the
input, not the instruction. Other examples from this project:
- Entity hallucination: literal-substring verification against the source email
  makes hallucinated entities fail automatically, before any model sees the output.
- Subject-echo gate (≥70% overlap → fail) makes a specific failure mode detectable
  by the scorer, not just by a human reader.

---

## L-03 · Use temp 0 for all extraction and classification tasks on this hardware

Validated across every model tested:
- Gemma4 E2B: temp 0 = 84/84; vendor temp 1.0 = 79/84. **−5 points.**
- Qwen3 1.7B: temp 0 = 73/84; vendor temp 0.7 = 70/84. **−3 points.**
- Gemma4 E2B: 4/4 identical validation runs at temp 0 — noise ≈ zero, any
  ≥1-point move in a scored experiment is real signal, not variance.

Vendor sampling recommendations target open-ended chat, not closed-set
classification or constrained-format extraction. Do not inherit them without
measuring. Set `"temperature": 0` in every slot's config; use `"seed"` + fixed
params only when deliberately testing non-zero temp, and document the result.

---

## L-04 · Use pointer-NER (GLiNER) over generative NER for entity extraction

GLiNER is a bidirectional encoder (BERT-style) that classifies spans against
free-text label descriptions at inference time. It does not generate tokens — it
points to spans that already exist in the source text. Consequences:

- **No hallucination by construction**: it can only return substrings that appear in
  the input. Combine with the existing literal-substring verification for defense-
  in-depth, but the architectural guarantee is already there.
- **Open-vocabulary labels**: labels are strings passed at call time — "person",
  "company", "organization", "product", "device", "online community or group". No
  retraining to add or remove a label type.
- **CPU-feasible at production throughput**: gliner_small-v2.1 (166M params) runs
  at ~0.44–0.65s/email on CPU with paragraph chunking, vs Gemma's ~2–4s of GPU
  decode for the same slot. Frees iGPU entirely for comprehension tasks.
- **Label descriptions, not category names**: "online community or group" (not
  "group") correctly captures Discord servers (confidence 0.71). "service" (too broad)
  was capturing generic product names. The description is the model's anchor — write
  it to describe exactly the span type you want, not a category you'd use in code.

Rules derived from GLiNER integration (066–074):
- Threshold 0.3→0.45: free quality gain — junk entities are low-confidence.
- Footer-zone exclusion (last 25% of text): eliminates address-family noise for free.
- Near-dup merge: requires the mutual-twin tie-break (equal norms keep the fuller
  form) or twins delete each other.
- Paragraph chunking (~1200 chars, merged spans): handles BERT's 512-token window
  without losing cross-paragraph entities.
- Sender-from-header rule: inject the FROM display name as a code-derived entity.
  This covers the single most common miss (sender org) for free, regardless of model.

Classic BERT-NER (dslim/bert-base-NER) is **not** a suitable alternative: its fixed
PER/ORG/LOC/MISC schema has no product class, it is case-sensitive, and ALL-CAPS
marketing headers break its capitalization features. Ruled out.

---

## L-05 · Use frozen configs + a held-out set + blind data as the evaluation method

Three distinct evaluation instruments, each catching what the others miss:

**Frozen configs** (one directory = one immutable experiment):
- Once a config directory is scored, never modify it. If you want to try a change,
  create a new numbered config directory. This guarantees that every score in the
  history is reproducible and comparable.
- The pass cache (`pass_cache.db`) stores model responses keyed by config + prompt
  hash. A frozen config is reproducible even without re-running the model.

**The held-out validation set** (`validation_ids.json`, 22 emails, pinned before
any model ran against it):
- Drafted gold labels from email text only, before seeing any model output.
- Stratified to include categories absent from the training set: security alerts,
  password resets, financial alerts, real deadlines, onboarding, confirmations,
  ToS updates, spam.
- Use this set to compare config candidates. Stop making champion-selection decisions
  against it after ~5–8 rounds (see M-11); by that point it is partially spent.

**Blind data** (fresh, never-benchmarked emails run end-to-end):
- This is the only instrument that finds bugs the benchmark set cannot expose by
  construction (the benchmark has no single-line-collapsed emails; it has no Faire
  invoices; it has no Sparkles marketing blasts).
- Run at least one full blind-email pass before every "ship" decision.
- The blind-data tally for this project: 31 fresh emails → 3 real defects, all
  invisible to the 100%-scoring benchmark. Budget time for this; it always pays.

The three instruments are not interchangeable. Each catches a different failure class.

---

## L-06 · Fix cosmetics in render, not in prompts

When the rendered output has a style defect — awkward phrasing, redundant "the email",
wrong connective — fix it in `render.py` with deterministic string operations, not by
issuing a new prompt config.

This is a hard rule because:
- Any stage-1 prompt change, even cosmetically motivated, shifts the model's attention
  distribution and changes *which facts* appear in the output. This was confirmed three
  independent times (configs 071, 072, 025). The keyword scorer cannot detect these
  content shifts — only a reading audit can.
- `render.py` changes are deterministic: the same clause always produces the same
  rendering. A prompt change introduces model-sampling variance in the content.
- The graft-fix logic already handles the primary structural challenge: Falconsai
  outputs full sentences, not noun phrases, so `render.py` detects finite-verb
  clauses and routes them to "that ..." complements rather than "about ..." prepositional
  attachment. New rendering edge cases belong here.

Current render capabilities: meta-email colon rule, multi-sentence = sentential
detection, possessive-safe capitalization (`re.sub(r"'s$", "")`, not `rstrip`),
article insertion, graft-fix verb detection. Extend this layer before touching prompts.

---

## L-07 · Validate assumptions with real data before trusting them

Several project decisions that seemed obviously correct turned out to be wrong when
measured:

| Assumption | Result when tested |
|---|---|
| Vendor temp (Gemma 1.0, Qwen 0.7) performs better than greedy | Both worse (M-09) |
| Flash-attn speeds up iGPU inference | Slightly negative (M-10) |
| More parallel slots = faster batch | 6/8 slots slower than 4; compute-bound (M-10) |
| Within-email slot parallelism saves wall time | 1.05× only — total work constant (M-10) |
| ONNX is a free GLiNER speedup | At least one report: 50% *slower* than native (ner_research.md) |
| The benchmark score reflects generalization | 100% benchmark, 3 defects in 31 blind emails (M-07) |
| Qwen3's informs-collapse is a sampling artifact | Purpose unchanged at temp 0 vs 0.7 — capability ceiling (M-09) |
| `/v1/models` = server is ready | No: model still loading when endpoint returns 200 (M-05) |

The pattern: things that sound obviously correct in ML lore are frequently wrong
for a specific hardware/model/task combination. State the assumption explicitly,
design the cheapest possible test, measure it, and record the result regardless
of direction. The falsified experiments are as valuable as the confirmed ones
(see EXPERIMENTS.md for the full config history).

---

## L-08 · Rule ORDER and structural completeness matter more than vocabulary in prompts

From the purpose prompt iteration (prompt_lab/LOG.md, v1–v12):

- The baseline prompt at v2 (018, 9/10) had all the right words. It was still getting
  the Elicit retention email wrong because the discount/promo rule appeared *before*
  the decision/response rule — so "Still want our emails?" triggered the promo path
  first.
- v4 (10/10) kept the baseline's vocabulary almost verbatim; it added only the asks
  rule *before* the promo rule, plus the `[MARKETING:…]` tag-ignore instruction.
- v10 (10/10, shipped) is 11 words shorter than the baseline with the miss fixed.
- Every attempt below ~120 words that dropped either (a) the "sender ___s" framing
  per label, (b) the asks label's 2–3 concrete examples, or (c) the correct rule
  order collapsed back to 5–7/10.
- The generic short control (37 words, no ordering, no tag note) scored 5/10 —
  identical to no prompt engineering at all.

**The lever is rule order and structural completeness, not vocabulary choice.**
When a prompt fails, audit the rule ordering before rewording. When a prompt works,
understand *why* — is it the words, or the structure? (In this case it was the
structure. The model's own elicited vocabulary, used in v11, scored 6/10.)

---

## L-09 · The "2–4 sentences" instruction in stage-1 is load-bearing

Config 056/057 tested a minimal "Summarize:" stage-1 prompt to probe whether the
instruction detail was necessary. Result:

- 056 (Gemma, bare "Summarize:"): −1 summary, +50% wall time.
- 057 (Qwen3, bare "Summarize:"): tie score, +103% wall time.

Why: "Summarize:" triggers the model's native register — a formatted markdown
mini-document (headers, bullets) written to the token cap and truncated mid-word.
The "2–4 sentences" instruction suppresses the document reflex, bounds output length
(which directly controls speed), and ensures the output ends cleanly for stage-2.

Instruction-minimalism has a floor. The 2–4 sentences bound is not filler —
it is the stage-1 prompt's single most important functional element. Do not remove
or weaken it in future prompt revisions without re-scoring.

---

## L-10 · Batch across emails; do not parallelize within a single email on shared iGPU

Two distinct parallelism concepts apply to this pipeline:

**Batch parallelism (across different emails)** — effective. Four parallel slots
(`--parallel 4`) amortize weight reads during decode across different emails.
This is the source of the 19.5s/email batch throughput on the champion config
(vs ~38s sequential single-email latency). Keep it.

**Within-email slot parallelism** (purpose + clause + entities fired concurrently
for one email) — measured at 38.1s → 36.4s (1.05×). Not worth the complexity.
On a compute-bound shared iGPU, firing multiple slots concurrently just shares
the same ALUs — total work is constant, scheduling overhead eats the gain.

**The actual speed levers on this hardware:**
1. Reduce token counts (200→120 stage-1 tokens: −30% wall, zero quality cost).
2. Reduce decode budget (entities 96→64 tokens: free, identical scores).
3. Use CPU for tasks that don't need GPU (GLiNER entities, Falconsai compress).
4. Code short-circuits (noreply/footer rules) before any model call.
