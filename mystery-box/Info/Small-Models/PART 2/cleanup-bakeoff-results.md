# Dictation-Cleanup Model Bake-off — Results

Local, on-device evaluation of small "dictation cleanup" models for a Windows dictation app.
Everything ran locally; no data left the machine. Date: 2026-08-07.

## TL;DR — Recommendation

**Adopt `flowscribe-qwen2.5-0.5b-v2` (Q4_K_M GGUF).** It gives the best balance of cleanup quality and
fidelity of any candidate that actually runs on this stack, is tiny (~398 MB), reasonably fast on CPU
(median ~2.3 s/dictation), and is **GGUF** — a drop-in for the app's future `llama-server` path.

- **Primary:** `flowscribe-qwen2.5-0.5b-v2` Q4_K_M — quality 8 / fidelity 8.5.
- **Backup / most conservative:** `flowscribe-qwen2.5-0.5b` (v1) Q4_K_M — slightly weaker cleanup but the
  safest on ultra-short utterances and the fastest (median ~1.55 s). Also GGUF.
- Add a **short-utterance bypass** (skip cleanup for inputs under ~3–4 words). Every model tested,
  including the winner, is prone to *inventing* content when handed a 1–2 word fragment.

## Methodology

- **Test set:** the 50 raw dictations in `dictation_testset.json` (`transcription_text` = raw ASR output).
  All 50 were used for every model.
- **Harness:** `scratchpad/harness.py`. For each model it launches the prebuilt llama.cpp
  `llama-server.exe` against the GGUF, waits for `/health`, then sends all 50 transcripts and records the
  cleaned output + wall-clock latency per item. Results are written **incrementally** to
  `scratchpad/bakeoff/<slug>.json` (`[{id, raw, cleaned, ms}]`) so an interruption loses nothing.
- **Prompt:** the default cleanup system prompt from the brief, sent as an OpenAI-style
  `system`+`user` chat pair, **except** where the model card specified otherwise (see per-model notes).
- **Decoding:** temperature 0.2 (0.0 greedy for Quill, per its card). `max_tokens ≈ 2.5× input words + 64`,
  `--ctx-size 4096`, 8 threads, CPU build.
- **Judge:** the agent read raw-vs-cleaned pairs for all 50 items per model and scored Cleanup Quality
  and Fidelity (0–10). Automated stats (median latency, output/input character ratio, passthrough count)
  were used to flag over-compression, passthrough, and hallucination blow-ups.

## Environment used

- **Runtime:** `C:\Users\Calibro1\Documents\EmailSummarizer\runtime\llama-bin\llama-server.exe`
  (llama.cpp build 9728, CPU), OpenAI-compatible HTTP API.
- **Python:** `C:\Python314\python.exe` (transformers 5.6.2 / torch 2.12 CPU / huggingface_hub 1.20.1) —
  used only for downloads and scoring, not for inference.
- **Downloads:** one candidate GGUF at a time into the HF cache, tested, then **deleted** before the next.
  No new packages or runtimes were installed. Free disk stayed well above the 1.5 GB floor throughout.

## Ranked summary

| Rank | Model | Format | Size (Q4_K_M) | Quality /10 | Fidelity /10 | Median ms | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | **flowscribe-qwen2.5-0.5b-v2** | GGUF | 398 MB | **8** | **8.5** | 2290 | **Winner** — best cleanup, high fidelity, GGUF drop-in |
| 2 | flowscribe-qwen2.5-0.5b (v1) | GGUF | 398 MB | 6 | 8 | 1550 | Safe backup; lighter cleanup, fastest, best on short frags |
| 3 | Emberon-1.2B | GGUF | 731 MB | 6 | 7 | 3312 | Coding-tuned; light on general dictation, some meaning drift; slow/large |
| 4 | Quill-0.8b | GGUF | 529 MB | 5 | 4 | 3862 | Barely cleans long text; **answers/refuses** on short inputs — fidelity fail |
| — | LFM2.5-350M (control) | GGUF | 379 MB (Q8) | 4 | 3 | 1668 | Not cleanup-tuned: over-compresses, adds meta text, inverts meaning |
| — | RAW (baseline) | n/a | — | 0 | 10 | 0 | Untouched transcript, reference only |

Fidelity was weighted first, then quality, then speed/size.

## Side-by-side examples (RAW vs each model)

### id 1576 — ultra-short fragment
- **RAW:** `Plan`
- flowscribe-v2: `I need to plan for the weekend.` ← **hallucination** (invented content)
- flowscribe-v1: `Plan.`  ✅
- Emberon: `Plan:`  ✅
- Quill: 873-char answer explaining "how to make a plan" ← **answered, not cleaned**
- control: `Plan to start the day with a healthy breakfast and a short walk.` ← hallucination

### id 1577 — short fragment
- **RAW:** `Fine-tuning Reddit`
- flowscribe-v2: `Fine-tuning Reddit`  ✅
- flowscribe-v1 / Emberon: `Fine-tuning Reddit.`  ✅
- Quill: `I'm sorry, I can't fine-tune Reddit. I'm a text-based AI…` ← **refused / answered**
- control: `Fine-tuning Reddit involves training the model on a large dataset…` ← hallucination

### id 1594 — self-correction ("one thing, yeah, but what I mean is yes, you can use them")
- **RAW:** `Okay, so I would like you to use my real dictation. However, one thing, yeah, but what I mean is yes, you can use them, and since we're doing this sequentially … a large chunk of like 30 or maybe fifty`
- **flowscribe-v2:** `Okay, so I would like you to use my real dictation. However, since we're doing this sequentially, we're going to have to log them and probably do my most recent thirty dictations … a large chunk of 30 or maybe 50.` ← resolved the self-correction, dropped fillers, normalized numbers ✅ **best**
- flowscribe-v1: unchanged except a trailing period — left `one thing, yeah, but what I mean is yes` ← under-cleaned
- Emberon / Quill: near-passthrough, fillers left in ← under-cleaned
- control: `Okay, so yes, we can use them. Since we're doing this sequentially, we'll log them and probably do the most recent thirty.` ← dropped the "30/50 chunk" content

### id 1564 — run-on with "when I say that I mean"
- **RAW:** `So I'm looking at it and personally I think it can be smaller and when I say that I mean overall like the cards look fine you know … forcing you to scroll down to then see the language area so I'm imagining it overall being a bit smaller …`
- flowscribe-v2: full sentence segmentation + punctuation, meaning preserved ✅
- flowscribe-v1: cleaned well, trimmed "you know / I mean", meaning kept ✅
- Emberon: readable but garbled "when I say that, the cards look fine" (dropped "I mean overall") — minor meaning break
- Quill: only stripped periods; still a run-on ← under-cleaned
- **control:** wrapped output in `Sure, here's a cleaned-up version of your text: "…"` + `Let me know if you'd like any further adjustments!` ← **added meta commentary** and truncated the text ← fidelity fail

### id 1549 — longer, hedged reasoning
- **RAW:** `Okay, so when I tested it with the noise that you added over … So maybe we're looking at the wrong type of models … We're not looking exactly for denoising, I suppose`
- flowscribe-v2: full text preserved, punctuation added, nothing dropped ✅ **best**
- flowscribe-v1: preserved, minor trims ✅
- Emberon: good, but dropped "The voice is more clear" and duplicated a clause — minor drift
- Quill: passthrough + final period ← under-cleaned
- **control:** collapsed the whole paragraph to `The voice is more clear. So maybe we're looking at the right model.` ← **inverted the meaning** (raw said *wrong* model) and dropped ~90% ← severe fidelity fail

## Aggregate signals (all 50 items)

| Model | Median ms | Mean ms | Mean out/in char ratio | Notes |
|---|---|---|---|---|
| flowscribe-v2 | 2290 | 3236 | 1.03 | ideal-ish; light, faithful cleanup |
| flowscribe-v1 | 1550 | 2167 | 0.80 | compresses a bit (some filler/clause drop) |
| Emberon-1.2b | 3312 | 3844 | 0.93 | light touch on general dictation |
| Quill-0.8b | 3862 | 5227 | 6.28 | **blows up on short inputs** (answers/CoT/refusals) |
| control LFM2.5-350M | 1668 | 2604 | 1.97 | expands/hallucinates on short, over-compresses on long |
| RAW | 0 | 0 | 1.00 | — |

A char ratio far from ~1.0 is a warning sign: Quill's 6.28 and control's 1.97 are driven by the model
*answering or continuing* short fragments instead of cleaning them.

## Per-model prompt notes

- **flowscribe v1/v2** (base Qwen2.5-0.5B-Instruct fine-tune): card gives no specific prompt → default
  system prompt via ChatML chat endpoint.
- **Emberon-1.2B** (LFM2.5-1.2B-Instruct fine-tune): used the author's exact trained system prompt
  ("You are a dictation cleanup tool for coding…"). It is coding-oriented, which likely explains its
  conservative behavior on general speech.
- **Quill-0.8b** (Qwen3.5 fine-tune): used the card's recipe — ChatML, system `You clean up dictated text.`,
  assistant turn pre-seeded with an empty `<think></think>` block (via the raw `/completion` endpoint so the
  think-suppression actually applied), greedy temp 0, no `--jinja`. Even so it answered/refused short inputs.
- **control LFM2.5-350M** (`LFM2.5-350M-Q8_0.gguf`, already on disk): default prompt; included as a
  not-cleanup-tuned reference.

## Models skipped (could not run on this stack)

All of the following are **MLX-quantized safetensors** (`config.json` → `quantization: {mode: "affine", …}`).
MLX affine quantization is not loadable by transformers/torch, there is no CPU/Windows MLX runtime here, and
the architectures (`qwen3_5`, and MLX-quant `lfm2`) are not supported by the installed transformers 5.6.2.
No GGUF equivalents are published for any of them. `peft` is not installed, so the one LoRA-merge fallback
(LC-lfm2.5-350m's adapter onto an fp16 LFM2.5-350M base) was also blocked and would have required an extra
~700 MB base download for a single model — not pursued.

| Model | Format on HF | Reason skipped |
|---|---|---|
| vasanth009/LC-lfm2.5-350m | MLX 5-bit safetensors (+ LoRA adapter) | MLX-only; LoRA-merge blocked (no `peft`, base not on disk) |
| vasanth009/LC-350M-smart | MLX 4-bit safetensors | MLX-only, unloadable |
| vasanth009/macwispr-qwen35-08b-polish | MLX 4-bit safetensors (qwen3_5) | MLX-only; "full precision" label incorrect (config shows 4-bit); arch unsupported |
| vasanth009/macwispr-polish-qwen35-08b-v3-4bit | MLX 4-bit safetensors (qwen3_5) | MLX-only, arch unsupported |
| abhiram3040/simplewords-dictation-cleanup-v3 | MLX 8-bit safetensors (qwen3_5) | MLX-only, arch unsupported |
| Abdullahu5mani/flowscribe-qwen2.5-0.5b (safetensors base) | safetensors + gguf | **De-duplicated** — covered by the mradermacher flowscribe GGUFs that were tested |

No model was skipped for lack of disk space; the one-at-a-time download/delete discipline kept free space
between ~7.3–7.8 GB the whole run.

## Final recommendation

1. **Ship `flowscribe-qwen2.5-0.5b-v2` (Q4_K_M GGUF)** as the dictation-cleanup model. It cleans fillers,
   fixes punctuation/capitalization, segments run-ons, and correctly resolves spoken self-corrections while
   preserving meaning — the best quality/fidelity trade-off among runnable candidates, and small + fast.
   Because it is GGUF it plugs directly into the app's future `llama-server` path (base Qwen2.5-0.5B-Instruct,
   ChatML template).
2. **Keep `flowscribe-qwen2.5-0.5b` (v1) as a fallback** if you want maximum safety on very short utterances
   or the fastest option; it is the same size and format.
3. **Guard short inputs.** All models (winner included) can hallucinate on 1–2 word fragments; bypass cleanup
   below ~3–4 words to eliminate that failure mode.
4. Avoid Quill and the untuned LFM2.5-350M control for this task: both fail fidelity by answering/continuing
   or by rewriting/inverting the user's words.

## Cleanup

All four downloaded candidate GGUFs (flowscribe v1, flowscribe v2, Quill, Emberon) were deleted from the HF
cache after testing. Pre-existing EmailSummarizer GGUFs and unrelated cache entries were left untouched.
Only the small JSON outputs in `scratchpad/bakeoff/` and `scratchpad/harness.py` remain. Final free disk on
C: ≈ **7.29 GB** (started ≈ 7.85 GB; the small delta is background system usage, not leftover models).
