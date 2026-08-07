# Implementation plan — UI polish + language-aware models

**Date:** 2026-08-06. **Status:** approved direction, not yet built.
**Constraint:** no model hosting exists yet (no DW Bridges HF org / GitHub infra),
so anything requiring new hosted models (IndicConformer) is deferred to the end.

## Order of work

| Phase | What | Needs hosting? |
|---|---|---|
| 1 | Quick UI: remove legend · rail tab icons · surface UI-language control | no |
| 2 | Language-aware models, slice A: hide unsupported languages | no |
| 3 | Language-aware models, slice B: per-language tier ladder (data-driven) | no |
| 4 | IndicConformer packaging (convert · host · catalog) | **yes — blocked** |
| 5 | (last, later) Feedback repo/token, help video, installer build | partially |

A finding that reshaped the plan: the previously-discussed "swap Fast tier
Parakeet v2 → v3" is **rejected**. Catalog scores: v2 = speed 85 / acc 89 (EN
only); v3 = 79 / 88 (25 langs); Balanced (unified) = 79 / 90. v3 loses on BOTH
axes to Balanced, and the tier ladder's design rule (tiers.ts doc comment) is
that every rung must win on at least one axis. So v3 must never appear in the
*English* ladder — it belongs in the *per-language* ladder (Phase 3), where for
e.g. German it is one of the best options available. The naive swap is dead;
Phase 3 is its correct replacement.

---

## Phase 1 — quick UI polish (one sitting, all frontend, HMR)

### 1a. Remove the Speed/Accuracy legend
- `ModelComparison.tsx`: delete the legend `<div>` (the two `dwb-legend-dot`
  spans) from the header row; keep the `dwb-eyebrow` title. Rows already label
  Speed/Accuracy inline, so nothing is lost.
- Possibly drop `.dwb-legend-dot` from dwb.css if then unused (grep first —
  it may be used elsewhere).

### 1b. Rail tab icons
- `Sidebar.tsx`: add `icon` to each `SECTIONS_CONFIG` entry (lucide-react):
  Accuracy = Gauge · Personalization = UserRound · History = Clock ·
  Settings = **Settings (gear)** · Help = CircleHelp · Debug = Bug ·
  About = (no rail row).
- Render icon at ~15px before the label in the rail button; keep the 3px active
  marker behaviour. Rationale on record: a non-English reader can find Settings
  by the gear alone.

### 1c. Surface the Application-language control
- It already exists and works: `AppLanguageSelector` (writes `app_language`,
  live i18n switch), currently buried in Settings → "More settings" disclosure.
- `PreferencesSettings.tsx`: move `<AppLanguageSelector>` out of the Disclosure
  into the always-visible top `SettingsGroup` (near Microphone / shortcut), and
  remove it from the "More settings" General group so it isn't listed twice.
- No backend change. i18n keys already exist (`appLanguage.*`).

Verify phase 1: tsc, eslint, visual check of rail + Settings.

---

## Phase 2 — hide languages no model supports

Goal: the transcription-language dropdown (`LanguageSelector`) must only offer
languages that at least one *offered* model can transcribe. No more promising
Sundanese when nothing speaks it.

- Source of truth: union of `supported_languages` across the models the runtime
  actually offers (`useModelStore` models — same list the tier picker uses), or
  across the five TIERS models only (decision below).
- `LanguageSelector.tsx` / `languages.ts`: filter `SELECTABLE_LANGUAGES` against
  that union before rendering ("auto" always stays).
- **Decision to make at build time:** union over the *whole catalog* (largest
  honest set — anything downloadable) vs union over the *tier shortlist* (what
  the picker actually offers). Recommendation: whole catalog while the full list
  is Debug-gated = union over tiers + downloaded models; simplest defensible
  rule: models visible to the user today (tiers ∪ downloaded ∪ Debug catalog if
  Debug on).
- Keep the code data-driven: no hard-coded language list.

Verify: pick each remaining language, confirm at least one tier/downloaded model
supports it (spot check DE/ZH); confirm removed ones are gone.

---

## Phase 3 — per-language tier ladder (the architecture piece)

Goal: "Choose your level" adapts to the selected transcription language. English
keeps the current curated 5. Other languages get the best ladder available for
them, auto-derived from the catalog — which automatically absorbs future models
(incl. IndicConformer when Phase 4 lands).

Design (data-driven, no hand-maintained language×tier table):
1. Input: selected language L (from `selected_language`; for "auto" keep the
   English/default ladder), plus the runtime model list with
   `supported_languages`, `speed_score`, `accuracy_score`.
2. Filter: models supporting L.
3. Frontier: drop any model dominated on both axes (same rule as the English
   ladder). Sort by speed desc.
4. Cap at 5; label rungs from the existing tier keys (Fastest … Most accurate)
   by position — with N<5 use a sensible subset (e.g. 2 rungs → Fastest / Most
   accurate).
5. English/auto: keep the existing hand-curated TIERS (they encode judgment the
   frontier calc can't, e.g. streaming preference for Balanced).

Touch points:
- `tiers.ts`: new `resolveTiersForLanguage(models, lang)` beside the current
  `resolveTiers` (which stays as the English path).
- `ModelComparison.tsx` + `ModelWizard.tsx`: consume the language-aware resolver
  (both must share it so they never disagree — same rule as today).
- Wizard copy: q2/results reference the English tier timings
  (`approxSecondsFor30s`); for non-English ladders compute rough seconds from
  speed_score instead, or hide the seconds line (decision at build time —
  recommend: derive approx seconds from speed_score everywhere so one code path).
- Dot ratings: already rank-based over whatever columns exist — works unchanged
  for variable N.
- Edge cases: L supported by only 1 model → single-row ladder (fine); L
  supported by zero models → cannot happen after Phase 2 (dropdown filtered).
- The "custom model outside tiers" notice logic must account for
  language-ladders (a model legitimate for L is not "outside tiers").

Verify: EN unchanged; DE shows a multi-rung ladder incl. Parakeet v3 / Canary /
Cohere; ZH shows SenseVoice-family ladder; switching language updates the picker
live; wizard result always ∈ current ladder.

---

## Phase 4 — IndicConformer (BLOCKED on hosting; do not start)

Prereq: a DW Bridges home for converted models (HF org or equivalent).
When unblocked: convert AI4Bharat IndicConformer 600M (MIT, NeMo) to a supported
runtime format → host → add catalog entry (`languages`: the 22 Indic codes,
honest speed/accuracy scores) → Phase 3's ladder picks it up automatically for
bn/ur/pa/mr/te/ta/gu/kn/ml etc. Details + sources:
docs/language-model-research.md.

## Phase 5 — release plumbing (explicitly LAST, not now)

Feedback FEEDBACK_REPO + DWB_FEEDBACK_TOKEN · real help-video.mp4 · production
installer (`tauri build`). Deliberately out of scope until the app is done.

---

## Standing rules for all phases

- Backup (vN) after each phase lands and is user-verified.
- English i18n values only; keys stable across locales.
- Quality gates per phase: `npx tsc --noEmit`, eslint on touched files,
  cargo check/fmt if Rust touched (none planned before Phase 4).
- No em dashes in any new user-visible string; plain-language glossary applies
  (docs/plain-language-proposal.md).
