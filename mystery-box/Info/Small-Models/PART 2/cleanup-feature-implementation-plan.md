# "Clean up my dictation" — implementation plan

**Status: plan only. No code written.** Companion to
[cleanup-bakeoff-results.md](cleanup-bakeoff-results.md) (which model) and
[flowscribe-retrain-plan.md](flowscribe-retrain-plan.md) (optionally training our own).

Goal: an optional, **on-device, offline** pass that turns raw dictation into clean text — fixes
punctuation/capitalization, removes fillers and false starts, resolves spoken self-corrections — with
**no API key, no internet, nothing leaving the machine.**

## Decisions locked (2026-08-07)
- **Model:** ship `flowscribe-qwen2.5-0.5b-v2` (Q4_K_M GGUF) **as-is now**. Retraining our own
  ([flowscribe-retrain-plan.md](flowscribe-retrain-plan.md)) stays a future option.
- **The local model REPLACES the online API as the polish engine.** The cloud post-process path is
  *not* surfaced; the only user-facing polish is on-device. Cloud code stays **dormant in the backend**
  (not deleted — harmless, reversible, Debug-only if ever surfaced).
- **Delivery:** **bundled with the app** (works offline from first launch), not first-run download.
- **Runtime:** **Option A — bundled `llama-server` subprocess** (locked for v1).

## v1 build status (2026-08-07)
Implemented. Files: `src-tauri/src/managers/cleanup_llm.rs` (new), `settings.rs`
(`cleanup_enabled`), `actions.rs` (local cleanup path + short-utterance bypass + overlay),
`shortcut/mod.rs` (`change_cleanup_enabled_setting`), `lib.rs` (manager init + command),
`src/components/settings/CleanupDictation.tsx` (new toggle), `PreferencesSettings.tsx`,
`settingsStore.ts`, `bindings.ts`, and `i18n/locales/*` (all 24). Runtime bundled at
`resources/cleanup/llama-bin/`.

- **Frontend: verified** — `tsc --noEmit` and `eslint src` both pass.
- **Backend: compile-verified** — `cargo build` via the portable toolchain
  (`C:\Users\Calibro1\msvc-toolchain\env.bat`, which supplies MSVC + Windows SDK + CMake/Ninja +
  Vulkan) finishes clean and produces `target/debug/handy.exe`. (The stock VS18 BuildTools on PATH
  lacks the Windows SDK headers, so plain `cargo check` fails on `vswhom-sys`; always build via
  `env.bat`.) Two errors caught and fixed during the first build: a `settings` scope fix in
  `actions.rs` and a borrow-checker fix in `cleanup_llm.rs`.
- **Remaining asset:** `resources/cleanup/model.gguf` (~400 MB) not staged (disk). Feature degrades
  gracefully until it is present.

## Prerequisite note: no installer yet
There is no installer today (this is a portable build). "Bundled" does **not** require one: the model
and `llama-server` ship as **resources beside the portable exe** (Tauri `bundle.resources`), which
already gives offline-from-first-launch. A real installer (MSI/NSIS) is a *later* packaging step that
would wrap that folder; add it to the release checklist, but it does not block this feature.

---

## 0. The key insight: the pipeline already exists

The app already has a full (currently dormant, cloud-oriented) post-processing path. We are **reusing
it**, not building a new one. Verified in code:

- `actions.rs::process_transcription_output(app, transcription, post_process)` — the single hook
  point. Runs after transcription, before paste; already returns
  `ProcessedTranscription { final_text, post_processed_text, post_process_prompt }` and is already
  wired into history saving.
- `actions.rs::post_process_transcription(settings, text)` — resolves the active provider + model +
  prompt and calls the LLM.
- `llm_client.rs::send_chat_completion[_with_schema]` — POSTs to `{base_url}/chat/completions`,
  **OpenAI-compatible**, works against *any* endpoint including `http://127.0.0.1:PORT/v1`. Auth
  header is skipped when the API key is empty (already handled).
- `actions.rs::strip_think_block` — already strips `<think>…</think>` that local servers emit.
- Overlay already shows a "Polishing"/processing state during post-process
  (`emit_stream_working(StreamWorkKind::Polishing)` / `show_processing_overlay`).
- Cancellation already wraps post-processing (`complete_unless_cancelled`).
- Settings already carry the whole provider model: `post_process_enabled`, `post_process_providers`
  (list), `post_process_provider_id`, `post_process_api_keys`, `post_process_models`,
  `post_process_prompts`, `post_process_selected_prompt_id` (`settings.rs`).
- Shortcut actions already exist: `transcribe` (post_process=false) and
  `transcribe_with_post_process` (post_process=true), plus CLI `--toggle-post-process`.

**Therefore:** if we run a local llama-server and register it as a built-in provider whose
`base_url` is `http://127.0.0.1:PORT/v1` with an empty API key, the *entire* existing flow —
invocation, structured output, think-strip, overlay, history — works with essentially **zero changes
to the transcription/LLM code.** The real work is: (1) ship + manage a local runtime, (2) ship the
model, (3) replace the dormant power-user cloud UI with one simple toggle, (4) add a short-utterance
guard.

---

## 1. Architecture decision: how to run the model locally

Two options for the local inference runtime:

### Option A — bundled `llama-server` subprocess  ✅ recommended for v1
Ship the llama.cpp `llama-server` binary; the app spawns it on demand, waits for `/health`, and talks
to it over the existing OpenAI-compatible client.

- **Pros:** reuses `llm_client.rs` and the whole post-process path unchanged (biggest win); the exact
  runtime we already validated in the bake-off (build 9728); trivial to update the binary; crashes are
  isolated to a subprocess.
- **Cons:** must bundle a per-platform binary; manage process lifecycle (spawn, port, health,
  idle-shutdown, kill on quit).

### Option B — in-process GGUF via a Rust crate (`llama-cpp-2` / `mistral.rs` / `candle`)
Link llama.cpp into the app and run inference in-process.

- **Pros:** no subprocess, no port, single distributable.
- **Cons:** new inference module to write (chat template, sampling, streaming); does **not** reuse the
  OpenAI client path; extra native build complexity alongside the existing `transcribe-cpp`.

**LOCKED: Option A for v1** — dramatically less code because it reuses the proven post-process path.
The company target is Windows-first, and we already have a working Windows llama-server (CPU + Vulkan).
Revisit Option B later (v3) for a cleaner single-binary distribution if desired.

---

## 2. Components to build (Option A)

### 2.1 Bundle the runtime
- Add `llama-server` (Windows CPU build; optionally Vulkan) as a Tauri **sidecar/resource** in
  `tauri.conf.json` (`bundle.resources` or `externalBin`).
- Resolve its path at runtime via the existing portable/app-resource helpers.
- Cross-platform (mac/linux) binaries deferred until needed.

### 2.2 Local-LLM lifecycle manager  (new file: `src-tauri/src/managers/cleanup_llm.rs`)
A small manager, initialized like the others in `lib.rs`:
- `ensure_running()` — start `llama-server --model <gguf> --port <p> --ctx-size 4096 --host 127.0.0.1`
  on an ephemeral free port; wait for `GET /health`. Idempotent.
- `base_url()` — returns `http://127.0.0.1:<p>/v1` for the provider.
- **Cold-start UX:** first cleanup after launch loads the model (~1–3 s). Either warm up on app launch
  when cleanup is enabled, or show the existing processing overlay (reuse the "WARMING UP" pattern
  from the mic overlay) on the first request.
- **Idle unload:** shut the server down after N minutes idle to free RAM (mirror the existing
  `ModelUnloadTimeout` setting). 0.5B Q4 ≈ ~400 MB RAM, so keeping it resident is also fine.
- **Shutdown:** kill the child on app exit (and on toggle-off).

### 2.3 Cleanup-model asset  (bundled)
The GGUF (~400 MB, `flowscribe-qwen2.5-0.5b-v2` Q4_K_M).
- **Bundled as an app resource** (Tauri `bundle.resources`), sitting beside the portable exe so it
  works offline from first launch. Resolve its path via the existing portable/app-resource helpers.
- No download UI needed for v1 (delivery decision locked to bundle). A first-run download could return
  later as an option to shrink the installer, but is out of scope now.
- Note: **~400 MB** ships with the app.

### 2.4 Provider wiring
- Add a built-in provider, e.g. `PostProcessProvider { id: "local", label: "On-device", base_url:
  "http://127.0.0.1:<p>/v1", allow_base_url_edit: false, supports_structured_output: false }`
  (fill `base_url` dynamically from the lifecycle manager, or special-case `id == "local"` in
  `post_process_transcription` to inject the live URL).
- Empty API key (already supported). Default `post_process_provider_id = "local"`.

### 2.5 Settings — one simple toggle (local replaces cloud)
- Reuse `post_process_enabled` as the on/off. Default `post_process_provider_id = "local"` so the
  toggle drives the **on-device** engine only.
- The cloud multi-provider/API-key/prompt fields stay in the struct but are **not surfaced** (dormant;
  Debug-only if ever exposed). Company users see only: **"Clean up my dictation" [toggle]** + a
  one-line description.
- Consider a "Formatting style" dropdown later (flowscribe supports Verbatim/Casual/Auto/etc.).

### 2.6 Prompt
- Use flowscribe's **native** system prompt for best results:
  `"You are Flowscribe, an expert Speech-to-Text post-processing AI…"` with a style instruction
  (default: Auto). Seed it as a built-in `LLMPrompt` selected by default for the local provider.
- If we ship our own retrain, use whatever prompt we train against.

### 2.7 Short-utterance bypass  (fidelity guard)
- In `post_process_transcription` (or `process_transcription_output`), **skip cleanup when the raw
  transcription is under ~3–4 words.** Every model tested — including the winner — invents content on
  1–2 word fragments. Cheap, eliminates the worst failure mode.

### 2.8 Trigger model (decision — see §5)
- Simplest for a company product: when the toggle is on, apply cleanup to the **normal** transcribe
  flow (set `post_process=true` for the default action) so users don't need a second shortcut.
- Alternatively keep both shortcuts (plain vs cleaned) as upstream does.

---

## 3. Flow (after)

```
Audio → VAD → ASR (transcribe-cpp/rs) → raw text
      → OpenCC (if applicable)
      → [cleanup enabled AND words ≥ 4] ?
            → ensure llama-server running → POST /v1/chat/completions (local)
            → strip_think_block → cleaned text
      → paste/clipboard  +  save to history (raw + cleaned)
```

Everything after "raw text" is the existing `process_transcription_output` path.

---

## 4. Edge cases & risks

| Concern | Handling |
|---|---|
| Hallucination on 1–2 word inputs | Short-utterance bypass (§2.7) |
| Model changes the user's words | Inherent LLM risk; mitigated by fidelity-weighted model choice; history stores BOTH raw and cleaned so nothing is lost; consider a "show original" affordance |
| `<think>` leakage from local server | Already stripped by `strip_think_block` |
| Cold start latency | Warm up on enable, or overlay "WARMING UP" on first request (reuse mic-warmup pattern) |
| RAM / idle | Idle-unload via `ModelUnloadTimeout` mirror; ~400 MB resident otherwise |
| Cancellation mid-cleanup | Already wrapped in `complete_unless_cancelled` |
| Offline | Local server → works fully offline (the whole point) |
| Disk (~400 MB model) | First-run download with progress; tight but OK |
| Cross-platform binaries | v1 Windows-only; add mac/linux llama-server later |
| First-run without model downloaded | Toggle shows "downloading…"; fall back to raw text until ready |

---

## 5. Decisions

1. **Trigger:** cleanup applies to the **normal dictation shortcut** when enabled (recommended
   default; still open to a separate shortcut later). *Proposed for v1.*
2. **Model source:** ✅ ship `flowscribe-qwen2.5-0.5b-v2` as-is now. *(locked)*
3. **Model delivery:** ✅ bundle with the app. *(locked)*
4. **Style control:** ship just "clean up" (Auto) for v1; expose Verbatim/Casual later. *Proposed.*

---

## 6. Phased rollout

- **v1 (minimal, Windows):** bundle llama-server + lifecycle manager; first-run model download;
  built-in "local" provider; single toggle (cloud UI behind Debug); native prompt; short-utterance
  bypass; apply on normal flow. Ship + validate.
- **v2 (polish):** idle-unload tuning; "show original" toggle; formatting-style dropdown; mac/linux
  binaries; optionally swap in our own retrained model.
- **v3 (optional):** in-process runtime (Option B) for single-binary distribution.

---

## 7. Testing
- Reuse the bake-off harness (`scratchpad/harness.py`) and the 50-dictation test set as a
  **regression suite**: after wiring, run cleanup end-to-end on those inputs and diff against the
  bake-off's recorded outputs to confirm parity.
- Manual: cold-start latency, cancel mid-cleanup, offline, toggle off/on, 1-word input (bypass fires),
  long input, history shows raw + cleaned.

---

## 8. Files to touch (concrete)
- **New:** `src-tauri/src/managers/cleanup_llm.rs` (server lifecycle); possibly
  `src-tauri/src/commands/cleanup.rs` (model download + enable/disable commands).
- `src-tauri/src/lib.rs` — init the new manager.
- `src-tauri/src/settings.rs` — default the local provider + local prompt; ensure defaults; keep cloud
  fields Debug-gated.
- `src-tauri/src/actions.rs` — short-utterance bypass; inject live localhost URL for `id == "local"`;
  (optional) apply post_process on the default action when enabled.
- `src-tauri/tauri.conf.json` — bundle llama-server sidecar + (optional) model resource.
- **Frontend:** new "Clean up my dictation" toggle component + i18n keys (all 23 locales); a Settings
  entry (Preferences or a small section); download-progress UI. `bindings.ts` regenerates
  automatically.
- `src-tauri/src/llm_client.rs` — expected **no change** (localhost is just another OpenAI endpoint).
