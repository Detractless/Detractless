# Handy → DW Bridges UI Implementation Plan

Retheme Handy's configuration window and live dictation overlay to match the
DW Bridges Dictation **2A** mockup ("Settings window + dictation overlay").

Source of truth: `DW Bridges Dictation.html`, section `#2a` (+ the `LIVE` overlay
block beside it). Values below were read off the rendered DOM, not eyeballed.

> **Status: implemented.** All six phases have landed. See
> [Deviations from the plan](#deviations-from-the-plan) at the end for the places
> where the built code differs from what was written here, and
> [Verification](#verification) for what was and was not checked.

---

## 0. Design tokens extracted from 2A

| Token                | Value                                                                | Used for                                                                  |
| -------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `--dwb-accent`       | `#4D78A4` rgb(77,120,164)                                            | active nav border, radio fill, toggles, buttons, top rule, waveform peaks |
| `--dwb-accent-hover` | `#3F6690`                                                            | button hover                                                              |
| `--dwb-ink`          | `#17242E`                                                            | display headings                                                          |
| `--dwb-text`         | `#25333F`                                                            | primary text                                                              |
| `--dwb-text-2`       | `#3C4B57`                                                            | nav labels                                                                |
| `--dwb-muted`        | `#5B6B78`                                                            | secondary text                                                            |
| `--dwb-muted-2`      | `#7B8B98`                                                            | tertiary / descriptions                                                   |
| `--dwb-faint`        | `#8B9AA6`                                                            | eyebrow labels, meta                                                      |
| `--dwb-placeholder`  | `#A3B0BB`                                                            | input placeholder, `+` separators                                         |
| `--dwb-surface`      | `#FBFBFC`                                                            | window / card body                                                        |
| `--dwb-card`         | `#FFFFFF`                                                            | option rows, inputs, chips                                                |
| `--dwb-card-sel`     | `#F4F7FA`                                                            | selected option row                                                       |
| `--dwb-rail`         | `#F5F7F9`                                                            | sidebar                                                                   |
| `--dwb-rail-active`  | `#ECEFF3`                                                            | active/hover nav row                                                      |
| `--dwb-titlebar`     | `#F1F3F5`                                                            | title bar, overlay stage                                                  |
| `--dwb-border`       | `#E2E6EA`                                                            | card + input borders                                                      |
| `--dwb-border-2`     | `#E5E9ED`                                                            | sidebar right edge                                                        |
| `--dwb-chip-border`  | `#D9E2EA`                                                            | chips, key caps                                                           |
| `--dwb-rule`         | `#E8EBEE`                                                            | horizontal dividers                                                       |
| `--dwb-track`        | `#CFD7DE`                                                            | toggle OFF track                                                          |
| `--dwb-wave-1 / -2`  | `#C6D3E0` / `#A9BED3`                                                | waveform low/mid bars                                                     |
| `--dwb-rec`          | `#B05252`                                                            | recording dot                                                             |
| `--dwb-ok`           | `#4F8A68`                                                            | inserted dot                                                              |
| `--dwb-shadow`       | `0 18px 40px -18px rgba(20,50,64,.45), 0 0 0 1px rgba(20,50,64,.10)` | window/card elevation                                                     |

Type: **Cormorant Garamond** (display: window title `DWB`, page headings) and
**Barlow** 300/400/500/600 (everything else). Both are already embedded as
woff2 data URIs in the bundle and will be extracted to
`public/fonts/` and registered via `@font-face` (Tauri runs offline — no CDN).

Radii: window `8px`, cards/inputs `6px`, chips `20px`, key caps `4px`,
overlay card `12px`, badges `3px`.
Letter-spacing is load-bearing: eyebrow labels `.14em`, nav `.02em`,
`DWB` wordmark `.1em`, overlay status `.14em`.

---

## Phase 1 — Theme foundation

1. **`src/styles/theme.css`** — replace the pink/warm Handy palette with the
   table above. Keep the existing `--color-*` semantic names so the ~90 files
   using `text-mid-gray`, `bg-logo-primary`, `border-mid-gray/20` etc. remap
   automatically instead of being touched one by one:
   - `--color-logo-primary` → `--dwb-accent`
   - `--color-background-ui` → `--dwb-accent`
   - `--color-background` → `--dwb-surface`
   - `--color-text` → `--dwb-text`
   - `--color-mid-gray` → `--dwb-muted-2`
     Then add the DWB-specific tokens on top for the new components.
2. **Dark theme.** 2A is light-only. Handy ships a working light/dark/system
   `ThemeSelector`. Plan: keep the selector and derive a dark counterpart from
   the same hues (ink `#101A21` surface, `#6E9BC9` accent) so dark mode doesn't
   regress into unreadable pink remnants. Light is the canonical DWB look.
3. **Fonts.** Extract Barlow 300/400/500/600 + Cormorant Garamond 400/500/600
   woff2 from the bundle manifest → `public/fonts/`; `@font-face` in `App.css`;
   set `font-family: Barlow` on `:root`, add a `.font-display` utility for
   Cormorant. Base `font-size` moves 15px → 14px to match 2A's scale.
4. **`App.css`** — add DWB utility layer: `.dwb-card`, `.dwb-input`,
   `.dwb-eyebrow`, `.dwb-rule`, `.dwb-chip`, `.dwb-keycap`.

Deliverable: existing UI already reads as DW Bridges before any restructuring.

---

## Phase 2 — Window chrome

- `src-tauri/src/lib.rs:876` — main window is `680×570` with native decorations.
  2A shows a **custom flat title bar**: 34px tall, `--dwb-titlebar`, 1px bottom
  border, `DW BRIDGES DICTATION` at 11px `.12em` on the left, `– ▢ ✕` glyph
  buttons (34×34) on the right.
- Switch the builder to `.decorations(false)` and render `TitleBar.tsx` in
  React, `data-tauri-drag-region` on the strip, wired to
  `getCurrentWindow().minimize() / toggleMaximize() / hide()` (hide, not close —
  Handy is a tray app).
- Size: 2A's window is 480×554. Handy's panes carry more content, so keep
  `680×570` as `inner_size`, drop `min_inner_size` to `560×520`.
- Windows-only: `apply_window_theme` at `lib.rs:894` becomes a no-op path once
  decorations are off; leave the call guarded rather than deleted.

---

## Phase 3 — Sidebar + navigation

Rewrite `src/components/Sidebar.tsx` to the 2A rail:

- 150px wide, `--dwb-rail`, `1px solid --dwb-border-2` right edge, `18px 0` pad.
- `DWB` wordmark: Cormorant 17px, `.1em`, `#3F5D7D`, padded `0 16px 18px`.
- Nav rows: `9px 16px`, 13.5px, `.02em`, **no icons**. Active = `--dwb-rail-active`
  background + `3px solid --dwb-accent` left border (logical `border-inline-start`
  so RTL still works); inactive = transparent bg + transparent 3px border so
  labels never shift. Hover → `--dwb-rail-active`.
- Bottom block (`margin-top:auto`): current transcribe hotkey (11px,
  `--dwb-muted`) and `v{version} · internal` (11px, `--dwb-faint`) — pulled from
  `useSettings()` and `getVersion()`.
- Content pane gets the 3px `--dwb-accent` rule pinned across its top.

**Tab set.** 2A specifies three tabs; you asked to keep History. Recommendation —
**four rows**, since History is a genuine destination and a 4th row costs
nothing visually:

| Row             | Component                           | Notes                                      |
| --------------- | ----------------------------------- | ------------------------------------------ |
| Models          | `ModelsSettings` (rebuilt, Phase 4) |                                            |
| Personalization | new `PersonalizationSettings`       | wraps `CustomWords` as chips               |
| History         | `HistorySettings` (restyled)        | kept per your instruction                  |
| Settings        | new `SettingsPane`                  | merges the survivors of General + Advanced |

Debug (`Ctrl+Shift+D`) and About stay reachable but move **out of the rail**:
Debug renders as an extra row only when `debug_mode` is on (unchanged behaviour);
About collapses into the sidebar footer version line + an "About" link.
Post-processing folds into Models as the "Cleanup with LLM" toggle (see below).

`src/App.tsx` keeps its `SECTIONS_CONFIG` switch; only the entries change.
`Footer.tsx` is **removed** — the model selector moves into the Models tab and
the version/update line moves into the sidebar footer, matching 2A.

---

## Phase 4 — Content panes

Shared pane shell: `padding: 26px 24px`, `flex column`, Cormorant 23px `.03em`
heading, eyebrow labels 11px `.14em` `--dwb-faint`, `1px --dwb-rule` dividers.

### Models

2A's three-tier radio list (Fast / Balanced / Accurate) maps onto a curated
subset of Handy's model catalogue. Per your note, **the transcription-tier
concept is out of scope for now** — so this pane keeps Handy's real model list
and download/manage behaviour, restyled as 2A option rows:

- Each model = `--dwb-card` row, `1px --dwb-border`, `6px` radius, `12px 14px`,
  title 14px + subtitle 12px `--dwb-muted-2` on the left, 16px radio on the
  right (`1.5px --dwb-border` ring unselected → `5px --dwb-accent` fill selected).
  Selected row: `1.5px --dwb-accent` border + `--dwb-card-sel` background.
- Download progress bars reuse `ProgressBar` restyled to the accent.
- Below the divider: **Cleanup with LLM** toggle (= `post_process_enabled`),
  then a **LANGUAGE** eyebrow + `LanguageSelector` styled as the 2A select
  (white, `--dwb-border`, `▾` in `--dwb-faint`).
- The search + language-filter controls in the current `ModelsSettings` stay,
  restyled as 2A inputs.

### Personalization

New pane, straight from 2A: description line (12.5px, `line-height 1.6`),
`[input] [ADD]` row (accent button, 12px, `.08em`), chips (`20px` radius,
`--dwb-chip-border`, 13px, click-to-remove ✕), and an `N of 500 terms` counter.
Backed by the existing `custom_words` setting — `CustomWords.tsx` is refactored
from a textarea-style control into this chip editor.

### History

Keep all behaviour (infinite scroll, audio player, copy/retry/favourite/delete,
`PAGE_SIZE = 30`). Restyle only: entries become `--dwb-card` rows with
`--dwb-border`; `IconButton` accent colours swap from `logo-primary` to
`--dwb-accent`; header gets the Cormorant 23px title + the existing
"Open recordings folder" button restyled as a 2A secondary button. Add the
2A eyebrow grouping (`TODAY` / `EARLIER`) using `formatDateTime`.

### Settings

2A's Settings pane, populated from Handy's real settings:

- **MICROPHONE** eyebrow → `MicrophoneSelector` as a 2A select, plus the live
  input-level meter (5px track, `--dwb-rule`, accent fill).
- **PUSH-TO-DICTATE HOTKEY** eyebrow → `ShortcutInput` rendered as key caps
  (`Ctrl` `+` `Shift` `+` `D`, `4px` radius, `--dwb-chip-border`) with a
  `Rebind` accent text button that enters the existing capture mode.
- Divider, then 2A-style toggle rows (40×22 track, 16px knob, accent ON /
  `--dwb-track` OFF): Launch at sign-in (`AutostartToggle`), Keep in system tray
  (`ShowTrayIcon`), Play sound on capture (`AudioFeedback`), Show overlay
  (`ShowOverlay`), Push-to-talk (`PushToTalk`).
- Second group behind a "More" disclosure for the rest of today's Advanced pane
  (paste method, typing tool, clipboard handling, auto-submit, VAD, history
  limit, retention, model unload timeout, theme, app language, experimental).
  This is the **simplification**: nothing is deleted, but only nine controls are
  visible at rest instead of ~30.

`ToggleSwitch.tsx`, `Dropdown.tsx`/`Select.tsx`, `Button.tsx`, `Input.tsx`,
`SettingsGroup.tsx` and `SettingContainer.tsx` are restyled in place so every
untouched setting inherits the look. `SettingsGroup`'s title becomes the 2A
eyebrow; its card becomes `--dwb-card` on `--dwb-border`.

---

## Phase 5 — Live dictation overlay

`src/overlay/RecordingOverlay.css` (+ small `.tsx` changes). 2A's overlay is a
**396px card**, `12px` radius, `#FBFBFC`, `16px 18px` padding, shadow
`0 14px 34px -14px rgba(20,50,64,.35), 0 0 0 1px rgba(20,50,64,.12)` — flatter
and wider than Handy's 184px pill, and it **never shows the text**.

Three states, all specified in the mockup:

1. **Listening** — 10px `--dwb-rec` dot · 10-bar waveform, 38px tall, `3px` gap,
   `2px` radius, bars coloured `--dwb-wave-1 / -2 / --dwb-accent` by level ·
   `M:SS` timer 14px tabular-nums. Second row: `LISTENING` (11.5px, `.14em`) left,
   `STOP CTRL+SHIFT+D · ESC CANCEL` (10.5px, `.06em`, `--dwb-faint`) right.
2. **Transcribing** — accent dot · 5px determinate progress track
   (`--dwb-wave-1` bg, accent fill) · greyed timer. Status:
   `TRANSCRIBING · {MODEL}` / `CLEANUP ON|OFF`.
3. **Inserted** — single row: `--dwb-ok` dot · `INSERTED · N WORDS` ·
   `CTRL+Z TO UNDO`, then auto-dismiss after ~1.2s.

Consequences:

- Bar count `WAVE_BARS` 9 → **10**.
- The streaming-text panel (`.stext` / `.stext-cap` / `.scaret`) is **removed**
  per 2A's "never the text" rule. `StreamTextEvent` listeners stay wired but
  unrendered so the backend contract is untouched and the panel can be restored
  behind a flag.
- New "inserted" state: `RecordingOverlay.tsx` gains an `inserted` overlay state
  and a word count. Backend already emits `hide-overlay`; the word count comes
  from the final `StreamTextEvent.committed` before hide — no Rust change needed.
- The width-morph animation goes away (one fixed card width); keep the pop-in.
- `src-tauri/src/overlay.rs:46-51` — `OVERLAY_WIDTH/HEIGHT` 256×46 → **420×110**
  for every state; `OVERLAY_STREAM_*` collapses to the same size. Top/bottom
  offsets unchanged.
- Keep the transparent, click-through, always-on-top window and the existing
  top/bottom placement logic.

---

## Phase 6 — Cleanup & verification

- Remove `HandyHand` / `HandyTextLogo` usage from the rail (kept in the file
  tree for the tray/onboarding).
- Retheme `Onboarding` and `AccessibilityOnboarding` to the DWB palette — they
  are the first screen a new user sees and would otherwise still be pink.
- New i18n keys (below) added to `en`; `bun run check:translations` then reports
  the 22 other locales as missing — fill with English fallbacks.
- `bun run lint`, `bun run format:check`, `bun run build`, `cargo fmt`, then
  `bun run tauri dev` and screenshot each tab and each overlay state against
  the mockup.
- `tests/app.spec.ts` only asserts that the dev server responds and the page has
  `<html>`/`<body>` — no sidebar or label assertions, so **no Playwright changes
  are required**. `bun run test:playwright` should still pass unmodified.

### New i18n keys (`src/i18n/locales/en/translation.json`)

```
sidebar.personalization      "Personalization"
sidebar.settings             "Settings"
titlebar.appName             "DW BRIDGES DICTATION"
titlebar.minimize/maximize/close
settings.personalization.title / description / addPlaceholder / add / counter
settings.preferences.title / more            ("More settings")
settings.models.cleanup.label / description  ("Cleanup with LLM")
settings.shortcut.rebind     "Rebind"
overlay.listening            "LISTENING"
overlay.inserted             "INSERTED · {{count}} WORDS"
overlay.undoHint             "CTRL+Z TO UNDO"
overlay.stopHint             "STOP {{shortcut}} · ESC CANCEL"
overlay.cleanupOn / cleanupOff
```

`sidebar.general`, `sidebar.advanced`, `sidebar.postProcessing` become unused —
leave them in place (removing keys from 23 locale files buys nothing).

---

## File-change manifest

### New files

| Path                                                                  | Purpose                                                                   | Phase |
| --------------------------------------------------------------------- | ------------------------------------------------------------------------- | ----- |
| `public/fonts/*.woff2`                                                | Barlow 300/400/500/600, Cormorant Garamond 400/500/600                    | 1     |
| `scripts/extract-dwb-fonts.ts`                                        | one-shot: pull the woff2 data URIs out of the bundle into `public/fonts/` | 1     |
| `src/styles/dwb.css`                                                  | DWB token block + `@font-face` + `.dwb-*` utilities                       | 1     |
| `src/components/TitleBar.tsx`                                         | 34px custom title bar + window controls                                   | 2     |
| `src/components/settings/personalization/PersonalizationSettings.tsx` | chip editor pane                                                          | 4     |
| `src/components/settings/preferences/PreferencesSettings.tsx`         | the new "Settings" pane                                                   | 4     |
| `src/components/ui/Disclosure.tsx`                                    | "More" collapse used by Preferences                                       | 4     |
| `src/components/settings/HotkeyDisplay.tsx`                           | `Ctrl + Shift + D` key caps + Rebind                                      | 4     |

### Modified files

| Path                                                                                                            | Change                                                      | Phase |
| --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | ----- |
| `src/styles/theme.css`                                                                                          | repoint every `--color-*` at DWB values; add dark pair      | 1     |
| `src/App.css`                                                                                                   | import `dwb.css`; base font Barlow; `font-size` 15px → 14px | 1     |
| `src-tauri/src/lib.rs:876-882`                                                                                  | `decorations(false)`, `min_inner_size(560,520)`             | 2     |
| `src/App.tsx`                                                                                                   | render `<TitleBar/>`; drop `<Footer/>`; new section list    | 2,3   |
| `src/components/Sidebar.tsx`                                                                                    | full rewrite to the 2A rail                                 | 3     |
| `src/components/settings/index.ts`                                                                              | export the two new panes                                    | 3,4   |
| `src/components/settings/CustomWords.tsx`                                                                       | textarea/list → chip editor                                 | 4     |
| `src/components/settings/models/ModelsSettings.tsx`                                                             | 2A option rows; absorb cleanup toggle + language select     | 4     |
| `src/components/settings/history/HistorySettings.tsx`                                                           | restyle only; add TODAY/EARLIER eyebrows                    | 4     |
| `src/components/settings/ShortcutInput.tsx`                                                                     | key-cap rendering via `HotkeyDisplay`                       | 4     |
| `src/components/ui/{ToggleSwitch,Button,Input,Select,Dropdown,Slider,Badge,SettingsGroup,SettingContainer}.tsx` | restyle to DWB                                              | 1,4   |
| `src/components/shared/ProgressBar.tsx`                                                                         | accent fill                                                 | 4     |
| `src/overlay/RecordingOverlay.tsx`                                                                              | `WAVE_BARS` 9→10; drop text panel; add `inserted` state     | 5     |
| `src/overlay/RecordingOverlay.css`                                                                              | rewrite to the 396px card                                   | 5     |
| `src-tauri/src/overlay.rs:46-51`                                                                                | 256×46 → 420×110; collapse `OVERLAY_STREAM_*`               | 5     |
| `src/components/onboarding/*.tsx`, `AccessibilityPermissions.tsx`                                               | DWB palette                                                 | 6     |
| `src/i18n/locales/*/translation.json`                                                                           | new keys (23 files)                                         | 6     |

### Removed

| Path                                                                 | Note                                                                                                                                       |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `src/components/footer/Footer.tsx`, `src/components/footer/index.ts` | 2A has no footer                                                                                                                           |
| —                                                                    | `src/components/model-selector/` and `update-checker/` are **kept**, re-mounted inside the Models pane and the sidebar footer respectively |

Of the 42 files that reference `logo-primary` / `background-ui` / `mid-gray`,
only the ~20 listed above need hand editing; the rest inherit Phase 1's remap.

---

## Acceptance criteria

**Phase 1** — app builds; every surface renders in DWB blue/slate with zero pink
pixels in light _and_ dark; Barlow renders offline with DevTools network
disabled; no layout shifts from the 15px → 14px base.

**Phase 2** — title bar is 34px, drag moves the window, `–` minimises, `▢`
toggles maximise, `✕` hides to tray (app keeps running); Windows snap layouts
still reachable via `Win+←/→`.

**Phase 3** — four rail rows in order; active row shows the 3px accent border
with no text reflow when switching; hotkey + version pinned to the rail bottom;
Debug row appears only after `Ctrl+Shift+D`; RTL locales mirror correctly.

**Phase 4** — each pane matches the mockup at 480px content width; Models can
still download, select, and delete a model; Personalization add/remove persists
to `custom_words`; History keeps infinite scroll, playback, copy, retry,
favourite, delete; every previously-reachable setting is still reachable
(nine visible, rest behind "More").

**Phase 5** — overlay is one 396px card in all three states; listening shows 10
level-reactive bars + `M:SS`; transcribing shows a determinate bar and the model
name; inserted shows the word count and self-dismisses; **no transcript text is
ever rendered**; the native window is 420×110 with no clipping at either
placement.

**Phase 6** — `lint`, `format:check`, `build`, `cargo fmt --check`,
`check:translations`, `test:playwright` all clean.

---

## Risks & rollback

| Risk                                                          | Mitigation                                                                                                          |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `decorations(false)` breaks Windows snap / system menu        | Phase 2 is a single-commit, self-contained change — revert `lib.rs` and drop `<TitleBar/>` to restore native chrome |
| Token remap leaves stray pink in an unvisited screen          | grep for `logo-primary`/`background-ui` after Phase 1; the 42-file list above is the checklist                      |
| Overlay resize clips on HiDPI / at the 4px Windows top offset | `overlay.rs` already scales offsets; verify at 100/125/150/200% before sign-off                                     |
| Removing the stream-text panel loses a feature users rely on  | Listeners stay wired; the panel is deleted from render only, so restoring it is a JSX change, not a rewrite         |
| Cormorant/Barlow licensing for redistribution                 | Both are SIL OFL — bundling in `public/fonts/` is permitted; add the OFL notice alongside                           |

Phases 1 → 6 are independently shippable and land in that order; the app is in a
usable, buildable state after each.

---

## Decisions (settled)

1. **Four tabs** — Models · Personalization · History · Settings.
2. **Dark mode kept** — derive a DWB dark palette from the same hues
   (`#101A21` surface, `#6E9BC9` accent); the theme selector stays.
3. **Custom title bar** — `decorations(false)` + a React title bar matching 2A.
   Windows snap/aero behaviour is re-implemented via the drag region and
   `toggleMaximize()`; verify snap layouts on Windows before sign-off.

---

## Deviations from the plan

Recorded because the sections above describe intent, and the code is what ships.

| Planned                                              | Built                                  | Why                                                                                                                                                                                          |
| ---------------------------------------------------- | -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scripts/extract-dwb-fonts.ts` (bun)                 | `scripts/extract-dwb-fonts.mjs` (node) | bun isn't required to run it; plain node keeps the one-shot script dependency-free. Faces are matched by base64 fingerprint, not byte length — length collided across weights.               |
| DWB tokens added to `App.css`                        | Own file, `src/styles/dwb.css`         | Both windows import it (main + overlay); inlining in `App.css` would have left the overlay without the tokens.                                                                               |
| Sidebar keeps `GeneralSettings` / `AdvancedSettings` | Both **deleted**                       | Every control they held moved into the new Settings pane. Leaving them would have been unreachable dead code.                                                                                |
| Settings pane shows a live mic level meter           | **Omitted**                            | The backend only emits `mic-level` during a recording, so in the configuration window the bar would always read empty — a broken-looking control rather than a level.                        |
| Post-processing keeps a rail row                     | Folded into the Models pane            | Follows the mockup, where "Cleanup with LLM" lives under the model list. The detail form renders directly beneath the toggle when enabled, so nothing became unreachable.                    |
| About reachable from the rail                        | Reached from the rail's version line   | 2A has exactly the four rows. Theme, app language and "what's new" moved out of About into Settings, where they are discoverable.                                                            |
| Overlay hide delay unchanged                         | `overlay.rs` 300ms → **1400ms**        | The "INSERTED · N WORDS" face has to outlive the `hide-overlay` event. With nothing to confirm the card fades immediately and the extra time is an empty, transparent, click-through window. |
| —                                                    | `ProgressBar.tsx` i18n fix             | Two pre-existing `i18next/no-literal-string` errors blocked the lint gate; fixed with real keys rather than suppressed.                                                                      |
| Waveform tier by CSS attribute selector              | Tier computed in the component         | `[style*="height: 1"]` matches both `12%` and `100%` — the selector approach was silently wrong.                                                                                             |

## Verification

Run from `Handy-main/` on 2026-08-05. npm was used in place of bun (bun is not
installed on this machine); the underlying commands are identical.

| Gate                 | Result                                                                                                                     |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `tsc --noEmit`       | pass                                                                                                                       |
| `eslint src`         | pass                                                                                                                       |
| `prettier --check .` | pass                                                                                                                       |
| `check-translations` | pass — 23/23 locales complete                                                                                              |
| `vite build`         | pass — fonts emitted to `dist/fonts` (18 files), accent `#4d78a4` present in the bundle, zero occurrences of the old pinks |
| `cargo fmt --check`  | pass                                                                                                                       |
| Visual               | Both windows rendered against the built CSS and compared to the mockup, in light and dark.                                 |

### `cargo check` — pass, with a caveat about the toolchain

The Rust edits are three small, mechanical changes:

- `lib.rs` — `.decorations(false)`, `min_inner_size(560, 520)`
- `overlay.rs` — window constants, hide delay
- `capabilities/default.json` — five `core:window:allow-*` permissions

The linker on this machine is **not on the system PATH by design**. It lives in a
portable, no-admin MSVC + Windows SDK + CMake + Ninja tree under
`C:\Users\Calibro1\msvc-toolchain\`, documented in the `IKS Automation App` fork's
`FORK-NOTES.md`. `cargo` only works after sourcing it:

```
cmd /c "call C:\Users\Calibro1\msvc-toolchain\env.bat && cargo check"
```

Run that way, `cargo check` reaches Handy's own code and **passes: exit 0, zero
errors, zero warnings.**

One detour on the way there. The first run failed in `transcribe-cpp`'s CMake
step with `Could NOT find Vulkan (missing: Vulkan_LIBRARY Vulkan_INCLUDE_DIR
glslc)` — zero rustc errors, so nothing to do with this work. Upstream Handy asks
for `dynamic-backends` + `vulkan` on Windows x86_64 (`Cargo.toml`), and Vulkan
needs the LunarG SDK, which the portable toolchain deliberately does without. The
fork solves this by building that target CPU-only. To get the compiler as far as
Handy's Rust, that same one-line change was applied **temporarily** and then
reverted — `Cargo.toml` in this tree is untouched and still requests Vulkan.

So: **this tree does not build on this machine as-is.** That is a pre-existing
mismatch between upstream's GPU backend and the no-admin toolchain, not a
consequence of the retheme, and changing the acceleration backend is a product
decision rather than part of a UI change.

### Still to check on a real run

`cargo check` type-checks; it does not exercise the window at runtime. On Windows,
confirm:

1. the window still snaps (`Win`+arrow) and resizes with no native chrome;
2. the title bar's `–` / `▢` / `✕` behave, and `✕` hides to tray rather than quitting;
3. the overlay is not clipped at 100/125/150/200% display scaling, in both the
   top and bottom placements.
