# EmailSummarizer — Unified Plan

Goal: a hover-pill email summary in Unified.exe that is fast, honest, searchable.
Strategy: Python lab discovers what works; C# ships it. Model does only what a
small local model can do (copy text, pick from closed sets); code does the rest.

State: infrastructure done (Vulkan server, trimming, prefix caching, pass cache,
score harness). Product pipeline (template summary) designed, not yet built.

---

## Phase 1 — Reorganize  [next action]

Max five items in root:

    PLANS.md         this file
    runtime/         models/, llama-bin/, llama-bin-vulkan/, start_server.ps1
    pipeline/        the product (built in Phase 2)
    eval/            run.py, score.py, gold_labels.json, results/
    old_reference/   all v1 code, prompts, results, caches, artifacts — frozen

Steps: move v1 files → old_reference/; move server assets → runtime/ and fix
start_server.ps1 paths; move score.py + gold_labels.json → eval/; verify server
starts and score.py still runs against an old results file.
Nothing is deleted.

## Phase 2 — Build the template pipeline (Plan B)

Output per email (stored as JSON, rendered as a sentence):

    <Email> from <sender-addr>, likely a [business/individual/automated service]
    that [asks/instructs/informs/markets] the user about [one-clause summary].
    List of mentioned entities: [flat, comma-separated]

Rules baked in:
- temperature 0 everywhere (finally applied for real)
- <script slots> extracted in code: sender, subject, trimmed body, marketing flag
- [AI slots] are closed-set picks or bounded outputs, each validated in code;
  invalid answer → "unknown", never shipped as-is
- entities verified to literally appear in the email text; non-matches dropped;
  deduped; display capped at ~6, full list kept for search
- purpose precedence when torn: asks > instructs > markets > informs
- sender_type answered by code when confident (noreply/marketing signals),
  model only breaks ties
- summary clause model call reads the trimmed email directly, never pass notes
- inverted prompt structure (email as shared system prefix) for KV-cache reuse

Files: pipeline/{extract,classify,summarize,render,llm}.py + pipeline/prompts/
llm.py is the only file that talks to the server (client, cache, temp, retries).

Build order: llm.py+extract.py → classify.py → summarize.py → render.py+eval/run.py.
Each stage tested on the 10-email set as soon as it exists.

## Phase 3 — Validate

1. USER REVIEWS eval/gold_labels.json (currently Claude's draft — the yardstick
   must be human-approved). Add template-era fields: expected sender_type,
   expected purpose per email.
2. Full 10-email run → score vs v1 numbers (v1 baseline: urgency 4/10,
   summary 4/10, ~50s/email). Targets: summary ≥8/10, sender_type+purpose
   ≥9/10, ≤15s/email.
3. Iterate prompts one slot at a time: tune on email 8 (CodePen, hardest),
   accept only if the full-10 score doesn't regress.
4. Optionally widen the gold set to 20-30 emails once labels are cheap to add.

## Phase 4 — Ship (C# port)

Trigger: template pipeline passes Phase 3 targets.
- SummarizerService.cs in host/Unified.Host next to MailDb.cs: HttpClient to
  llama-server, same prompts (copied as-is), same validation logic
- structured fields written to mail.db; renderer gets them via BridgeRouter;
  pill UI renders the sentence, entities searchable
- eval/score.py keeps working against the C# output (it only reads JSON)
- server lifecycle: host starts/stops llama-server alongside the app

## Parked (deliberate, revisit later)

- Urgency levels on the pill. Restart point: Plan A 2d below — 'personal'
  probe answered in code, remaining probes reworded to text-observable facts.
- Qwen 0.5B as second server for probes/classification (it was the
  conservative model; benchmark said LFM 1.2B over-fires on judgment calls)
- Merged urgency probes (rejected once for cross-contamination)
- Prompt-format smoothing of the template sentence (stiff English is fine
  for now; true-but-stiff beats fluent-but-invented)

## Reference — v1 findings (2026-07-14, LFM2.5 1.2B, gold-scored)

- inverted style: urgency 4/10, summary 4/10; static: 0/10, 2/10
- copying tasks (dates, numbers, names) work; world-knowledge categorization
  (entity boxes) and judgment (urgency probes) fail — hence the template design
- v1 synthesis never saw the email, only pass notes → "receipt" x4,
  urgency leakage ("high-priority") in summaries
- parallel slots: only ~13% faster (iGPU saturated); pass cache: re-runs 0.8s
- Vulkan vs CPU: pp +74%, tg -20% → net ~30% faster on this prompt-heavy load
- harness: eval/run.py --workers 4; eval/score.py new.json old.json

## Plan A archive (stage-by-stage v1 tuning — superseded by template design)

Phases were: temp 0 → synthesis grounding (feed email, drop urgency notes) →
entity flattening → actions w/o implicit box → urgency probe rework (2d) →
synthesis wording. Absorbed into Phase 2 rules above except 2d (parked, urgency).
