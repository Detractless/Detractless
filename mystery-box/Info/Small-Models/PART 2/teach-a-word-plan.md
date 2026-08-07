# Teach-a-Word — implementation plan

A personalization feature: the user teaches the app a term it keeps mis-hearing by
**recording it a few times**; the app captures *what the current model actually
transcribes* for each take, turns the distinct wrong outputs into
correction rules, and silently rewrites those misfires to the correct spelling on
every future dictation.

Grounded in the codebase audit (Aug 2026). Model-agnostic: works on the default
Parakeet model, where prompt-biasing is unavailable and post-correction is the
only lever.

## Why this shape

- The default model (Parakeet, transcribe-rs/GGUF non-whisper) exposes **no**
  prompt/hotword/vocabulary hook. Whisper's `initial_prompt` is the only native
  bias and is whisper-only + weak on proper nouns. So the durable, universal
  mechanism is **post-transcription substitution**, which the app already does
  for `custom_words` and filler words.
- The teach flow's value over the existing flat `custom_words` list: it captures
  the model's *exact confusion set* from reality (e.g. "DW Bridges" → "the WB
  ridges") instead of hoping a fuzzy matcher connects a blind list entry to an
  arbitrary mangling.

## Data model

New persisted setting, kept **separate** from `custom_words` (both coexist):

```rust
// settings.rs
pub struct TaughtWord {
    pub id: String,               // uuid
    pub canonical: String,        // the correct spelling to emit
    pub variants: Vec<String>,    // captured mis-transcriptions → canonical
    pub enabled: bool,
}
// AppSettings:
#[serde(default)] pub taught_words: Vec<TaughtWord>,
```

- `default_taught_words() -> Vec::new()`; add to the explicit `get_default_settings()`
  constructor (required — it does not derive). Bump `settings_schema_version`;
  container-level `#[serde(default)]` means older stores load fine (empty list).
- Frontend mirror type in `bindings.ts` (auto-generated via tauri-specta once the
  Rust type derives `Type`).

## Backend commands (register in `lib.rs` `collect_commands!`)

1. `start_teach_recording() -> Result<(), String>`
   - Reject if a real dictation is active (`AudioRecordingManager::is_recording`).
   - Ensure a model is loaded (`tm.initiate_model_load()`); report not-ready so the
     UI can wait on `model-state-changed`.
   - `rm.try_start_recording("__teach__", vad_policy)` with a **lenient/disabled VAD
     policy** so a single short word isn't trimmed. Does NOT go through
     `TranscribeAction`, so **no dictation overlay appears** — correct.

2. `stop_teach_recording() -> Result<String, String>`
   - `rm.stop_recording("__teach__", gen)` → `Some(samples)`.
   - `spawn_blocking(move || tm.transcribe(samples))` → returns the transcript
     `String` directly to the awaiting frontend call. **No paste, no history, no
     event.** (Direct model of `commands::history::retry_history_entry_transcription`.)

3. `cancel_teach_recording()` → `rm.cancel_recording()` (discard).

4. `update_taught_words(words: Vec<TaughtWord>) -> Result<(), String>`
   - Persist whole array (model of `update_custom_words`); add `settingsStore` updater
     + binding.

## Correction integration

New helper beside `apply_custom_words`:

```rust
// audio_toolkit/text.rs
pub fn apply_taught_words(text: &str, words: &[TaughtWord]) -> String
```

- For each enabled word, replace any occurrence of a `variant` with `canonical`.
- **Whole-token/phrase, case-insensitive, punctuation-tolerant** matching;
  normalize (lowercase, collapse whitespace, strip surrounding punctuation) for the
  compare, emit the stored `canonical`.
- Longest-variant-first to avoid partial shadowing.
- Called in `post_process_transcription_text` (`transcription.rs:1711`) **first**,
  before the existing custom-words fuzzy pass and filler filtering, so exact
  captured mappings win. Applies to batch and streaming finalize paths (both route
  here). Fail-open (wrapped like the existing passes).

Phase-1 matching is **explicit variants only** (safe, predictable). Phonetic
generalization (reuse the existing Soundex helper within `word_correction_threshold`)
is a deliberate Phase-2 add, not built now.

## Safety valves

- Show every captured variant to the user before it becomes a rule.
- **Auto-flag risky variants**: any variant that is a common English word, equals
  the canonical, is <2 chars, or empty. Flagged ones default to *unchecked*.
- Never store the take that already equals canonical as a variant (it's the ✓).
- De-dupe variants; trim; cap length.

## Frontend (Personalization tab)

`PersonalizationSettings.tsx` gains a **"Taught words"** section above the existing
custom-words chips:

- List: each taught word → canonical, variant count, enable toggle, edit, delete.
- **"Teach a word"** → modal:
  1. Text field: correct spelling.
  2. Record control: click to start (`start_teach_recording`), click to stop
     (`stop_teach_recording` → returns transcript). Show "Model heard: …" per take.
     Mark takes equal to canonical with ✓ and exclude from variants.
  3. Soft cap ~5 takes with "Record another".
  4. Review table of distinct captured outputs as candidate variants (checkboxes;
     risky ones flagged + unchecked).
  5. Save → append `TaughtWord`, persist via `update_taught_words`.
- Gate recording on model-ready (listen `model-state-changed`); disable + show
  "Preparing model…" until loaded. Block if a real dictation is running.
- i18n keys under `settings.personalization.teach.*` in `en/translation.json`
  (other locales fall back to en; ESLint enforces *usage*, not presence in all 23).

## Non-goals / out of scope (Phase 1)

- No audio fingerprint / acoustic matching (heavy, brittle, no payoff over text).
- No native model word-boosting (runtime doesn't expose it).
- No passive "learn from manual edits" (Phase 2 candidate).
- No phonetic generalization yet (Phase 2).

## Files touched

- `src-tauri/src/settings.rs` — `TaughtWord` type, field, default, constructor,
  version bump.
- `src-tauri/src/audio_toolkit/text.rs` — `apply_taught_words`.
- `src-tauri/src/managers/transcription.rs` — call in `post_process_transcription_text`.
- `src-tauri/src/commands/…` — the 3 recording commands + `update_taught_words`.
- `src-tauri/src/lib.rs` — register commands.
- `src/components/settings/personalization/PersonalizationSettings.tsx` + new
  `TeachWordModal.tsx`.
- `src/stores/settingsStore.ts`, `src/bindings.ts` (generated).
- `src/i18n/locales/en/translation.json`.

## Verification

- `cargo test` (settings serde round-trip incl. `taught_words`), `cargo fmt`, `tsc`.
- Unit test `apply_taught_words`: exact/case/punctuation/whole-word boundaries,
  longest-first, risky-word skip.
- Manual: teach "DW Bridges", confirm captured misfires, confirm a later dictation
  containing a misfire is rewritten; confirm no dictation overlay during teach;
  confirm blocked while dictating.
