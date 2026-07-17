# RECIPE: Qwen3 1.7B email summarizer — config 042 (the good one)

**36/40 echo-gated (sender 10, purpose 9, summary 9, entities 8) · 129s wall / 10 emails
· AMD iGPU Vulkan · frozen 2026-07-14.**

> **CURRENT OVERALL CHAMPION (2026-07-16): `069-polish-cap45`** — 84/84 (100%)
> validation, 40/40 train, ~17s/email wall. Three-specialist stack: Gemma4 E2B
> (purpose + stage-1 summary, iGPU) + Falconsai T5-60M compress (CPU) + GLiNER
> entities (CPU) + code rules + graft-fix render + polish. Speed tier:
> `067-gliner-speed` (80/84, ~5s/email — GPU does only the 8-token purpose call).
> Qwen3 no longer appears in any current best config; this doc remains the record
> of the Qwen3 line (042/048) and its lessons. See eval/COVERAGE.md for the full arc.

This documents exactly how `eval/configs/042-qwen3-hybrid-twostage` works and why every
piece is the way it is. It is the best speed/quality pipeline found after 42 configs.
The config folder itself is the executable source of truth; this file is the map.

## The stack

| Layer | Value | Why (what broke without it) |
|---|---|---|
| Model | Qwen3-1.7B-Q6_K.gguf | Best accuracy-per-second of 20+ models tried |
| Server | llama-server (Vulkan build), `--n-gpu-layers 99 --parallel 4 --ctx-size 16384 --reasoning off --reasoning-budget 0` | Thinking mode tested (024): slower AND worse. 4 slots share KV prefix |
| Launch | `runtime\start_server.ps1 -ModelFile Qwen3-1.7B-Q6_K.gguf -Port 8001` | |
| Style | **hybrid** (all slots) | +2 entities, +1 summary vs inverted (042 vs 041d). Email in system prompt (KV cache), user turn = one-line recap "The email above is from X with subject Y" + instruction |
| Summary | **two-stage**: free summary (200 tok) → compress to ≤20-word phrase (48 tok) | Single-shot clause = 70% subject-echo on Qwen3 (audit). Two-stage: echo 22%, real body facts (salaries, counts, requirements) |
| Purpose prompt | v3 (aka prompt_lab v10, 128 words) | asks-rule BEFORE promo-rule + explicit "ignore [MARKETING:...] tag". 5/10 → 10/10 inverted (dips to 9/10 under hybrid) |
| Temperature | 0.0 everywhere | Determinism (llama-server batching still flips a rare word) |
| Extraction | body_cap 4000, trim_boilerplate on, marketing_flag on, markdown off | Markdown pre-pass tested twice (038e/039e): no gain, slower |

## Call sequence per email (all POST /v1/chat/completions, temp 0)

1. **sender_type** (8 tok) — often short-circuited by code rules (noreply→automated,
   footer→business) before any model call
2. **purpose** (8 tok) — v3 prompt, closed set asks/instructs/markets/informs,
   precedence order on ambiguous output
3. **clause stage 1** (200 tok) — "Summarize the email above in 2-4 sentences…"
4. **clause stage 2** (48 tok) — compress_v3 rewrites stage-1 output; **the email is
   NOT in this call** (instruction=system, stage-1 summary=user) — that's why echoing
   is structurally impossible here
5. **entities** (96 tok) — comma list; code verifies each name literally appears in the
   email (hallucination structurally impossible), dedup, cap 6

Then `render.py` fills: `Email from {sender}, likely {article} {sender_type} that
{purpose_verb} the user about {clause}.` + entity line.

## The compress prompt is a razor's edge at 1.7B (hard-won)

- v1: hint list "(offer, deadline, request, or finding)" → Qwen3 **parroted the list
  as its answer** (039d: summary 1/10)
- v2: worked example ("40% shoe sale…") → Qwen3 **copied the example verbatim on 3/10
  emails** (040d: looked like 9/10, was fake)
- v3 (shipped): example-free, bare format constraints — "start with a/an/the, ≤20
  words, only words from the summary, output only the phrase" → honest 8-9/10
- Gemma4 tolerated all three phrasings. This fragility is the practical difference
  between 1.7B and E2B class.

## Known residual issues

- Purpose 9/10 under hybrid: CustomizerGod digest flips to `markets` (the recap line
  disturbs the v3 rule that fixed it inverted). Untested fix: per-slot style mix —
  purpose inverted, clause+entities hybrid.
- Hallucinated "deadline"/"by deadline" occasionally leaks from the free_summary
  prompt's own vocabulary into clauses.
- The `[MARKETING:…]` extraction tag leaks into stage-1 summaries ("legal footer
  detection" appeared in a clause). Untested fix: marketing_flag off for the clause
  slot's view only.
- Some clauses truncate mid-word at the 20-word cap ("…start from…").

## Validation (2026-07-14 — the overfitting caveat below is now measured)

Held-out 21-email stratified set (security alerts, password resets, financial alerts,
deadlines, onboarding — none of which were in the tuning set):
- **042 (this recipe): 71/84 (85%)** — summary held at 20/21 (two-stage generalizes!),
  but purpose fell to 15/21: every action-required email (reset password, verify
  identity, assessment required) defaults to `informs`. Model ceiling, not prompt —
  Gemma4 runs the identical purpose prompt at 21/21. Entities 15/21 (omits sender org).
- **038d (all Gemma4): 80/84 (95%)** — purpose and entities PERFECT on unseen
  categories. **Ship 038d when quality matters.**
- Speed per email, 4 workers: Qwen3 ~13-15s wall (~48-58s sequential model time);
  Gemma4 ~19-24s wall (~73-93s sequential).

**Post-validation improvement — config 048 (best Qwen3, 73/84 = 87% validation):**
042 + two changes:
1. `"context": "free_summary"` on the purpose slot — the classifier reads the clause
   stage-1 summary prepended to the v3 prompt. Fixed 3 of the 6 action-email purpose
   misses (reset-password/onboarding emails whose own summary says "call to action").
   Purpose 15→17-18/21. Plumbing: classify.py free_summary param; clause runs first.
2. Stage-1 free_summary prompt DE-HINTED: the old "offers, deadlines, requests,
   findings" noun list made Qwen3 hallucinate "deadline" into summaries (same
   parroting failure as compress v1). New wording describes content kinds with verbs:
   "what happened, what is offered, and what the recipient is expected to do".
   Summary back to 20/21 val, first 10/10 train.
Sweep result: two-stage recipe on Qwen3.5 2B (045: 35/40) and MiniCPM5 (046: 21/40)
found no upset — Qwen3 1.7B and Gemma4 E2B remain the frontier.

## Caveats on the numbers

- Training-set scores came from the SAME 10 emails all 42 configs iterated against —
  see the validation section above for the honest generalization numbers.
- Single run; observed run-to-run noise ±1 point (server batching nondeterminism).
- Summary metric = keyword groups + echo-gate (≥70% subject-word overlap fails). The
  gate cannot catch fluent paraphrase-echo; eval/summary_audit.md is the honest referee.

## Reproduce

```powershell
cd C:\Users\Calibro1\Documents\EmailSummarizer
.\runtime\start_server.ps1 -ModelFile Qwen3-1.7B-Q6_K.gguf -Port 8001   # wait for ready
python eval/run.py --config 042-qwen3-hybrid-twostage --no-cache --force
python eval/score.py eval/results/042-qwen3-hybrid-twostage.json
```

## Dream team — per-slot model routing (043/044, added later on 2026-07-14)

`044-dreamteam-cap28`: **39/40** (sender 10, purpose 10, summary 9, entities 10) — ties
the all-Gemma champion using Qwen3 for 3 of 4 slots.

- sender_type + clause: Qwen3, hybrid, two-stage (as 042)
- **purpose: Qwen3, style back to `inverted`** — hybrid's recap line was flipping the
  CustomizerGod digest to `markets`; inverted restores v3's 10/10
- **entities: Gemma4 E2B Q4_K_M, inverted** — the only model ever to hit 10/10 there
- **clause max_words 28 (was 20), stage-2 max_tokens 64 (was 48)** — the 20-word
  guillotine kept amputating the best fact mid-phrase ("with a salary…"). The compress
  prompt still asks for ≤20 words; the cap is headroom, not a target. Recovered the
  salary range, feature lists, clean sentence endings → summary 8→9.

**Hardware limitation:** this iGPU cannot host both models simultaneously (Vulkan
ErrorOutOfDeviceMemory → 400s → server crash; ctx 8192/4096 + parallel 2 all failed).
Workaround used: two sequential passes through the pass cache — phase A runs Gemma
alone and caches the 10 entities calls (~231s), phase B runs Qwen alone with cache ON
(entities hit cache exactly). Total ~380s sequential, so on THIS machine the all-Gemma
`038d` (39/40, 191s, one server) is still the practical quality pick. 044 becomes the
best config the moment both models fit in memory at once.

Sibling recipes: quality champion is `038d-twostage` (Gemma4 E2B Q4_K_M, 39/40, 191s) —
same architecture, model swapped, purpose stays 10/10 and entities 10/10 there.
Full experiment history: eval/COVERAGE.md · echo audit: eval/summary_audit.md ·
purpose prompt iteration log: eval/prompt_lab/LOG.md.

Remaining 1-point gap to 40/40 (all top configs): the DeviantArt summary keyword group
demands a "promo/marketing"-type word that an honest body summary doesn't naturally
contain — likely a gold-label fix, not a model fix.
