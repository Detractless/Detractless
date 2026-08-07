# Dictation cleanup — what we tested and what we learned

A running record of the on-device "clean up my dictation" model exploration, so we don't relearn
this later. Detailed per-model reports live alongside this file (see "Detailed reports" at the end).

## The goal and the hard constraint

Take raw speech-to-text (run-ons, fillers, false starts, spoken self-corrections, no punctuation) and
return clean text, **on-device**, fast, faithful. The binding constraint is the **runtime**: the app
runs models via a bundled **llama.cpp `llama-server`**, which only runs **decoder-only GGUF** models.
That single fact decides most of what follows.

## Models tested (summary)

| Model | Arch | Runs on our llama-server? | Result |
|---|---|---|---|
| flowscribe-qwen2.5-0.5b | decoder-only GGUF | ✅ yes | Works, but hallucinated on "meta" inputs at default temp; fixed by temp 0.2. Trained on SHORT text only. |
| vennify/t5-base-grammar-correction | T5 encoder-decoder | ❌ no | **Rejected.** Loops on single words ("plan"→"Plan B. Plan B…"), 512-token cap truncates long dictations, needs a new engine. |
| grammarly/coedit-large | T5 encoder-decoder | ❌ no | Better than t5-base (safe on fragments, better grammar), but **CC-BY-NC (non-commercial)**, 512-cap, and 3–4 min latency on long inputs. Not shippable. |
| **LFM2-700M (Q8) + JSON + system prompt** | decoder-only GGUF | ✅ yes | **Best result.** Runs in-app, handles long inputs, fast, faithful. See "The winning config". |

## KEY LEARNINGS (the reusable stuff)

### 1. JSON structured output (schema-constrained decoding) — the big one
You can give the model a **JSON schema** (e.g. `{"cleaned_text": "string"}`) and the decoder is
*physically constrained* so it can only emit output matching that schema. LM Studio exposes this;
`llama-server` supports it via `response_format: {type: "json_schema", ...}`.

- **What it fixes:** output-format consistency (guaranteed parseable) and — huge — it **kills the
  chatty preamble**. Plain LFM2 answered fragments with "The number 24 is correct. If you meant…";
  with the schema it just returned "24". No room for the model to ramble.
- **What it does NOT fix:** the *meaning*. The schema constrains the form, not the content — the model
  can still write an answer or an expanded essay *inside* the field. That needs a system prompt (below).
- **Reliability caveat:** on a small (700M) model, ~1 in 18 responses came back as malformed JSON.
  Always keep a parse-failure fallback (retry, or fall back to the raw text).

### 2. A system prompt is required (not just the user "Fix grammar:" line)
Using only `"Fix grammar: <text>"` with no system prompt, LFM2 rambled on fragments and, on long
inputs, rewrote them into structured essays (headings, bullet points, invented content). Adding a
firm **edit-only system prompt** ("You are a cleanup tool, not an assistant. Do not answer, explain,
add structure, or expand. Return only the cleaned text.") removed both failures. Word counts before vs
after the system prompt on the long inputs went from *expanding into essays* to *modest cleanup*
(323→251, 375→254 words).

### 3. Temperature matters a lot
`llama-server` defaults to temp 0.8. On a small model that causes wandering and hallucination (our
early flowscribe cleanup invented a bulleted list). **Temp 0.2** fixed the consistency and most of the
hallucination. Always set it explicitly.

### 4. Architecture decides runnability
Decoder-only (LFM2, Qwen, Llama, SmolLM) → runs on our `llama-server` as GGUF. Encoder-decoder
(T5, BART, flan-T5, CoEdIT) → does NOT; it would need a whole separate ONNX seq2seq engine. Most
*dedicated grammar-correction* models are encoder-decoder, which is why they keep hitting this wall.

### 5. Short fragments and long inputs are the stress tests
- **Fragments** (1–3 words): small models either chat about them or loop. Schema + system prompt fix it.
  (The user's actual "single word gets capitalized" complaint is separate — that capital comes from the
  ASR; no cleanup model lowercases it, so it still needs a tiny deterministic rule.)
- **Long inputs** (300–480 words): encoder-decoders truncate at 512 tokens; LLMs handle the length but
  may **over-condense** (LFM2-700M summarized a 482-word input down to 179, dropping points). Watch this.

### 6. Model license vs dataset license are different
`grammarly/coedit-large` (model) is **CC-BY-NC** (non-commercial — can't ship, even "per individual"
if the work is for the business). But `grammarly/coedit` (dataset) is **Apache-2.0** — so we can train
our OWN model on that data commercially. Don't confuse the two. (And never rename/obscure a model to
dodge its license — that's infringement.)

## The winning config (so far)

**LFM2-700M (Q8 GGUF) + JSON schema (`{cleaned_text}`) + edit-only system prompt + temp 0.2**, run on
the bundled `llama-server`.
- Runs in-app (decoder-only GGUF), handles long dictations (no 512 cap), fast (fragments ~1–2 s, long
  ~13–20 s), faithful and clean on the large majority of inputs.
- **No fine-tuning required** — this is an off-the-shelf model + prompt + schema.

### Remaining issues to solve before shipping
1. Very-long inputs over-condense (drop content). Mitigations to try: a bigger small model
   (LFM2.5-1.2B), a firmer "preserve every point, do not summarize" instruction, or chunking.
2. JSON parse reliability (~1/18 failed on 700M) — needs the parse-fail fallback (the app's
   `llm_client` already has this pattern).
3. Minor quirks: `24` → "twenty-four" (number direction), a stray `[insert screenshot link]` artifact.

## The fine-tune / dataset path (optional, later)
If off-the-shelf isn't good enough, train our own decoder-only model:
- **Data:** the Apache-2.0 **CoEdIT dataset** (69k editing pairs) + our own dictations, targets produced
  by a strong teacher model under the edit-only teacher prompt (see `docs/`), fidelity-filtered.
- **Base:** a permissive decoder-only model (Qwen2.5-0.5B / LFM2). Runs on our stack, no 512 cap.
- Needs a GPU (Colab/cloud) for training; inference stays local.

## Detailed reports
- `docs/cleanup-bakeoff-results.md` — original flowscribe-family bake-off.
- `docs/t5-grammar-eval.md`, `docs/coedit-eval.md` — the encoder-decoder grammar models.
- `docs/small-grammar-models-research.md` — survey of dedicated GEC models + the runtime wall.
- `docs/flowscribe-retrain-plan.md` — training-our-own plan.
- Raw eval outputs: `scratchpad/results.json` (coedit), `results_t5.json`, `lfm2_results.json`
  (plain vs JSON), `lfm2_sys_results.json` (JSON + system prompt).
