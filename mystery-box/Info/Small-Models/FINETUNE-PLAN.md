# Fine-tuning plan — three-specialist architecture (decided 2026-07-15)

## Decision

Train **three specialist LoRA adapters** on a shared **Qwen3.5-0.8B** base — one per
AI slot: **purpose**, **summary**, **entities**. Sender-type stays code rules (solved:
10/10 across all 55 configs, usually no model call).

Chosen over the fused single-model alternative (one call, all outputs) deliberately:
the user prioritizes **control and cheap targeted repair** — when one slot develops a
loophole, retrain one ~20-50MB adapter for pocket change instead of gambling a whole
model retrain. Accepted cost: single-email latency ~7-8s (repeated prefills per
specialist, adapters break KV-prefix sharing) vs ~4.5s fused. Batch throughput
largely unaffected. Escape hatch if latency bites: purpose specialist reads the
summary specialist's OUTPUT (tiny prefill) instead of the raw email.

## Why fine-tuning at all

- Prompts get baked into weights: no instruction tokens at inference (shorter
  prefill), no instruction-following failures (the 0.8B's screen failure was
  instruction interpretation, not comprehension).
- NuExtract proved the pattern: 0.5B base (our worst generalist) → competent
  specialist via LLM-annotated fine-tuning.
- Speed truth: training NEVER changes tokens/sec (same param count) — the speed wins
  come from shorter inputs (no prompts) and fewer/shorter outputs.

## Data plan

- Target **3,000-5,000 high-quality examples** per the "extreme accuracy" goal;
  quality and diversity beat volume. ~1k is the floor for a solid specialist.
- Sources ranked: (1) user's own inbox — mail.db has 434, export deeper Proton
  history first, this is the best-matched distribution; (2) teacher-generated
  augmentation (controlled variants of real emails); (3) public newsletter archives;
  (4) Enron corpus as ~10% seasoning for person-to-person mail only.
- **Class balance**: inbox is ~70% informs/markets — oversample asks/instructs or
  the informs-bias gets inherited.
- **Decontamination**: the 10 train + 22 validation eval emails must NEVER appear in
  training data.
- Teacher labels (Claude + the 051 pipeline) follow the accumulated labeling policy:
  v3 purpose rules (asks-before-markets, ignore marketing footer tag), echo-gate
  filter on all summary labels, entities must literally appear in the email.
- Training format: minimal fixed marker, NOT the production prompts (prompts are
  teacher-side only). One frozen chat structure for training and inference — style
  experiments (inverted/hybrid) are irrelevant post-fine-tune.

## Pipeline integration and evaluation

- llama-server: one 0.8B base + three LoRA adapters, switched per call.
- Per-slot eval already exists (score.py reports each slot). A specialist ships only
  when it beats/matches champion 051 on ITS slot (purpose 21/21, summary 18/21,
  entities 21/21 validation). Mix-and-match with Gemma for unready slots.
- Steps: (1) export more Proton mail; (2) define 3 label schemas + annotate with
  balancing/decontamination; (3) user reviews ~50-label sample before scaling;
  (4) rent cloud GPU (QLoRA on 0.8B = hours, few dollars), train 3 adapters;
  (5) convert to GGUF adapters; (6) run the existing harness per slot.

Status: PLANNED — nothing trained yet. Champion remains 051 (81/84, see
eval/COVERAGE.md and RECIPE-QWEN3.md).
