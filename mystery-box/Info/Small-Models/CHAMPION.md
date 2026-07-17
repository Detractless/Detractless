# CHAMPION.md — The 076 stack: reproduce it completely

**Config:** `076-two-sentence`
**Sealed:** 2026-07-17
**Scores:** 40/40 training · 84/84 validation (100% both) · blind-tested on 31 fresh emails
(3 defects found, 3 fixed, 0 open, benchmark scores intact throughout)

> **Speed tier** (separate config): `067-gliner-speed` — 80/84 val at ~5s/email wall.
> GPU does only the 8-token purpose call. Should inherit the 074 entity recipe when next touched.

---

## 1. The stack at a glance

| Layer | Component | Detail |
|---|---|---|
| **Model — comprehension** | Gemma 4 E2B Q4_K_M | llama-server Vulkan, full iGPU offload |
| **Model — compress** | Falconsai/text_summarization (T5-60M) | t5_server.py shim, CPU only |
| **Model — entities** | GLiNER small-v2.1 (166M) | in-process Python, CPU only |
| **Inference server** | llama-server (Vulkan build) | `runtime/llama-bin-vulkan/llama-server.exe` |
| **T5 shim** | `runtime/t5_server.py` | OpenAI-compatible, BoundedSemaphore(4) |
| **Server flags** | `--ctx-size 16384 --parallel 4 --threads 6 --reasoning off --reasoning-budget 0` | reasoning off is mandatory — see M-04 |
| **Ports** | Gemma: 8001 · Falconsai: 8003 | configurable; defaults in config.json |
| **Temperature** | 0.0 everywhere | validated across all models; see L-03 |
| **Style** | inverted (email in system, instruction in user) | all slots |
| **Body cap** | 2500 chars | `extraction.body_cap` |

---

## 2. Call sequence per email

Each email produces exactly these calls (in order):

### Step 1 — extract.py (no model calls)
- HTML → text via `html_to_text()`
- `clean_text()`: URL masking → footer cutoff (bottom-third only) → junk-line filter
  → **catastrophic-shrink guard** (`<200 chars out of >600 in → fall back to uncut text`)
- Body capped at 2500 chars
- Marketing flag set if footer pattern detected
- `email_block()` assembles: `[MARKETING: ...]\nFROM: ...\nSUBJECT: ...\n\n{body}`

### Step 2 — sender_type (classify.py)
- **Code rules first** (short-circuit, 0ms):
  - `noreply_is_automated`: FROM address matches `no[-_.]?reply|notifications?@|...` → `automated service`
  - `footer_is_business`: marketing flag set → `business`
- Falls back to Gemma if neither rule fires (8 tokens, temp 0)
- Options: `business` / `individual person` / `automated service`

### Step 3 — purpose (classify.py)
- Gemma, v3 prompt (`purpose.txt`), inverted style, 8 tokens, temp 0
- Options: `asks` / `instructs` / `markets` / `informs`
- Precedence order: asks > instructs > markets > informs (highest-precedence match wins)
- `footer_fallback_markets`: if model output unclear AND marketing flag set → `markets`
- Key prompt invariants: asks-rule evaluated **before** promo-rule; explicit instruction
  to ignore `[MARKETING: ...]` tag (see M-02, L-08)

### Step 4 — summary clause, two-stage (summarize.py)

**Stage 1 — Gemma free summary** (`free_summary.txt`, inverted)
- Max 120 tokens, temp 0
- Prompt: "Summarize the email above in 2-4 sentences. Describe what happened, what is
  offered, and what the recipient is expected to do." (de-hinted — no noun lists)
- Output: 2–4 sentence free-form summary of body content

**Stage 2 — Falconsai compress** (`falconsai_compress.txt`, port 8003)
- Input: stage-1 output only (email is NOT in context — echo is architecturally impossible)
- Max 64 tokens, temp 0
- Trim mode: `sentence` — cut at last full sentence within 45-word cap rather than mid-word
- Max words cap: 45

### Step 5 — entities (summarize.py → ner.py)

GLiNER backend (in-process, CPU):
- Model: `urchade/gliner_small-v2.1` (166M, loads lazily once per process)
- Labels: `person` / `company` / `organization` / `product` / `device` / `online community or group`
- Threshold: **0.45** (raised from 0.3 — junk is low-confidence; see L-04)
- Chunking: ~1200 chars on paragraph boundaries (handles 384-token BERT window)
- `footer_exclude`: drop entities appearing only in last 25% of text
- `dedup`: near-duplicate merge with mutual-twin tie-break (longer/earlier raw form wins)
- **Code rule `sender_is_entity`**: FROM display name inserted at position 0
- **Code rule `entity_noise_filter`**: drops UI chrome, greetings, generic device nouns,
  addresses (defined in `summarize._ENTITY_NOISE` + `_ADDRESS_RE` + `_GREETING_RE`)
- All returned names then verified: must appear literally in email text (haystack check)
- Display cap: 6 entities

### Step 6 — render.py (no model calls)

Template (from config):
```
Email from {sender}, likely {article} {sender_type}. It {purpose_verb} the user about {clause}.
List of mentioned entities: {entities}
```

**Graft-fix** (`render_graft_fix: true`): detects whether the clause is a full sentence
(finite verb within first ~12 words, or multi-sentence) and routes accordingly:
- Phrase clause → `...the user about {clause}` (unchanged)
- Sentential clause, purpose != asks → `...the user that {clause}`
- Sentential clause, purpose == asks → `...asks the user to respond: {clause}`
- Meta-framed clause (`The email announces...`) → `...the user: The email announces...`

**Possessive-safe capitalization**: first word lowercased unless it is a known proper noun
from subject/sender/entities. Possessive stripped with `re.sub(r"'s$", "")`, not `rstrip`
(see M-06).

**Article**: `a` / `an` by first character of sender_type.

---

## 3. Starting the servers

### Terminal 1 — Gemma (iGPU, port 8001)

```powershell
cd C:\Users\Calibro1\Documents\EmailSummarizer
.\runtime\start_server.ps1 -ModelFile gemma-4-E2B-it-Q4_K_M.gguf -Port 8001
```

Wait for the server log to show `all slots are idle` before proceeding.
Flags applied by the script: `--n-gpu-layers 99 --ctx-size 16384 --parallel 4
--threads 6 --reasoning off --reasoning-budget 0 --log-disable`

> **Do not launch bare llama-server by hand for benchmark runs.** The script's
> `--reasoning off` is mandatory for Gemma; omitting it produces empty `content`
> (21 cached empty strings observed — see M-04).

### Terminal 2 — Falconsai T5-60M (CPU, port 8003)

```powershell
cd C:\Users\Calibro1\Documents\EmailSummarizer
python runtime/t5_server.py --model runtime/models/hf/Falconsai/text_summarization --port 8003
```

Wait for `Ready: text_summarization on http://127.0.0.1:8003`.
The shim uses `BoundedSemaphore(4)` + `torch.set_num_threads(3)` for concurrency.
No GPU required; runs alongside Gemma on the same machine.

> **GLiNER** loads lazily in-process the first time an entities slot runs (~10s one-time,
> then ~0.5s per email). No separate server needed.

---

## 4. Running the benchmark

### Against the 10-email training set

```powershell
# Scores must be: 40/40 (sender 10, purpose 10, summary 10, entities 10)
python eval/run.py --config 076-two-sentence --no-cache --force
python eval/score.py eval/results/076-two-sentence.json
```

### Against the 22-email validation set

```powershell
# Expected: 84/84 (21/21 per slot)
python eval/run.py --config 076-two-sentence --ids eval/validation_ids.json --no-cache --force
python eval/score.py eval/results/076-two-sentence.json --gold eval/gold_validation.json
```

### Against the fresh-30 blind set

```powershell
# Expected: reference baseline only — fresh emails may vary; check outputs by hand
python eval/run.py --config 076-two-sentence --ids eval/fresh30_ids.json --no-cache --force
python eval/score.py eval/results/076-two-sentence.json --gold eval/gold_labels.json
```

### Single email (steady-state latency check)

```powershell
python eval/prompt_lab/single_email.py --config 076-two-sentence --id <rowid>
# Expect ~12s model call time + ~10s GLiNER first-load (subsequent runs: ~12s)
```

---

## 5. Expected scores and performance

| Set | S | P | Su | E | Total | Wall/email |
|---|---|---|---|---|---|---|
| Training (10 emails) | 10 | 10 | 10 | 10 | **40/40** | — |
| Validation (22 emails) | 21 | 21 | 21 | 21 | **84/84 = 100%** | ~17–20s (batch, 4 workers) |
| Blind (31 fresh emails) | — | — | — | — | 3 defects found & fixed | ~12s (single-email calls) |

Performance note: the ~17–20s batch throughput is with 4 parallel workers sharing the
iGPU via `--parallel 4`. Single-email sequential latency is ~38s (Gemma calls) + ~0.5s
(GLiNER) + ~0.5s (Falconsai). The token diet (stage-1 cap 120, entities cap 64) accounts
for ~30% of the speed gain vs earlier champions.

---

## 6. Config snapshot (config.json)

The frozen source of truth is `eval/configs/076-two-sentence/config.json`.
Key values reproduced here for quick reference:

```json
{
  "models": {
    "default":    { "url": "http://127.0.0.1:8001", "id": "gemma-4-E2B-it-Q4_K_M" },
    "compressor": { "url": "http://127.0.0.1:8003", "id": "falconsai-summarization" }
  },
  "slots": {
    "sender_type": { "temperature": 0.0, "max_tokens": 8,  "style": "inverted" },
    "purpose":     { "temperature": 0.0, "max_tokens": 8,  "style": "inverted",
                     "precedence": ["asks","instructs","markets","informs"] },
    "clause": {
      "temperature": 0.0, "max_words": 45, "trim": "sentence",
      "stages": [
        { "prompt": "free_summary.txt",      "max_tokens": 120 },
        { "prompt": "falconsai_compress.txt", "max_tokens": 64,
          "input": "previous", "model": "compressor" }
      ]
    },
    "entities": {
      "backend": "gliner",
      "gliner_model": "urchade/gliner_small-v2.1",
      "threshold": 0.45,
      "labels": ["person","company","organization","product","device","online community or group"],
      "footer_exclude": true, "dedup": true, "max_tokens": 64, "display_cap": 6
    }
  },
  "code_rules": {
    "noreply_is_automated": true, "footer_is_business": true,
    "footer_fallback_markets": true, "sender_is_entity": true,
    "entity_noise_filter": true
  },
  "extraction": { "body_cap": 2500, "trim_boilerplate": true, "marketing_flag": true },
  "template": "Email from {sender}, likely {article} {sender_type}. It {purpose_verb} the user about {clause}.",
  "render_graft_fix": true
}
```

---

## 7. Known open items (all optional)

| Item | Notes |
|---|---|
| Full fresh-set labeled certification | Corpus plan: plans/CORPUS.md. Certify before any 100% accuracy claim in production. |
| Purpose-based routing | ~8–9s blended wall time; 067-speed does GPU only for purpose |
| App integration | Render format 073 (`From {sender} ({type}, {purpose}): {summary}`) is the UI option; adoptable as a pure render change |
| Fine-tuning phase | Three LoRA specialists on Qwen3.5-0.8B; plan: plans/FINETUNE.md |
| Speed tier entity recipe | 067-gliner-speed should adopt the 074 entity recipe (threshold 0.45, label set, footer_exclude, dedup) when next touched |
| C# integration | plans/INTEGRATION.md (pending app-repo recon) |
