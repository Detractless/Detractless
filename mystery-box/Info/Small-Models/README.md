# EmailSummarizer

A local, privacy-first email summarization pipeline that turns raw emails into a
single structured sentence plus an entity list — no cloud, no API keys, all models
run on the same AMD iGPU workstation that reads the mail.

**Output format:**
```
Email from noreply@pnc.com, likely an automated service. It informs the user that
their PNC Virtual Wallet account statement is ready for the period ending June 30.
List of mentioned entities: PNC, Virtual Wallet
```

---

## Champion result (config 076, sealed 2026-07-17)

After 76 configs and a 22-email stratified validation set, the pipeline achieves
**40/40 training and 84/84 validation (100% both sets)**, blind-tested on 31 fresh
emails with 3 defects found and fixed. The stack: Gemma 4 E2B Q4\_K\_M on the iGPU
(purpose + stage-1 summary) → Falconsai T5-60M on CPU (compress) → GLiNER small
in-process (entities) → deterministic render. Batch throughput ~17–20s/email; single-
email steady-state ~12s. Speed tier (067): 80/84 at ~5s/email.

---

## Start here

| Document | What it answers |
|---|---|
| **[CHAMPION.md](CHAMPION.md)** | Reproduce the 076 stack exactly — servers, flags, prompts, commands, expected scores |
| **[LESSONS.md](LESSONS.md)** | What to do correctly — 10 directives grounded in measured results |
| **[MISTAKES.md](MISTAKES.md)** | What went wrong and the rule for next time — 11 documented incidents |
| **[EXPERIMENTS.md](EXPERIMENTS.md)** | Compressed config history — era table + one-line verdict per config |
| **[eval/README.md](eval/README.md)** | Harness manual — run.py, score.py, frozen-config law, gold files |

---

## Plans

| Document | Contents |
|---|---|
| **[plans/FINETUNE.md](plans/FINETUNE.md)** | Three-specialist LoRA on Qwen3.5-0.8B (next phase) |
| **[plans/CORPUS.md](plans/CORPUS.md)** | Gmail/Proton/Outlook export + corpus processing pipeline |
| **[plans/INTEGRATION.md](plans/INTEGRATION.md)** | C# app integration (pending app-repo recon) |

---

## Archive

The full experiment journal and research notes live in `archive/` — the evidence base,
not the entry point:

- `archive/COVERAGE.md` — every config 001–076 with rationale, scores, and findings
- `archive/model_dossiers.md` — 8-model prompting/sampling/system-role research
- `archive/ner_research.md` — GLiNER/BERT-NER candidate research and decision
- `archive/prompt_lab_log.md` — purpose prompt iteration log (v1–v12)
- `archive/summary_audit.md` — Sonnet audit: honest vs keyword rate per config (001–039)
- `archive/RECIPE-QWEN3.md` — Qwen3 042/048 era record and compress-prompt lessons
- `archive/PLANS.md` — original phase design notes (Phase 4 C# section → plans/INTEGRATION.md)

---

## Project layout

```
EmailSummarizer/
├── pipeline/          # Python modules: extract, classify, summarize, ner, render, llm, config
├── eval/
│   ├── configs/       # One frozen directory per config (001–076)
│   ├── run.py         # Benchmark runner
│   ├── score.py       # Scorer
│   ├── validation_ids.json
│   ├── fresh30_ids.json
│   ├── gold_validation.json
│   └── gold_labels.json
├── runtime/
│   ├── start_server.ps1   # llama-server launcher (Vulkan + reasoning-off)
│   ├── t5_server.py       # T5 OpenAI-shim for Falconsai
│   └── models/            # GGUF + HuggingFace model files
├── plans/             # Forward-looking plans (FINETUNE, CORPUS, INTEGRATION)
└── archive/           # Superseded donor documents
```
