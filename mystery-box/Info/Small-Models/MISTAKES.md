# MISTAKES.md — What went wrong and the rule for next time

Every incident here was discovered during the 076-config evaluation campaign (2026-07-01 → 2026-07-17).
Format: **symptom** → **root cause** → **rule to follow next time**.
Ordered roughly by how many configs were affected before the problem was caught.

---

## M-01 · Keyword scorer rewarded subject-echoing for ~30 configs silently

**Symptom.** Configs 001–035 showed summary scores of 7–10/10 on the benchmark.
A Sonnet subagent audit (summary_audit.md) reading all 380 clauses by hand found that
no config exceeded a 40% genuine-summary rate; configs scoring 10/10 on keywords (034,
032, 033, 021) were as low as 10–30% honest. The worst offender: 034-qwen3-hybrid scored
keyword 10/10 while 70% of its outputs were pure subject echoes.

**Root cause.** `score.py`'s summary metric is a vocabulary/entity-overlap check, not a
summarization-quality check. A clause that fluently paraphrases the subject line —
adding zero body information — passes every keyword group for that email. The scorer
literally cannot distinguish "Amazon shipped your order" (subject echo) from a genuine
body-fact clause. Models that defaulted to subject-echoing were being invisibly rewarded.

**Rule.** Never treat the keyword summary score as a quality signal in isolation.
Pair it with a reading audit (or the echo-gate: ≥70% subject-word overlap → fail) at
every era boundary. Two-stage summarization (stage-1 → compress) is the structural fix:
make echoing architecturally impossible by not including the email in stage-2.
The echo-gate was added in the 038-era; the reading audit remains the honest referee.

---

## M-02 · Our own `[MARKETING:…]` extraction tag poisoned purpose classification for ~15 configs

**Symptom.** Config 018 scored 9/10 purpose but kept misclassifying the Elicit
"Still want our emails?" retention email as `markets` instead of `asks`. All short
prompts (v1–v3 in prompt_lab) showed the same miss despite heavy rewriting.
The tag had been present from config 001 onward.

**Root cause.** `extract.email_block()` prepends a literal `[MARKETING: unsubscribe/
legal footer detected]` tag to any email containing an unsubscribe or legal footer —
including genuine `asks` emails that happen to have a footer. This tag text directly
biased the model toward `markets` regardless of prompt wording. The fix required *two*
things together: (1) an explicit rule that a decision/response request beats "looks
promotional", evaluated *before* the discount/promo rule, and (2) an explicit instruction
to ignore the `[MARKETING: …]` tag when classifying intent.

**Rule.** Preprocessing artifacts that are visible in the model's context affect
classification. Any flag or annotation injected by extraction code must either be
explicitly accounted for in the prompt or stripped from the classification view.
Test classification prompts against emails that carry the flag by design (footers with
genuine non-marketing intent) before declaring a prompt version final.

---

## M-03 · Hint-lists get parroted; worked examples get copied verbatim at ≤1.7B

**Symptom.** Config 039d: compress prompt v1 used a hint list "(offer, deadline,
request, or finding)". Qwen3 1.7B parroted the list as its answer → summary 1/10.
Config 040d: compress prompt v2 used a worked example ("40% shoe sale…"). Qwen3
copied the example verbatim on 3 of 10 emails — looked like 9/10 on casual inspection
but was fake on those 3 emails.

**Root cause.** Sub-2B models lack the instruction-following headroom to use examples
as demonstrations; they pattern-match to the nearest concrete string in the prompt
instead. Hint lists become the output; worked examples become a template to fill in
literally regardless of the actual email content.

**Rule.** For models ≤1.7B, use bare format constraints only — no hint lists, no
worked examples, no sample outputs. Describe what you want in terms of constraints and
structure ("start with a/an/the, ≤20 words, only words from the summary, output only
the phrase") not demonstrations. Gemma4 E2B class tolerated all three phrasings; this
fragility is a practical marker of the 1.7B vs E2B capability threshold. Also applies
to the free-summary stage-1: the old "offers, deadlines, requests, findings" noun list
made Qwen3 hallucinate "deadline" into summaries (048 finding) — the same parroting
failure one layer up.

---

## M-04 · Gemma returns empty `content` silently without `--reasoning off`

**Symptom.** During the validation run, llama-server was launched *without*
`--reasoning off --reasoning-budget 0`. Gemma4 E2B entities calls returned empty
`content` with all output routed to `reasoning_content`. 21 empty strings got written
into the pass cache before a non-empty guard caught it. Those 21 cached empty responses
were then served from cache on subsequent runs — silently poisoning the stored results.

**Root cause.** Gemma4 E2B has a thinking/reasoning mode. When llama.cpp serves it with
the reasoning format enabled (the default), output lands in `reasoning_content` and
`content` is empty. Multiple independent GitHub issues corroborate this: ArtemisAI/
strip-gemma-4 #1, mlx-lm #1352, llama.cpp #22786 and #25067. The flag interaction is
not an edge case — it is the default behavior for this model family in llama.cpp.

**Rule.** Always launch Gemma4 (and any reasoning-capable model) via `start_server.ps1`,
which includes `--reasoning off --reasoning-budget 0`. Never launch the server manually
from a bare command line during a benchmark run. The pass cache must be considered
poisoned if it contains empty strings — purge and re-run if the guard fires.

---

## M-05 · `/v1/models` answers during model load; used for readiness → 503s mid-run

**Symptom.** During multi-run sessions, the pipeline occasionally hit 503 errors
mid-benchmark despite the server appearing ready (health check passed). This was traced
to the readiness probe: the pipeline was polling `/v1/models` which returns 200 while
the model is still loading, then proceeding to fire inference requests before the server
was actually ready to serve.

**Root cause.** `/v1/models` is a metadata endpoint — it enumerates registered model
slots but does not wait for or confirm inference readiness. The model can still be in
the loading/warm-up phase when `/v1/models` returns 200. `ping_stub.py` exists precisely
to answer this endpoint for the offline/second-server case so the cache can replay
results without a live server — which also means any code relying on `/v1/models` as
a liveness signal is working against the stub design.

**Rule.** Use `/health` (llama-server's actual readiness endpoint) for launch-gating,
not `/v1/models`. Poll `/health` until it returns `{"status":"ok"}` before firing any
inference request. The `start_server.ps1` script handles this correctly; do not bypass
it with manual readiness checks.

---

## M-06 · `rstrip("'s")` ate brand names ending in *s*

**Symptom.** First blind-email test (config 074, Sparkles "Christmas in July" marketing
email): the brand name "Sparkles" was rendered as "Sparkle" → the proper-noun check
failed → the name was lowercased mid-sentence → "sparkle" appeared in the output.

**Root cause.** `render.py` used `rstrip("'s")` to strip possessive suffixes.
`rstrip` strips any trailing *character* in the given set, not a literal suffix string —
so "Sparkles" became "Sparkle" (trailing s stripped), "Paris" became "Pari", etc.
Any brand name ending in the letter s was silently corrupted.

**Rule.** Strip possessive suffixes with a true regex, not `rstrip`. The correct pattern
is `re.sub(r"'s$", "", name)` which matches only the two-character literal suffix `'s`
at the end of the string. `rstrip` is the wrong tool for suffix removal of any kind.
This was fixed before the fresh-30 blind run; regression confirmed 40/40 + 84/84 intact.

---

## M-07 · Three extraction bugs found only by blind data, invisible to the benchmark

**Symptom.** All three bugs scored 0/0 on the 10-email training set and 0/0 on the
22-email validation set. They were discovered only on emails that had never been run
through the pipeline before.

**Root cause (three separate incidents):**

1. **Single-line footer wipe (blind test, config 074):** The Sparkles email body
   collapsed to a single giant line in which the content and a footer phrase appeared
   on the same line. The footer cutoff rule deleted the *entire* remaining text from
   that line onward → output was 96 characters from 4,117. The model honestly reported
   "No body content was provided in the prompt" — a pipeline-vocabulary leak caused by
   starvation, not rendering. The benchmark set had no single-line-collapsed emails.

2. **Security-alert footer (validation era):** Security-alert emails have footer
   patterns not present in the training set. The footer zone exclusion for GLiNER
   entities was calibrated on training data structure; novel footer forms from the
   validation set produced entity noise.

3. **Giant-line catastrophic trim (fresh-30, config 075):** Same root as #1 — emails
   whose HTML-to-text conversion collapses all content to one giant line hit the footer
   cutoff and produced near-empty bodies. Fixed by a catastrophic-shrink guard:
   if output is <200 chars but input was >600 chars, fall back to the uncut text
   (junk lines still removed). Faire email (4,117 chars → "96") now summarizes fully.

**Rule.** A benchmark score of 100% does not mean the pipeline is correct — it means
it is correct on the specific emails in the benchmark. Run fresh, never-before-seen
emails through the full pipeline before any "ship" decision. The blind-data tally for
this project: 31 fresh emails → 3 real defects, all invisible to the 100%-scoring
benchmark. Budget time for a fresh-email certification pass after each champion is
sealed. The catastrophic-shrink guard (`<200 chars out of >600 in → fall back`) is the
current defense for the footer-wipe class.

---

## M-08 · Prompt cosmetic changes always perturb content emphasis (confirmed 3×)

**Symptom.**
- Config 071 (stage-1 told "never say 'the email'"): keyword score 84/84 same as 070,
  but a reading audit found content damage invisible to keywords: the PNC card summary
  lost the main event (card WAS locked), CVS confirmation led with accommodations
  boilerplate, UDG lost the password-reset action. The model also just substituted
  "the message" 4× — solving zero of the original cosmetic issue.
- Config 072 (delete "email" from all framing text): score dropped −2 AND Gemma still
  said "email" 4× (FROM/SUBJECT headers convey email-ness regardless of framing).
- Config 025 (Qwen3.5 2B style experiment): cosmetic prompt reorder → summary
  regressed; the earlier prompt_lab runs confirmed the same pattern repeatedly.

**Root cause.** Any change to the stage-1 prompt — even one intended only to affect
output phrasing, not content — alters the model's attention distribution over the email.
Sub-2B and E2B class models both exhibit this; keyword scoring cannot detect the
resulting emphasis shifts because it only checks vocabulary presence, not what the
clause leads with or which facts it prioritises.

**Rule.** Cosmetic fixes belong in `render.py` (deterministic string manipulation),
not in prompts. If the output renders awkwardly, fix the template or graft logic.
Do not issue a new config to fix a style complaint — any prompt change requires a full
reading audit, not just a keyword rescore. This lesson was confirmed three independent
times (071, 072, 025) and is now a project invariant.

---

## M-09 · Vendor sampling advice tested and both times worse

**Symptom.**
- Config 052: Gemma4 at the official vendor recipe (temp 1.0 / top_k 64 / top_p 0.95 /
  seed 42) → validation 79/84 (summary 18→16). Worse than temp 0.
- Config 053: Qwen3 1.7B at the official vendor recipe (temp 0.7 / top_p 0.8 / top_k 20 /
  seed 42) → validation 70/84 (summary 20→17, purpose *unchanged* at 17/21). Worse
  than temp 0 by 11 points, and did not fix the action-email informs-collapse the Qwen
  docs had suggested greedy decoding might cause.

**Root cause.** Vendor sampling recommendations target open-ended chat and creative
generation — not closed-set classification or constrained-format extraction. "Temperature
1.0 for Gemma" and "don't use greedy decoding for Qwen" are appropriate defaults for
freeform dialogue; they are anti-advice for deterministic extraction tasks where the
correct output is a fixed label or a short structured phrase.

**Rule.** For extraction and classification workloads: use temp 0. Do not apply vendor
sampling advice without testing. Both experiments are now falsified for this project's
workload; the validated finding is: **temp 0 wins on every model tested for this task.**
If a model shows a specific failure that vendor docs attribute to greedy decoding
(e.g. Qwen's informs-collapse), test their recommended temp first — but document the
result. In this case the failure was a model capability ceiling, not a sampling artifact.

---

## M-10 · Every "obvious speedup" failed on measured hardware

**Symptom.** The following optimizations were assessed or tested and produced zero
measurable gain (and in some cases a regression):
- `--flash-attn`: slightly negative to neutral on AMD iGPU Vulkan build.
- `--ubatch-size` 256/512/1024: all within ±5% noise.
- `--threads` 4/6/8/12: flat (GPU-bound; controlled 3-rep test showed no win).
- Speculative decoding: assessed and rejected — wrong bottleneck (saves bandwidth
  not compute; main/draft size ratio <3×; workload is prefill-heavy).
- MTP: unsupported by llama.cpp + our models.
- Parallel slots 6/8: 8→400s (2048 tokens/slot too small for big emails); 6→27.8s
  (worse than parallel-4's 19.5s). Parallel 4 is optimal.
- Within-email slot parallelism (purpose/clause/entities concurrently): 38.1s→36.4s
  (1.05× only — compute-bound iGPU shares ALUs, total work is constant).

**Root cause.** The hardware is a Vulkan iGPU (AMD integrated). It is compute-bound
(pp ~140–150 t/s, tg ~18–19 t/s, confirmed by GPU-bound flat threading profile).
Most "speedups" either target memory-bandwidth bottlenecks (wrong bottleneck here),
require driver support not present in Vulkan compute (flash-attn), or trade one resource
for another in ways that don't help a shared-GPU setup.

**Rule.** Profile before optimizing. On compute-bound iGPU Vulkan, the meaningful speed
levers are reducing token counts (stage-1 tokens 200→120 saved 30% wall time at zero
quality cost; entity decode budget 96→64 was free). Hardware flags are noise.
Do not chase driver-level or architecture-level speedups without measuring on the actual
device; iGPU results don't transfer to any dGPU or CPU benchmark you'll find online.

---

## M-11 · Validation set slowly spent: adjudicated ~12+ selection rounds on 22 emails

**Symptom.** Configs 058–076 all selected champions or made design decisions using the
same 22-email validation set (validation_ids.json, pinned 2026-07-14). By config 069,
the project had made ~12 champion-selection decisions against this set. The final
76-config champion claimed 100% validation, but the set had been the adjudicator for
every design choice since 058.

**Root cause.** A validation set that participates in repeated champion-selection rounds
is no longer held-out — it has been optimized against, implicitly, through the selection
process itself. Each "this config is better because it scores higher on validation" round
makes the next config's validation score slightly less meaningful as a generalization
estimate. The fresh-30 blind run (config 075) confirmed that the benchmark-perfect
pipeline still produced 3 real defects on never-seen emails.

**Rule.** Track how many champion-selection decisions have used each validation set.
After ~5–8 decisions, treat the set as partially spent and require fresh-email
confirmation before shipping claims of 100% accuracy. Keep a separate, never-touched
"certification set" for final ship-gate validation. The fresh_30_ids.json set exists
for this purpose; use it as the certification gate, not as another training signal.
The project note stands: *certify with fresh emails before shipping claims of 100%.*
