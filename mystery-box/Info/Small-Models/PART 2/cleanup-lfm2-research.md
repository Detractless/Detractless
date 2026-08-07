# Research: `vasanth009/LC-lfm2.5-350m` for Dictation Cleanup

**Date:** 2026-08-06
**Purpose:** Evaluate whether this Hugging Face model fits a "clean up voice dictation" post-processing step in DW Bridges Dictation (Handy fork, Tauri 2.x + Rust + React).
**Model page:** https://huggingface.co/vasanth009/LC-lfm2.5-350m

> This is a research/assessment document only. No application code was modified.

---

## TL;DR

This model is **surprisingly well-targeted** for exactly this use case — its stated purpose is on-device voice-dictation cleanup that also honors spoken self-corrections. However, it ships **only in safetensors/MLX format** (no GGUF, no ONNX), is quantized for **Apple Silicon (MLX)**, and is an **obscure personal upload with 0 likes** and a small self-reported eval. Using it on Windows/CPU would require **re-converting the base + adapter to GGUF** and adding a **completely new LLM runtime** (llama.cpp / a Rust crate), since the app's existing GGUF engine is a *speech* engine (whisper.cpp), not an LLM text generator. It is worth prototyping, but treat it as an experiment, not a proven component.

---

## 1. What is it

- **Base model:** `LiquidAI/LFM2.5-350M-Base` — part of Liquid AI's **LFM2 / Liquid Foundation Model 2.5** family (~350M parameters). LFM2 is a hybrid **convolution + attention** architecture (10 conv blocks + 6 attention blocks = 16 layers), purpose-built by **Liquid AI** for fast on-device/edge inference.
  - Base: https://huggingface.co/LiquidAI/LFM2.5-350M
- **This fine-tune (`LC-lfm2.5-350m` by user `vasanth009`):** A LoRA fine-tune for **voice-dictation cleanup**, derived from `juanquivilla/sotto-cleanup-lfm25-350m`, then quantized (the card references MLX 5-bit).
- **Stated purpose (verbatim from the model card):**
  > "A small, fast **on-device voice-dictation cleanup** model: it turns messy spoken transcripts into clean written text, and — unlike most cleanup models — it **honors spoken self-corrections**."
- **What "LC" likely means:** Not explicitly defined on the card. Given the lineage (`sotto-cleanup`) and stated task, it most plausibly stands for **"cleanup"** (transcript/language cleanup) — *not* "letter correction." This is an inference, not documented.
- **Training details (per card):** LoRA, 8 layers, 600 iterations, LR 5e-6. Trained on LLM-generated input/output pairs with held-out leakage prevention (0/94 topic overlap with the eval set).

**Verdict on #1:** This is not a random general model — its author explicitly built and named it for dictation cleanup. That is a strong point in its favor.

## 2. Task fit

- **Yes, it is a text-to-text model:** raw transcript string in → cleaned text out. The card's own example:
  ```
  Input:  "set the oven to three fifty no wait three seventy five for the lasagna"
  Output: (expected) "Set the oven to 375 for the lasagna."
  ```
  The prompt format is a simple `### Input:\n{raw}\n\n### Output:\n` completion template.
- **It is specifically designed for ASR/dictation cleanup**, including the differentiator of honoring self-corrections ("no wait, make it X"). This is exactly the described post-processing goal (grammar, punctuation, capitalization, filler removal, self-correction resolution).
- **Documented vs guessed:** The *task* is well-documented on the card. What is *not* well-established is real-world robustness across accents, domains, and languages — the only evidence is a 94-item self-reported eval (see §5). It is a 350M model, so it will be far weaker than cloud LLMs at edge cases.

## 3. Formats & runtime

- **Files provided (this repo):** `model.safetensors` (~244 MB), `tokenizer.json`, `config.json`, `chat_template.jinja`, `generation_config.json`, and a `lora-adapter/` directory. **Format = safetensors only, oriented toward MLX (Apple Silicon).**
- **No GGUF. No ONNX.** So neither of the app's existing engines can load it as-is:
  - `transcribe-cpp` = whisper.cpp-based, **audio→text**, GGUF — cannot run a text LLM.
  - `transcribe-rs` = ONNX ASR — cannot run this model (no ONNX export, and it's not an ASR model).
- **Does LFM2 have GGUF/llama.cpp support?** **Yes.** LFM2 (`lfm2` architecture) is supported in `llama.cpp` (`convert_hf_to_gguf.py --outtype bf16`), and Liquid AI itself publishes **official GGUF builds**, e.g. `LiquidAI/LFM2-350M-GGUF` and larger. So the *architecture* runs in llama.cpp — but **this specific fine-tune has not been converted to GGUF**; someone would have to do that (merge LoRA into base, then convert + quantize).
- **What running it on Windows (no admin, possibly no GPU) requires — a SEPARATE new runtime:**
  - Option A: bundle **llama.cpp** (or `llama-server`) and shell out / FFI to it with a GGUF build of the merged model.
  - Option B: add a Rust crate — **`llama-cpp-2`** (llama.cpp bindings, GGUF, CPU-friendly, matches the app's existing C++ FFI style), or **`mistral.rs`**, or **`candle`** (pure-Rust; LFM2 support is less certain).
  - MLX (`mlx_lm`) as shown in the card's example is **Apple-only** and irrelevant on Windows.
  - Practical recommendation: `llama-cpp-2` + a GGUF quant (Q4_K_M/Q5) is the most realistic path, CPU-only, no admin, no GPU required.

## 4. Size, speed, license

- **Parameters:** Base is ~**350M**. (One HF-rendered metadata field showed "66.5M" — that most likely reflects LoRA/adapter param count or a metadata artifact, not the deployable model; the safetensors size is consistent with a quantized 350M model. Treat 350M as the real footprint.)
- **Download size:** ~**244 MB** for the quantized safetensors; a GGUF Q4/Q5 build would be roughly **200–260 MB**. Small enough to bundle or download on first use.
- **Latency:** Card claims **~50–100 ms per utterance on Apple Silicon**. On a mid-range Windows **CPU** with a Q4 GGUF, expect a short paragraph to clean up in roughly **~0.3–2 s** (order-of-magnitude estimate; a 350M model is fast on CPU but not instant, and depends on token count and thread count). Acceptable for a post-dictation step, but not zero-cost — it adds latency after transcription.
- **Quantization options:** Currently MLX 5-bit only. Via llama.cpp you can produce the usual GGUF tiers (Q4_K_M, Q5_K_M, Q8, BF16).
- **License:** **`lfm-open`** (LFM Open License v1.0), inherited from the LFM2 base.
  - Based on Apache 2.0, royalty-free, allows use/modify/distribute/derivatives.
  - **Commercial-use restriction:** free commercial use is limited to companies with **annual revenue under $10M USD**; above that you must obtain a commercial license from Liquid AI (sales@liquid.ai).
  - License text: https://huggingface.co/LiquidAI/LFM2.5-350M/blob/main/LICENSE and https://www.liquid.ai/lfm-license
  - **Flag:** This is **not** a pure permissive license. If DW Bridges is (or becomes) a commercial product from a company over the $10M threshold, a commercial license is required. This must be reviewed before shipping.

## 5. Quality evidence

- **Community signal is weak:** ~**358 downloads** last month, **0 likes**, no community discussions or reviews visible. It is an **obscure personal upload**, not a vetted or popular model.
- **Only evidence is the author's own small eval** (94-item held-out set):
  - Course-correction: 13/16 (base 10/16)
  - Light cleanup: 12/12 (tied with base)
  - Preserve / anti-over-edit: 7/8 (base 6/8)
- **No independent benchmarks, no third-party validation, no leaderboard presence.** The eval is self-reported and tiny. The anti-over-edit ("preserve") metric is encouraging because the biggest risk of LLM cleanup is *changing the user's actual words*, but 7/8 on 8 items is not statistically meaningful.
- **Maturity assessment:** Early/experimental. Reasonable design intent, minimal proof.

## 6. Alternatives

If pursuing local transcript cleanup, safer or comparable bets include: **Liquid AI's own official GGUF models** (`LiquidAI/LFM2-350M-GGUF`, `LFM2-700M`, `LFM2-1.2B`) prompted for cleanup — well-maintained and llama.cpp-ready out of the box; small **instruction-tuned models** like **Qwen2.5-0.5B/1.5B-Instruct** or **SmolLM2-360M/1.7B-Instruct** (all have GGUF, strong community support, permissive-ish licenses) with a cleanup prompt; or, for a narrower/safer scope, dedicated **punctuation-restoration / capitalization models** (e.g. `oliverguhr/fullstop-punctuation-multilang-large`, or `deepmultilingualpunctuation`) which restore punctuation/casing **without an LLM rewriting the words** — lower hallucination risk, though they don't remove fillers or resolve self-corrections. For this specific "honor self-corrections" behavior, `LC-lfm2.5-350m` (or its `sotto-cleanup` parent) is actually one of the few purpose-built options.

## 7. Integration verdict

**Difficulty: Moderate.** The hard part is not the model file (small) but that it needs an **entirely new LLM inference runtime** in the app. The current backend has two ASR engines; neither can run a text LLM. Realistic path:

1. Merge the LoRA into the LFM2.5-350M base and convert to **GGUF** (llama.cpp `convert_hf_to_gguf.py`), quantize to Q4/Q5.
2. Add a Rust LLM runtime — **`llama-cpp-2`** is the best fit (GGUF, CPU-only, no admin/GPU, mirrors the existing whisper.cpp FFI pattern).
3. Wire an optional post-transcription step: raw text → `### Input/### Output` prompt → cleaned text, behind a user toggle, greedy decoding (temp 0) to minimize drift.

**Main risks:**
- **Hallucination / word-changing** — the #1 danger for dictation; an LLM can silently alter meaning, numbers, or names. Must be opt-in, temp 0, ideally with an easy "show raw" / undo.
- **Latency** — adds a generation pass after every dictation (~sub-second to a couple seconds on CPU).
- **License** — LFM Open License commercial threshold ($10M revenue) must be cleared for commercial distribution.
- **Maturity** — obscure model, tiny self-eval, no community validation; quality on real diverse dictation is unproven.
- **New dependency footprint** — bundling a second native inference stack (llama.cpp) increases build complexity and binary size.

**Is it worth pursuing?** As an **optional, experimental feature: yes, prototype it** — the task fit is unusually good and the model is tiny/fast. But **do not build directly on this exact obscure upload** for a shipping feature. Prototype with it (or its `sotto-cleanup` parent) to validate the UX, and for production strongly consider the **official `LiquidAI/LFM2-350M-GGUF`** (or a punctuation-restoration model for a lower-risk, non-rewriting version). Whatever the choice, the real engineering cost is the **new llama.cpp/`llama-cpp-2` runtime**, which is reusable regardless of which small model wins.

---

## Sources

- Model card: https://huggingface.co/vasanth009/LC-lfm2.5-350m
- Base model: https://huggingface.co/LiquidAI/LFM2.5-350M
- Official LFM2-350M GGUF: https://huggingface.co/LiquidAI/LFM2-350M-GGUF
- LFM2 llama.cpp architecture support issue: https://github.com/ggml-org/llama.cpp/issues/22287
- LFM Open License: https://www.liquid.ai/lfm-license and https://huggingface.co/LiquidAI/LFM2.5-350M/blob/main/LICENSE
- Liquid AI LFM2.5 background: https://venturebeat.com/technology/liquid-ais-smallest-model-yet-lfm2-5-230m-beats-models-4x-its-size-at-data-extraction-can-run-anywhere
- LFM2 release overview: https://www.therobotreport.com/liquid-ai-releases-on-device-foundation-model-lfm2/
