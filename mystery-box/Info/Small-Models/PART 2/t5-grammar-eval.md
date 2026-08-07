# Evaluation: `vennify/t5-base-grammar-correction` as dictation-cleanup model

**Date:** 2026-08-07
**Model:** `vennify/t5-base-grammar-correction` (T5-base, encoder-decoder, ~220M params, fp32 ~892 MB)
**Scope:** Research + local evaluation only. No app code touched. Model deleted after eval.
**Test data:** User's real dictations (`dictation_all.json`, 173 entries), run locally via HuggingFace `transformers` on CPU.

## TL;DR verdict: **DO NOT ADOPT.**

It fails on three independent, each-sufficient grounds: (1) it cannot run cleanly on the app's bundled llama.cpp `llama-server`; (2) it makes the user's core capitalization complaint **worse**, force-capitalizing every fragment; (3) it hard-caps at 512 input tokens and further stops early, so 300–480-word dictations are truncated and mangled. It also degenerates into repetition loops and hallucinates on single-word inputs.

---

## 1. Runtime feasibility (critical)

**Bundled llama.cpp `llama-server`: effectively NO.** T5 is an encoder-decoder. llama.cpp has *experimental* T5 support (issue [#5763](https://github.com/ggml-org/llama.cpp/issues/5763)) usable via `llama-cli`, but the **`llama-server` completion / OpenAI endpoints do not drive the encoder step**. Running a T5 GGUF through the server surfaces the assertion / error **"call `llama_encode()` first"** — the server's decoder-only completion path never calls the encoder. This is the same limitation reported in [llama-cpp-python #1587](https://github.com/abetlen/llama-cpp-python/issues/1587) and the [Felladrin Flan-T5 GGUF discussion](https://huggingface.co/Felladrin/gguf-sharded-LaMini-Flan-T5-248M/discussions/1). Most current T5-in-llama.cpp usage is *encoder-only* (SD3/Flux text conditioning), not seq2seq generation over the server. So the app could **not** simply point its existing `llama-server` at a T5 GGUF.

**What integration would actually require (all are new work):**
- **ONNX Runtime (`transcribe-rs` already bundled):** *Plausible but non-trivial.* The app already ships an ONNX engine for ASR, but a T5 seq2seq graph is a different beast: you export **two graphs** (encoder + decoder-with-past/KV-cache) and must implement the **autoregressive generation loop + beam search + T5 tokenizer (SentencePiece)** in Rust yourself. `transcribe-rs` is built for a fixed ASR pipeline, not general seq2seq decoding — this is a substantial new engine, not a config swap. Optimum can export the ONNX, but the Rust-side decode loop is the hard part.
- **CTranslate2:** Cleanest T5 runtime technically, but it's a **new C++ dependency to bundle** (no Rust-native story), adding build/packaging burden.
- **In-process `transformers` (Python):** Would require shipping a Python + torch runtime — a massive footprint regression for a Tauri desktop app; a non-starter given the ~8 GB-free disk reality.

**Integration difficulty: HIGH.** No path reuses the current `llama-server` cleanly; the least-bad option (ONNX seq2seq in Rust) is a meaningful engineering project. This alone is close to a dealbreaker.

## 2. Model input format

Confirmed from the [model card](https://huggingface.co/vennify/t5-base-grammar-correction): prefix each input with **`"grammar: "`**. All eval runs used `"grammar: " + text`.

## 3–4. Local quality evaluation

18 representative real dictations + a targeted 482-word input + a capitalization/number probe. Beam search (num_beams=4), `max_length=512`, CPU (`torch 2.12 cpu`, `transformers 5.6.2`).

### Side-by-side (raw → T5-corrected)

| id | words | raw (truncated for display) | T5 output | note |
|----|-------|------|-----------|------|
| 1507 | 1 | `24` | `24. 24. 24. 24. …` (repeats ~50×) | **degenerate loop** |
| 1510 | 1 | `One.` | `One.` | ok |
| 1511 | 1 | `Two.` | `Two.` | ok |
| 1497 | 2 | `DW Bridges` | `DW Bridges.` | adds period only |
| 1492 | 3 | `D. W. Bridges` | `D. W. Bridges.` | adds period only |
| 1462 | 35 | `…Like what about Netflix.com, YouTube?…` | `…Like Netflix.com, YouTube?…` | **dropped "what about"** |
| 1463 | 40 | `…I uploaded it to you. It's in my downloads` | `…I uploaded it to you.` | **dropped trailing clause** |
| 1467 | 34 | `…Let's go ahead and try that` | `…Let's go ahead and try that.` | good (period) |
| 1472 | 26 | `…which works` | `…which works.` | good (period) |
| 1459 | 45 | `…They would have to scroll… What the fuck are you doi…` | `…They would have to scroll to know it's there.` | **dropped tail** |
| 1569 | 300 | long | early-stopped, partial | see §Long |
| 1489 | 323 | long | early-stopped, partial | see §Long |
| 1593 | 373 | long | early-stopped, partial | see §Long |
| 1579 | 482 | long | **truncated 562→512 tok, output only 88 words** | see §Long |

### Capitalization probe (the user's actual complaint)

| input | output | verdict |
|-------|--------|---------|
| `plan` | `Plan B. Plan B. Plan B. Plan C. …` | **forces capital + hallucinates + loops** |
| `stop` | `Stop! stop! stop! …` (loops) | degenerate |
| `the website` | `The website is located on the website.` | **forces capital + hallucinates** |
| `send it now` | `Send it now.` | **forces capital** |
| `can we add the icon` | `Can we add the icon?` | forces capital (adds `?`) |

**Capitalization verdict: it makes the complaint WORSE.** Every lowercase fragment is force-capitalized; the single-word case additionally hallucinates ("plan" → "Plan B") or loops. It does not "sensibly leave a single word uncapitalized" — it does the opposite. This is a direct, hard fail against the stated goal.

### Numbers / dates

No digit conversion: `five hundred dollars` → `Five hundred dollars.`; `march third` → `March third, march third.`; `3pm` unchanged. GEC only; does not normalize numbers/dates.

### Fidelity

On clean full sentences, fidelity is decent (mostly adds terminal punctuation, fixes minor agreement). But it **silently drops trailing content** on several medium inputs (ids 1462, 1463, 1459) and **hallucinates** on short/fragment inputs. It does not "answer" the dictation, but it is not content-safe on fragments or long inputs.

### Latency (CPU, beam=4)

Short: 0.4–1.2 s (excluding degenerate loops, which hit 10–12 s on `24`). Medium (30–60 w): 3–8 s. Long (300–480 w): **12–20 s**. The degenerate single-token loops (10+ s for one word) are a bad UX signature.

### Long-input result (likely dealbreaker — confirmed)

T5-base input cap is **512 tokens (~380 words)**. The 482-word dictation (id 1579) tokenized to **562 tokens**, was **truncated to 512** (transformers warning: *"Token indices sequence length is longer than the specified maximum (562 > 512)"*), and the decoder then **stopped early at ~88 output words** — roughly the **last 75% of the user's content was lost**. The 300–443-token inputs fit but still show early-stopping / partial rewrites. Long dictations are unusable.

## 5. Verdict & comparison

**Recommendation: DO NOT ADOPT.**

| criterion | T5-base-grammar-correction | current LLM (flowscribe-0.5B via llama-server) |
|-----------|-----|-----|
| Runs on bundled runtime | **No** (encoder-decoder unsupported on llama-server; needs new ONNX/CT2 engine) | Yes |
| Fixes single-word capitalization | **No — worse** (force-caps, loops, hallucinates) | tunable via prompt |
| Long inputs (300–480 w) | **Truncated/mangled at 512 tok** | handles long inputs |
| Fidelity | drops tails, hallucinates on fragments | can hallucinate, but steerable |
| Numbers/dates | no normalization | promptable |
| Latency | 3–20 s CPU | heavier but acceptable |

The current 0.5B decoder-only LLM is heavier and can hallucinate, but it (a) already runs on the shipped `llama-server`, (b) handles long dictations, and (c) is promptable — including toward *not* capitalizing bare fragments. T5-base-grammar-correction regresses on every axis the user cares about and would require building a whole new inference engine to even try. Not worth it.

*If* a lightweight GEC model is still desired later, the realistic path is an ONNX seq2seq engine (new work) plus a model without the 512-token cap and without the fragment-capitalization/looping behavior — this specific model is not it.

## Sources
- llama.cpp T5 support: https://github.com/ggml-org/llama.cpp/issues/5763
- llama-cpp-python "Cannot run T5-based models": https://github.com/abetlen/llama-cpp-python/issues/1587
- Flan-T5 GGUF encoder-decoder discussion: https://huggingface.co/Felladrin/gguf-sharded-LaMini-Flan-T5-248M/discussions/1
- Model card: https://huggingface.co/vennify/t5-base-grammar-correction
