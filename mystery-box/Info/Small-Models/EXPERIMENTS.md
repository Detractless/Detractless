# EXPERIMENTS.md — Compressed config history

Navigation index to the 076-config evaluation campaign. For the full chronicle
(rationale, prompt text, per-email outputs) see `archive/COVERAGE.md`.

Scores use the format **T/V** where T = training set (/40 = 4 slots × 10 emails)
and V = validation set (/84 = 4 slots × 21 scored emails). Early configs (001–037)
predate the 4-slot harness; their scores are noted per-slot or as a fraction of
the 2-slot training set where applicable.

---

## Era table

| Era | Configs | Key technique | Peak train | Peak val | Verdict |
|---|---|---|---|---|---|
| **Model sweep** | 001–030 | Single-stage summarization, no echo gate; 10+ models screened | 20/20 (keyword) | — | Gemma4 E2B dominates (015/016 = 10/10 purpose); Qwen3 1.7B best small model; T5 trio too slow/broken; echo audit later revealed ≤30% of outputs were honest summaries |
| **Purpose v3 + hybrid** | 031–037 | v3 purpose prompt (asks-first + tag-ignore); hybrid style experiments; echo audit conducted | 10/10 purpose | — | v3 fixes the Elicit misclassification; hybrid is per-model (helps Qwen3, hurts LFM/MiniCPM); echo audit reveals single-stage is 0–40% honest — forces architecture rethink |
| **Two-stage + echo gate** | 038–044 | Two-stage summary (free → compress); echo gate added to scorer; per-slot model routing tested | 39/40 | 80/84 | Structural fix for echoing works; 038d (all-Gemma, 39/40 / 80/84) becomes first real champion; 044 dream team matches score but needs two servers |
| **Validation + Qwen3 refinement** | 045–048 | First held-out validation set; de-hinted stage-1; purpose-from-summary | 36/40 | 73/84 | Gemma4 generalizes better than Qwen3 (80 vs 71 val); 048 is best Qwen3 ever (73/84); Qwen3's purpose ceiling mapped: capability, not prompting |
| **Champion refinement** | 049–055 | Token diet (stage-1 120 tok, body_cap 2500); vendor sampling falsified | 39/40 | 81/84 | 051 = first deployable champion (81/84, 16.7s); sampling experiments (052/053) both worse than temp 0 — closed |
| **Speed + compressor screen** | 056–065 | Minimal prompt test; Falconsai T5-60M as compressor; shim concurrency; entities token diet | 40/40 | 83/84 | First perfect training score (060); graft-fix render makes Falconsai output grammatical (061); parallel 6/8 closed; entities diet 96→64 tokens is free (064) |
| **GLiNER integration** | 066–067 | GLiNER small in-process replaces generative entity slot | 40/40 | **84/84** | First perfect validation. GLiNER at 1/30 the GPU cost; speed tier (067) at ~5s/email |
| **Polish + framing** | 068–074 | Sentence-boundary trim; entity label/threshold/footer tuning; framing experiments | 40/40 | **84/84** | 070 sealed as render fix (meta-colon); 071 rejected despite 84/84 — reading audit found content damage; 073 is the future app-UI format option; 074 entity recipe finalized |
| **Blind testing + final** | 075–076 | Fresh-30 blind run; two-sentence template | 40/40 | **84/84** | 3 bugs found and fixed on fresh emails (all invisible to benchmark); 076 sealed as project champion |

---

## Config index

### Model sweep era (001–030)

| Config | Name | Score | Status | One-line verdict |
|---|---|---|---|---|
| 001 | baseline | 8/8 purpose+summary | superseded | LFM2.5 1.2B Q4; first run; ~70% echo rate revealed later by audit |
| 002 | qwen05b | 1/8 purpose | superseded | Qwen2.5 0.5B; purpose nearly random; echo 100% |
| 003 | minicpm5-1b | 2/9 purpose | superseded | MiniCPM5 1B; purpose fails; 40% honest summary but ~40% incoherent garbage |
| 004 | qwen35-08b | 4/7 purpose | superseded | Qwen3.5 0.8B v1; purpose marginal; 10% honest summary |
| 005 | qwen35-purpose-v2 | 7/7 purpose | superseded | v2 prompt helps Qwen3.5 0.8B purpose; summary still 10% honest |
| 006 | lfm12b-purpose-v2 | 5/8 purpose | superseded | LFM2.5 1.2B v2 prompt regression vs v1 on this model |
| 007 | qwen25-05b-purpose-v2 | 3/8 purpose | superseded | Qwen2.5 0.5B v2; marginal improvement; still near-useless |
| 008 | minicpm5-purpose-v2 | 4/9 purpose | superseded | MiniCPM5 v2; purpose no better; same incoherence |
| 009 | lfm2-12b-purpose-v1 | 5/9 purpose | superseded | LFM2 (older) 1.2B v1; weaker than LFM2.5 |
| 010 | lfm2-12b-purpose-v2 | 5/9 purpose | superseded | LFM2 v2; tied with v1 — model bottleneck not prompt |
| 011 | lfm25-12b-q8-purpose-v1 | 5/7 purpose | superseded | LFM2.5 Q8 v1; Q8 no better than Q4 on this model |
| 012 | lfm25-12b-q8-purpose-v2 | 7/7 purpose | superseded | LFM2.5 Q8 v2; matches Q4 v2 — quant not the bottleneck |
| 013 | gemma3-1b-purpose-v1 | 2/5 purpose | superseded | Gemma3 1B; too small; 20% honest summary |
| 014 | gemma3-1b-purpose-v2 | 2/5 purpose | superseded | Gemma3 1B v2; no improvement — model ceiling |
| 015 | gemma4-e2b-purpose-v1 | 9/10 purpose | superseded | **Gemma4 E2B Q4_K_M first appearance**; 9/10 purpose; but 30% honest summary |
| 016 | gemma4-e2b-purpose-v2 | 10/10 purpose | superseded | Gemma4 E2B v2; perfect purpose; still 30% honest summary — scorer blind to echo |
| 017 | qwen3-17b-purpose-v1 | 5/8 purpose | superseded | Qwen3 1.7B v1; 30% honest summary |
| 018 | qwen3-17b-purpose-v2 | 9/8 purpose+summary | superseded | Qwen3 1.7B v2; misses Elicit (asks→markets); prompt_lab baseline |
| 019 | qwen35-2b-purpose-v1 | 6/8 | superseded | Qwen3.5 2B v1; 30% honest summary |
| 020 | qwen35-2b-purpose-v2 | 9/8 | superseded | Qwen3.5 2B v2; marginal vs Qwen3 1.7B at higher cost |
| 021 | gemma4-iq3m-v1/v2 | 9/10 both | superseded | Gemma4 IQ3_M; Q3 quant matches Q4 on score; 30% honest |
| 022 | gemma4-qat-q2kxl-v1/v2 | 6–7/8 | superseded | Q2 quant; quality degrades; 20% honest |
| 023 | deepseek-r1-15b-think | 8/10 purpose | superseded | DeepSeek-R1 1.5B think; 30% honest; thinking slower AND not better |
| 024 | qwen3-17b-think | 5/10 purpose | superseded | Qwen3 1.7B think; thinking hurts purpose (5/10 vs 9/10 no-think); 30% honest |
| 025 | qwen35-2b-think | killed | superseded | Run killed; cosmetic prompt reorder already showing regression |
| 026 | qwen35-08b-think | not run | superseded | Created, never run — thinking already falsified by 023/024 |
| 027 | minicpm5-1b-think | not run | superseded | Created, never run — same reason |
| 028 | t5-email-summarizer | 5/7 purpose | superseded | wordcab T5-small; 61s wall; 0% honest summary (all broken/truncated) |
| 029 | flan-t5-base | 3/6 purpose | superseded | flan-T5 250M; 139s wall; 0% honest |
| 030 | lamini-flan-t5 | 5/8 purpose | superseded | LaMini-Flan-T5 248M; 127s wall; 10% honest |

### Purpose v3 + hybrid era (031–037)

| Config | Name | Train | Status | One-line verdict |
|---|---|---|---|---|
| 031 | qwen3-17b-purpose-v3 | 10/8 | superseded | v3 purpose prompt (10/10); summary still 30% honest; echo confirmed |
| 032 | gemma4-e2b-purpose-v3 | 10/10 | superseded | Gemma4 v3; 10/10 purpose; 30% honest — echo audit imminent |
| 033 | gemma4-e2b-v3-notag | 9/10 | superseded | v3 without marketing tag; marginal regression; 30% honest |
| 034 | qwen3-17b-hybrid | 10/10 keyword | superseded | **Worst offender in audit**: 70% pure echo at keyword 10/10 |
| 035 | lfm25-12b-hybrid | 9/10 keyword | superseded | 0% honest — most convincing echo cheater; fluent paraphrase of subject |
| 036 | minicpm5-1b-hybrid | 9/10 keyword | superseded | 40% honest but 40% incoherent; hybrid doesn't fix MiniCPM |
| 037 | distilbart-news | 4/7 keyword | superseded | 40% honest — best honest rate in era despite lowest keyword score; 244s wall |

### Two-stage + echo gate era (038–044)

| Config | Name | Train | Val | Status | One-line verdict |
|---|---|---|---|---|---|
| 038a | clause-newprompt | 10/10/9/10 = 39/40 | — | superseded | Gemma4 new clause prompt; single-stage |
| 038b | newprompt-bodyonly | su 7 | — | superseded | Body-only view strips headers and hurts summary |
| 038c | oldprompt-bodyonly | su 7 | — | superseded | Same — header stripping is harmful |
| **038d** | **twostage** | **39/40** | **80/84** | **superseded (→049)** | **Two-stage clause; 191s wall; single-server quality champion at the time** |
| 038e | twostage-markdown | 39/40 | — | superseded | Markdown pre-pass: same score, 344s — no gain, closed |
| 039d | qwen3-twostage | broken | — | superseded | Compress v1 hint list → Qwen3 parrots list (1/10 summary) |
| 039e | qwen3-twostage-md | broken | — | superseded | Markdown + compress v1; same parrot failure |
| 040d | qwen3-twostage-v2 | fake 9/10 | — | superseded | Compress v2 worked example → Qwen3 copies example verbatim 3/10 |
| 041d | qwen3-twostage-v3 | 10/10/8/6 = 34/40 | — | superseded | Compress v3 bare constraints; honest but entities weak |
| **042** | **qwen3-hybrid-twostage** | **36/40** | **71/84** | **superseded** | **Best Qwen3 speed; hybrid all slots; 129s; compress v3 works** |
| 043 | dreamteam | 10/10/8/10 = 38/40 | — | superseded | Qwen3 + Gemma4 entities; needs two servers; iGPU OOMs co-hosting |
| **044** | **dreamteam-cap28** | **39/40** | **75/84** | **superseded** | **Cap 28 words recovers salary/detail facts; best if both models fit in memory** |

### Validation + Qwen3 refinement era (045–048)

| Config | Name | Train | Val | Status | One-line verdict |
|---|---|---|---|---|---|
| 045 | qwen35-2b-twostage | 35/40 | — | superseded | Qwen3.5 2B at 042 recipe; dominated by 042 |
| 046 | minicpm5-twostage | 21/40 | — | superseded | Two-stage doesn't fix MiniCPM incoherence |
| 047 | qwen3-purpose-from-summary | 36/40 | 72/84 | superseded | Purpose reads stage-1 summary (+3 val); exposes deadline hint leak |
| **048** | **qwen3-pfs-dehinted** | **36/40** | **73/84** | **superseded** | **Best Qwen3 ever; de-hinted stage-1 fixes hallucinated "deadline"; su 10/10 train** |

### Champion refinement era (049–055)

| Config | Name | Train | Val | Wall | Status | One-line verdict |
|---|---|---|---|---|---|---|
| 049 | gemma4-pfs | 38/40 | 81/84 | 31s | superseded | 038d + purpose-from-summary + de-hinted stage-1 + cap28; first 81 val |
| 050 | gemma4-pfs-trimmed | 38/40 | 81/84 | 25s | superseded | Token diet (stage-1 120 tok, body 2500): −30% wall, zero quality cost |
| **051** | **gemma4-trimmed-lean** | **38/40** | **81/84** | **16.7s** | **superseded** | **051 = 050 minus purpose-from-summary (pure overhead on Gemma); first practical champion** |
| 052 | gemma4-official-sampling | 38/40 | 79/84 | — | closed | Gemma vendor temp 1.0: −2 val; temp 0 confirmed better |
| 053 | qwen3-official-sampling | 35/40 | 70/84 | — | closed | Qwen vendor temp 0.7: −3 val; informs-collapse unchanged — capability ceiling |
| 054 | qwen35-08b-lean | 30/40 | — | — | closed | 0.8B overwhelmed by v3 rules; below its own v2-era best |
| 055 | lfm25-12b-lean | 28/40 | — | — | closed | 4th LFM intervention, 4th regression; v1-era setup remains its best |

### Speed + compressor screen era (056–065)

| Config | Name | Train | Val | Wall | Status | One-line verdict |
|---|---|---|---|---|---|---|
| 056 | gemma4-minimal-prompt | 38/40 | — | 306s | closed | Bare "Summarize:" triggers markdown document reflex; +50% wall; "2–4 sentences" is load-bearing |
| 057 | qwen3-minimal-prompt | 36/40 | — | 215s | closed | Same: +103% wall; tie score; floor of instruction minimalism found |
| 058 | gemma-stage1-qwen17-stage2 | 39/40 | 83/84 | two-phase | superseded | Qwen3 as compressor: new val record 83/84; needs both models (two-phase on iGPU) |
| 059 | gemma-stage1-qwen08-stage2 | 38/40 | 76/84 | two-phase | superseded | 0.8B lacks compression headroom |
| **060** | **gemma-stage1-falconsai-stage2** | **40/40** | **83/84** | deployable | **superseded** | **First perfect train; Falconsai T5-60M CPU co-exists with Gemma iGPU; grammar broken** |
| **061** | **falconsai-graftfix** | **40/40** | **83/84** | **19.5s** | **superseded** | **Graft-fix render makes Falconsai output grammatical; ties record AND deployable** |
| 062 | wordcab-compressor | 40/40 | 83/84 | — | closed | Score-tied with 061 but wrong agency on action emails; Falconsai keeps crown |
| 063 | lamini-compressor | 39/40 | 83/84 | — | closed | 4× size of Falconsai, no gain |
| **064** | **entities-diet** | **40/40** | **83/84** | **19.5s** | **superseded** | **Entities decode 96→64 tokens: free (identical scores); new champion recipe** |
| **065** | **falconsai-solo-clause** | **40/40** | **79/84** | **~10s** | **superseded by 067** | **Speed tier origin; Falconsai does all summarization; GPU does only purpose** |

### GLiNER integration era (066–067)

| Config | Name | Train | Val | Wall | Status | One-line verdict |
|---|---|---|---|---|---|---|
| **066** | **gliner-champion** | **40/40** | **84/84** | **~17s** | **superseded by 069** | **First perfect validation (100%); GLiNER in-process entities; GPU does purpose + stage-1 only** |
| **067** | **gliner-speed** | **40/40** | **80/84** | **~5s** | **active speed tier** | **GPU does only the 8-token purpose call; speed tier (should inherit 074 entity recipe)** |

### Polish + framing era (068–074)

| Config | Name | Train | Val | Status | One-line verdict |
|---|---|---|---|---|---|
| 068 | polish | 39/40 | 83/84 | superseded | Sentence-boundary trim at cap 28 accidentally kept only sentence-1 (subject-shaped → echo); $13.28 case dropped |
| **069** | **polish-cap45** | **40/40** | **84/84** | **superseded by 070** | **Cap 45 words: room for two full sentences; 0/22 mid-word ellipses; entity noise filter; clean output** |
| **070** | **meta-colon** | **40/40** | **84/84** | **superseded by 074** | **Render fix: meta-framed clauses get colon connector; sealed champion at the time** |
| 071 | no-meta-prompt | 40/40 | 84/84* | **rejected** | Keyword 84/84 but reading audit found content damage: PNC lost card-locked event, CVS led with boilerplate, UDG lost password action; also substituted "the message" 4× |
| 072 | neutral-framing | 40/40 | 82/84 | closed | Delete "email" from framing: −2 val AND Gemma still said "email" 4×; prompt cosmetics falsified |
| 073 | header-format | 40/40 | 84/84 | parked | `From {sender} ({type}, {purpose}): {summary}` — future app-UI format; adoptable as pure render change |
| **074** | **entities-polish** | **40/40** | **84/84** | **superseded by 076** | **Threshold 0.45, footer zone, near-dup merge, label set finalized; SEALED entity recipe** |

### Blind testing + final (075–076)

| Config | Name | Train | Val | Status | One-line verdict |
|---|---|---|---|---|---|
| **075** | **fresh30** | 40/40 | 84/84 | **active (blind set)** | Fresh-30 blind run: 3 bugs found (rstrip, footer-wipe, giant-line); all fixed; benchmark intact |
| **076** | **two-sentence** | **40/40** | **84/84** | **PROJECT CHAMPION** | Two-sentence template kills double-that run-on; render-only change on 074 pipeline; all bugs fixed |

---

## Reading this table

- **Status = superseded**: a later config in the same lineage improved on it.
- **Status = closed**: the experiment was a deliberate test with a negative result (no further work warranted on that axis).
- **Status = rejected**: achieved equivalent scores but was rejected after a reading audit found content damage invisible to the keyword scorer.
- **Status = active**: currently in use.
- Scores marked with `*` passed keyword scoring but failed a reading audit — see 071.
- Details on every config (prompts, per-email outputs, rationale): `archive/COVERAGE.md`.
