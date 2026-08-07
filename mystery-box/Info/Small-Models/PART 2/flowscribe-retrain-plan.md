# Retraining our own dictation-cleanup model ("FlowScribe") — plan & analysis

**Status: analysis / plan only. Nothing built or trained.** This machine is CPU-only, so
training cannot run here — the training step requires an external GPU (see
[The one real blocker](#the-one-real-blocker-no-local-gpu)).

Context: the [cleanup bake-off](cleanup-bakeoff-results.md) picked
`flowscribe-qwen2.5-0.5b-v2` (Q4_K_M GGUF) as the best on-device dictation-cleanup model that
actually runs on our stack. This doc records (a) how it was built and whether that's repeatable,
(b) why we might retrain our own, (c) the base-model decision (incl. the "why not a newer Qwen?"
question), and (d) a concrete sketch of what a retrain would take.

---

## 1. How the reference model was built (from its HF card)

`Abdullahu5mani/flowscribe-qwen2.5-0.5b-v2` — the source of the GGUF we tested.

| | |
|---|---|
| Base | `Qwen/Qwen2.5-0.5B-Instruct` |
| Method | LoRA via Unsloth (72.4% of params trained) |
| Dataset | `Abdullahu5mani/flowscribe-dataset` — 27,393 synthetic examples, Alpaca-style (instruction/input/output), 10 domains, 49 formatting styles |
| Hyperparameters | 3 epochs · lr 2e-5 · effective batch 16 (8×2 grad-accum) · seq len 2048 · AdamW 8-bit · final loss 0.616 |
| Hardware | NVIDIA RTX 4070 Laptop, 8 GB |
| Chat template | ChatML |
| System prompt | "You are Flowscribe, an expert Speech-to-Text post-processing AI…" |
| License | **MIT** (model). Dataset license: **unspecified**. |

It is a **style-instructed formatter**, not just a cleaner — its native prompt looks like
`"Transcribe and format this with style: Software_Dev"` (styles include Verbatim, Casual, Auto).
It won our bake-off even though we drove it with a *generic* cleanup prompt, so using its native
prompt would likely do better and unlocks per-style formatting we didn't exercise.

### Is it repeatable?

- **Closely reproducible — yes.** The dataset is public, the base and all hyperparameters are
  documented. We could re-run a very close reproduction.
- **Bit-for-bit — no.** No training code/notebook or seed is published, and the dataset itself is
  not regenerable (synthesised via "Google Gemini (primary) + 16 free OpenRouter models" with no
  published pipeline). There is also no dataset card and **no stated dataset license**.

---

## 2. Why retrain instead of just using it

Using the off-the-shelf GGUF is fine and MIT-licensed. Reasons we might still retrain our own:

1. **License cleanliness.** The *model* is MIT but the *training data* has no stated license and was
   generated from Gemini/OpenRouter outputs. For a commercial product that gray area is worth
   removing by owning our data.
2. **Domain tuning.** Bake in DW Bridges vocabulary, product/person names, the app's "taught words",
   and real raw→clean pairs from actual usage — so cleanup gets *our* terms right.
3. **True ownership + reproducibility.** We'd publish our own training script + seed, so the model is
   fully reproducible (the thing the original lacks).

If the goal is just "ship cleanup soon," retraining is optional polish, not a prerequisite.

---

## 3. Base-model decision (the important part)

### Naming clarification
- **Qwen3** (Apr 2025) is the family with the **0.6B** edge model.
- **Qwen3.5** (Feb 2026) is a refresh whose *small* model is **0.8B**, not 0.6B.
- So "a newer 0.6B" = **Qwen3-0.6B**; "a newer 0.8B" = **Qwen3.5-0.8B**.

### The runnability catch (ties back to the bake-off)
The app runs models as **GGUF via llama.cpp/llama-server**. If a base can't convert to GGUF, the
resulting model can't run in the app at all.

| Base | GGUF / llama.cpp | Verdict |
|---|---|---|
| **Qwen2.5-0.5B-Instruct** | Fully supported (proven winner's base) | ✅ Safe |
| **Qwen3-0.6B-Instruct** | Supported — official GGUFs exist, `convert_hf_to_gguf.py` handles it | ✅ Safe "newer" option |
| **Qwen3.5-0.8B** | **Supported** — GGUF quants exist (bartowski, unsloth, lmstudio-community, mradermacher); Unsloth documents fine-tuning it | ✅ Viable, more capable |

CORRECTION (2026-08-07): an earlier version of this doc called Qwen3.5-0.8B "risky / a dead end, no
GGUF." That was wrong. The macwispr models in the bake-off failed only because *those specific uploads*
were MLX-quantized safetensors (Apple format) with no GGUF — NOT because llama.cpp lacks Qwen3.5
support. Official/community GGUF quants of Qwen3.5-0.8B exist and run in llama.cpp, and Unsloth
supports LoRA fine-tuning it. So Qwen3.5-0.8B is a legitimate, more-capable base for our own retrain.

### Why the original author used Qwen2.5-0.5B (assessment)
Even assuming a newer base was available, this was the correct call for a *shippable* model:

1. **Tooling maturity** — Unsloth and llama.cpp had rock-solid day-one Qwen2.5 support; newer archs
   lag in both.
2. **Cross-platform runnability is the whole game** — Qwen2.5-0.5B → GGUF → runs everywhere. It was
   the *only* cleanup model that ran in our test, while bleeding-edge `qwen3_5` ones were stranded.
3. **0.5B is enough, and smaller is faster on CPU** — cleanup is an easy task; little to gain from
   0.6B and a real latency cost.
4. **"Boring tech that works"** — least resistance, maximum compatibility for a solo dev on an 8 GB
   laptop GPU.

**Recommendation:** **Qwen3.5-0.8B is now the most attractive base** — it's GGUF-supported and
meaningfully more capable than 0.5B, which is exactly the weakness that made the "Professional/concise"
style unreliable on flowscribe-0.5B (it paraphrased and, on meta inputs, answered/apologized). A larger
base is the most likely fix for a *trustworthy* Professional mode. Qwen2.5-0.5B stays the safe, smallest
fallback. Cost: ~0.8B Q4 GGUF is ~0.5 GB (vs ~0.4 GB) and a bit slower on CPU.

---

## 4. Retrain sketch

| Step | What | Notes / effort |
|---|---|---|
| 1. Base | `Qwen2.5-0.5B-Instruct` (safe) or `Qwen3-0.6B-Instruct` (newer, still GGUF-safe) | Start with 2.5-0.5B to match the proven winner |
| 2. Data | Public `flowscribe-dataset` (~27k) **+ our domain examples** | Where retraining earns its keep: DW Bridges vocab, names, taught-words, real raw→clean pairs |
| 3. Generate clean targets | Use one strong model, once, to produce "cleaned" versions of our dictations as training targets | ~half a day; the synthetic-data step |
| 4. Train | LoRA via Unsloth, ChatML template, ~3 epochs, lr 2e-5 (their recipe) | 1–3 hrs on a single GPU for a 0.5–0.6B LoRA |
| 5. Convert | Merge LoRA → `convert_hf_to_gguf.py` → quantize Q4_K_M | minutes |
| 6. Eval | Re-run the existing bake-off harness on held-out dictations | reuse `scratchpad/harness.py` |

### The one real blocker: no local GPU
This machine is CPU-only (no CUDA torch). Unsloth needs an NVIDIA GPU, so training must happen
elsewhere:
- **Free Google Colab (T4)**, a **rented cloud GPU** (~a few dollars for a couple hours), or a
  company NVIDIA box.
- **Privacy:** including real company dictations means that data leaves the machine during cloud
  training. Mitigations: train on public data + *synthetic* domain examples (no real content), or use
  a private/self-hosted GPU.

### Cost & time
Roughly **1–2 focused days**, dominated by data prep and GPU access — not the training itself
(1–3 hrs). Cash cost near-zero (Colab) to a few dollars (rented GPU).

### What we'd get vs off-the-shelf
Full ownership, **MIT-clean provenance** (removes the dataset-license question), a model tuned to our
vocabulary, and a **reproducible script + seed**.

---

## 5. Bottom line

- **Ship soon:** use `flowscribe-qwen2.5-0.5b-v2` GGUF as-is (MIT, works today). Retraining is
  optional.
- **Own it / domain-tune / clean license:** retrain on **Qwen2.5-0.5B-Instruct** (optionally A/B
  **Qwen3-0.6B**), on public data + synthetic domain examples. **Skip Qwen3.5-0.8B** until GGUF
  support is confirmed.
- **Either way:** add a **short-utterance bypass** (<~3–4 words) — every model, winner included,
  hallucinates on 1–2 word fragments.

Whichever path, the *feature* still needs a build: bundle a llama.cpp runtime, add a "Clean up my
dictation" toggle, wire it into the transcription pipeline, and add the short-utterance guard. That
is a separate implementation plan.

---

## Sources
- Qwen3.5 small models — https://artificialanalysis.ai/articles/qwen3-5-small-models
- Qwen release timeline — https://www.scriptbyai.com/qwen-timeline/
- Qwen3-0.6B GGUF (exists / runnable) — https://huggingface.co/codebasic/Qwen3-0.6B-GGUF
- llama.cpp Qwen conversion docs — https://qwen.readthedocs.io/en/latest/quantization/llama.cpp.html
- FlowScribe v2 model — https://huggingface.co/Abdullahu5mani/flowscribe-qwen2.5-0.5b-v2
- FlowScribe dataset — https://huggingface.co/datasets/Abdullahu5mani/flowscribe-dataset
