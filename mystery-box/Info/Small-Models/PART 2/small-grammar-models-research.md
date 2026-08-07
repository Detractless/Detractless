# Small dedicated grammar-correction models for Handy dictation cleanup

Research date: 2026-08-07
Goal: find a small (<1B param) model **specifically fine-tuned for grammar / punctuation / capitalization correction** that beats `vennify/t5-base-grammar-correction` **and** fits Handy's runtime (bundled llama.cpp `llama-server`, decoder-only GGUF).

---

## TL;DR of the runtime wall

Handy runs models through a bundled **llama.cpp `llama-server`** which serves **decoder-only** GGUF models.

The hard, uncomfortable finding: **essentially every dedicated GEC model that is actually good is an encoder-decoder (T5/flan-T5/BART) model** — the same architecture class we already rejected. The dedicated *decoder-only* GEC finetune under 1B that would drop into our stack **does not exist off the shelf**, and the research literature says small decoder-only models are *bad* at GEC (see below). So the choice is really between:

- (A) building a new inference engine (ONNX seq2seq, or the fragile llama.cpp T5 path) to run a good encoder-decoder GEC model, or
- (B) using a **punctuation+capitalization restoration** model (BERT-style, yet another engine) that directly fixes the user's capitalization complaint but is not full grammar correction, or
- (C) accepting that a *general* small decoder-only LLM prompted for cleanup is the only thing that runs on `llama-server` today — but the user explicitly does not want a general LLM.

Details and the honest recommendation are below.

---

## Ranked shortlist

| # | Model | Params | Architecture | Runs on our `llama-server` (GGUF)? | Quality vs `t5-base-grammar` | Context | License |
|---|-------|--------|--------------|-----------------------------------|------------------------------|---------|---------|
| 1 | **pszemraj/flan-t5-large-grammar-synthesis** | ~0.78B | Encoder-decoder (flan-T5-large) | **No** — GGUF exists but runs only via `llama-cli`/llamafile T5 path, **not `llama-server`**. Otherwise needs ONNX seq2seq engine. | **Clearly better.** Purpose-built for "single-shot" multi-error correction; explicitly designed **not to alter already-correct text** (directly attacks t5-base's hallucination/looping on clean fragments). | 512 enc | Apache-2.0 / (base) |
| 2 | **grammarly/coedit-large** | ~0.77B | Encoder-decoder (flan-T5-large) | **No** — same T5 wall; no first-party GGUF. | **Better.** SOTA text-editing at its size; beats GPT-3-Edit/ChatGPT in Grammarly's evals on GEC/fluency benchmarks. Instruction-driven ("Fix grammar: …"). | 512 enc | **CC-BY-NC-4.0 (non-commercial!)** |
| 3 | **1-800-BAD-CODE/punctuation_fullstop_truecase_english** | ~few×10M (6-layer, d=512) | Encoder + token-classification heads (SentencePiece) | **No** — token-classification, needs its own ONNX runtime (different again from seq2seq). | **Different task.** Not grammar, but **directly solves the capitalization + punctuation complaint**, restores sentence boundaries, no autoregressive loop/hallucination risk, handles long input. | Long (chunked) | Apache-2.0 |
| 4 | **prithivida/grammar_error_correcter_v1 (Gramformer)** | ~0.22B | Encoder-decoder (T5-base) | **No** — T5 wall. | Roughly **peer** to t5-base (same base size/arch), not a clear win; older. | 512 enc | Apache-2.0 |
| 5 | **oliverguhr/fullstop-punctuation-multilang-large** | ~0.35B | Encoder token-classification (XLM-RoBERTa-large) | **No** — token-classification ONNX engine. | Punctuation-only (no truecasing, no grammar). Solid, widely used, but narrower than #3. | Long (chunked) | MIT |

Honorable mentions: `pszemraj/grammar-synthesis-small` (~77M, t5-small — tiny, runs cheap but weaker than large, still encoder-decoder); `grammarly/coedit-xl` (~3B, over budget); `felflare/bert-restore-punctuation` (BERT-base ~110M, punctuation restore, English, token-classification).

---

## Per-candidate assessment

**1. pszemraj/flan-t5-large-grammar-synthesis (~0.78B, flan-T5-large).** The strongest *quality* pick and the closest thing to "better than t5-base that someone actually shipped a GGUF for." Fine-tuned on a 180k-row expanded JFLEG set with the explicit design goal of correcting many errors at once *without* semantically changing text that is already correct — the exact failure mode (looping/hallucinating on clean single words) that got t5-base rejected. A first-party GGUF repo exists (Q4_K_M ~487MB up to F16 ~1.57GB) with instructions to run via llamafile / `llama-cli`. **But that is the T5 encoder-decoder code path, which `llama-server` does not serve** — so it is not a drop-in for our stack; it either needs the fragile llama.cpp T5 CLI path wired in, or a new ONNX seq2seq engine. Input is still 512 tokens (same truncation risk on ~480-word dictations — would need sentence chunking).

**2. grammarly/coedit-large (~0.77B, flan-T5-large).** Best-benchmarked dedicated editor at this size; Grammarly reports SOTA text-editing beating far larger GPT-3-Edit/ChatGPT. Instruction-tuned ("Fix grammatical errors in this sentence: …"). Two blockers: (a) **CC-BY-NC-4.0 — non-commercial**, a real problem if Handy ships commercially; (b) same encoder-decoder runtime wall, no first-party GGUF. Great quality, wrong license + wrong architecture for us.

**3. 1-800-BAD-CODE/punctuation_fullstop_truecase_english (~tens of M).** Not a grammar model — it does **punctuation restoration + true-casing (capitalization) + sentence segmentation** in one pass on lower-cased unpunctuated text. This is the single most *targeted* fix for the user's stated capitalization pain, and by design it neither force-capitalizes randomly nor autoregressively loops (it's per-token classification, deterministic). Handles long input via chunking, so no 512-word truncation. Cost: it's a token-classification model needing its own small ONNX runtime + SentencePiece — a third integration style, but a much lighter/lower-risk one than an autoregressive seq2seq decoder.

**4. Gramformer / prithivida/grammar_error_correcter_v1 (~0.22B, T5-base).** Same base size and architecture as the rejected t5-base; realistically a lateral move, not an upgrade, and it shares the 512-token cap and encoder-decoder wall. Not worth the integration cost.

**5. oliverguhr/fullstop-punctuation-multilang-large (~0.35B, XLM-RoBERTa-large).** Popular punctuation restorer, MIT-licensed, multilingual. Restores punctuation but **not** capitalization/truecasing and not grammar, so it only partially addresses the complaint; #3 is a superset for English.

---

## Why the "decoder-only GEC finetune" sweet spot is empty

I searched specifically for small Llama/Qwen/SmolLM/Pythia models fine-tuned for GEC with GGUF builds. **None of quality surfaced.** The research is discouraging: a 2026 study evaluating small decoder-only LMs (<1B: GPT-2, GPT-2-Medium, GPT-Neo-125M, fine-tuned) on JFLEG found average F0.5 around **5**, and even Gemma-2B only reached **GLEU ~25 / F0.5 ~16 — about 3× worse than GPT-3.5** and far below the low-60s F0.5 that strong dedicated systems (and t5-base-class models) reach. The minimal-edit GEC literature that *does* work with decoder-only models uses ≥1.5B instruct models (Qwen2.5-1.5B, Llama-3.2-3B) — over our budget and general-purpose, not dedicated. Translation: **there is no small, dedicated, decoder-only GEC model that both beats t5-base and runs on `llama-server` today.**

## The llama.cpp T5 nuance (important)

llama.cpp *did* add T5 encoder-decoder support (PR #8141, merged 2024) — but it is implemented for the `llama-cli` / t5 example path, is repeatedly reported as fragile/broken across refactors (e.g. issue #12588 "T5Encoder support broken"), and **`llama-server`'s generation endpoints do not drive the encoder-decoder path.** So "there's a GGUF" does not mean "our bundled server can serve it." Running any T5 GEC model on our stack still means either (a) shelling out to a patched `llama-cli` T5 build, or (b) the ONNX seq2seq engine we already estimated as high-effort (encoder + autoregressive decoder w/ KV cache + SentencePiece).

---

## Honest bottom line

1. **Is there a dedicated grammar model that is BOTH better than t5-base AND runnable on our current `llama-server` stack? No.** Every dedicated GEC model that clearly beats t5-base (flan-t5-grammar-synthesis, CoEdIT-large) is encoder-decoder and hits the same runtime wall we already rejected. The small decoder-only GEC finetunes that *would* fit our stack don't exist off the shelf, and the ones people have trained are markedly *worse* than t5-base, not better.

2. **Effort comparison.**
   - *Run a good encoder-decoder GEC model (flan-t5-grammar-synthesis):* needs a new ONNX seq2seq engine (encoder + autoregressive decoder + KV cache + SentencePiece) **or** bundling/patching a separate `llama-cli` T5 binary alongside `llama-server`. High effort either way, and still 512-token-capped (needs chunking).
   - *Fine-tune a small decoder-only model on our existing `llama-server`:* zero new engine, but the evidence says sub-1B decoder-only GEC quality is poor unless you go to ~1.5–3B instruct models — which are (a) over the 1B budget and (b) general LLMs, which the user explicitly rejected. So this path buys runtime compatibility at the cost of the very quality/dedication we're chasing.

3. **The capitalization complaint specifically CAN be solved cheaply without full GEC.** A dedicated **punctuation+truecasing restoration** model (#3 `1-800-BAD-CODE/punctuation_fullstop_truecase_english`, or #5 `oliverguhr/fullstop`) directly fixes missing capitalization and punctuation on raw dictation, handles long input, is deterministic (no looping/hallucination), and is small. It is a *different* (token-classification / lightweight ONNX) integration than seq2seq, but a much lower-risk one, and it targets the user's actual pain more precisely than any general grammar model.

**Recommendation:** If the real complaint is "dictation comes out lowercase/unpunctuated," ship a **punctuation+capitalization restoration** model (#3) — smallest effort-to-value, no llama-server change needed for the decoding *style* (still a new but light ONNX token-classification path), and it won't hallucinate. If full grammar correction is genuinely required, the best *quality* pick is **pszemraj/flan-t5-large-grammar-synthesis**, but be clear-eyed that adopting it means owning a seq2seq inference path (ONNX or patched llama.cpp T5), plus sentence-chunking to beat the 512-token cap — i.e. the same high-effort engine work we scoped for the rejected T5, just with a genuinely better model at the end of it. There is **no** free lunch that is dedicated, sub-1B, better than t5-base, *and* a `llama-server` drop-in.

---

## Sources

- CoEdIT model card / sizes / license — https://huggingface.co/grammarly/coedit-large , https://huggingface.co/grammarly/coedit-xl-composite
- CoEdIT paper/blog (SOTA text editing) — https://www.grammarly.com/blog/engineering/coedit-text-editing/
- pszemraj flan-t5-large-grammar-synthesis — https://huggingface.co/pszemraj/flan-t5-large-grammar-synthesis
- pszemraj GGUF build — https://huggingface.co/pszemraj/flan-t5-large-grammar-synthesis-gguf
- pszemraj grammar-synthesis-small — https://huggingface.co/pszemraj/grammar-synthesis-small
- Gramformer / Gramformer overview — https://huggingface.co/prithivida/grammar_error_correcter_v1 , https://www.vennify.ai/gramformer-correct-grammar-transformer-nlp/
- 1-800-BAD-CODE punctuation+truecase (English) — https://huggingface.co/1-800-BAD-CODE/punctuation_fullstop_truecase_english
- 1-800-BAD-CODE 47-language / xlm-roberta — https://huggingface.co/1-800-BAD-CODE/xlm-roberta_punctuation_fullstop_truecase , https://github.com/1-800-BAD-CODE/punctuators
- oliverguhr fullstop punctuation — https://huggingface.co/oliverguhr/fullstop-punctuation-multilang-large
- felflare bert-restore-punctuation — https://huggingface.co/felflare/bert-restore-punctuation
- Small decoder-only LMs for GEC (poor scores) — https://arxiv.org/abs/2601.03874
- Minimal-edit GEC with decoder-only LLMs (uses ≥1.5B) — https://arxiv.org/abs/2506.13148
- llama.cpp T5 encoder-decoder support & breakage — https://github.com/ggml-org/llama.cpp/issues/5763 , https://github.com/ggml-org/llama.cpp/issues/12588
