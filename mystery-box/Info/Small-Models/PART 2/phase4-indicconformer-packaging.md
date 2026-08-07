# Phase 4 — packaging IndicConformer (turnkey runbook)

**Status: BLOCKED on transcription-engine support (NOT hosting).** The app code
is already ready — the per-language tier ladder (`resolveTiersForLanguage`,
Phase 3) auto-absorbs any catalog model, so the instant a loadable IndicConformer
is in the catalog it appears in the ladder for Bengali/Urdu/Tamil/etc. with **no
further UI work**.

## The real blocker (corrected)
Hosting is NOT the problem: the app downloads models from any public Hugging Face
repo (`ModelSource::HuggingFace { repo_id }`) and caches them locally — no DW
Bridges CDN needed. The problem is **format + engine architecture support**:

- The engines only load a fixed set of model *types*, each with a dedicated
  loader: `transcribe-cpp` GGUF archs = parakeet, canary, cohere_asr, whisper,
  gigaam, sensevoice, moonshine, granite_speech, qwen3_asr, funasr_nano, voxtral;
  `transcribe-rs` ONNX types = Parakeet, Moonshine, SenseVoice, GigaAM, Canary,
  Cohere.
- IndicConformer (Hybrid CTC-RNNT Conformer) is **not one of them**. The official
  weights are NeMo; community **ONNX** conversions exist (e.g. Hindi) but no GGUF
  and nothing that matches an existing loader's I/O contract.
- `transcribe-cpp` / `transcribe-rs` are **external crates we don't control**, so
  adding IndicConformer as a new architecture isn't a change we can make here.

### What would actually unblock it (any one of)
1. Upstream `transcribe-cpp` or `transcribe-rs` adds IndicConformer / Conformer
   CTC-RNNT support, and a compatible GGUF/ONNX is published on HF → then it's
   just a catalog entry (steps below), no hosting.
2. A bespoke conversion that reshapes IndicConformer to *exactly* match an
   existing supported loader (e.g. the Parakeet ONNX contract, incl. tokenizer /
   decoder) — high effort, uncertain, needs real runtime testing.
3. A community publishes a drop-in build for one of the supported engines.

Until one of those exists, Phase 4 cannot complete. **In the meantime Indic
languages are NOT broken** — Phase 3's ladder already offers Whisper (Small →
Large) for them; they just don't yet get the faster specialised model.

Do NOT add a catalog entry before a *loadable* build exists — it would point at a
model the engine can't open and break model loading.

## The model
- **AI4Bharat IndicConformer 600M multilingual** —
  <https://huggingface.co/ai4bharat/indic-conformer-600m-multilingual>
- License **MIT** (commercial OK). Conformer / NeMo, hybrid CTC-RNNT, ~0.6B.
- 22 Indic languages: as, bn, brx, doi, gu, hi, kn, ks, kok, mai, ml, mni, mr,
  ne, or, pa, sa, sat, sd, ta, te, ur. (Covers 9 of our top-15 gap languages.)
- Details + why it was chosen: docs/language-model-research.md.

## Steps

1. **Pick the runtime format.** Two supported paths:
   - GGUF via transcribe-cpp (how the catalog GGUF models are built), OR
   - ONNX via transcribe-rs (how the legacy Parakeet/Canary ONNX models run).
   Decide by which conversion is cleaner for a NeMo Conformer CTC-RNNT. NeMo has
   first-class ONNX export, so ONNX/transcribe-rs is likely the lower-friction
   path; confirm transcribe-rs accepts a Conformer CTC-RNNT ONNX graph (Parakeet
   is the closest precedent — same NeMo lineage).
3. **Convert.** Export from NeMo → chosen format. Verify a local round-trip:
   transcribe a known Indic clip and eyeball the text before packaging.
4. **Host.** Upload the converted files (+ tokenizer/vocab) to the DW Bridges HF
   org, mirroring the layout of an existing catalog model
   (`handy-computer/parakeet-*-gguf` is the template — quant files, revision pin).
5. **Add the catalog entry** in `src-tauri/src/catalog/catalog.json`, copying an
   existing entry's shape. Fill honestly:
   - `id` / `slug` / `name` (name is internal only — the UI shows tier labels, so
     it won't surface to users),
   - `languages`: the 22 Indic codes above; `language_count: 22`,
   - `capabilities`: `lang_detect` (per model), `streaming: false`, `translate`,
   - `speed_score` / `accuracy_score` (0–100): from real benchmarks, not guesses —
     these drive the per-language ladder position and dot ratings,
   - `parameters: "0.6B"`, `default_quant`, `files`, `revision`, `license: mit`.
   Catalog entries are forced to `EngineType::TranscribeCpp` in catalog/mod.rs —
   if you take the ONNX/transcribe-rs path instead, follow the legacy model
   registration in model.rs rather than the catalog.
6. **Verify end-to-end:** `handy.exe --transcribe-file <indic.wav> --model <id>
   --json` returns sensible text; then in-app, set transcription language to e.g.
   Bengali → the Accuracy tab's ladder should now include IndicConformer
   (automatically, via Phase 3), download + switch works, dictation transcribes.
7. **No UI/i18n changes needed.** The ladder, dots, wizard, and language filter
   (Phase 2) all pick it up from the catalog data.

## Acceptance
Bengali (and the other Indic gap languages) show a real, fast, MIT-licensed tier
in "Speed & Accuracy" instead of only slow Whisper — with zero code changes
beyond the catalog entry.
