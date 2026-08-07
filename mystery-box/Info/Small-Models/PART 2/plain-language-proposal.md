# Plain-language proposal (for approval — nothing changed yet)

Goal: make DW Bridges Dictation readable by someone with zero AI/tech vocabulary,
without dumbing it down. Change **English text values only** (keys stay, so all 23
locales keep resolving; other languages re-synced later or fall back).

## The glossary (consistency is the whole game)

Pick one word for each idea and use it *everywhere*:

| Instead of | Always say |
|---|---|
| hotkey, keyboard shortcut | **shortcut** |
| dictate, dictation, transcribe (the action) | **voice typing** / **type with your voice** |
| transcription (the produced text) | **your text** / **what you said** |
| model, AI model | **AI** (and the picker is framed as **accuracy**) |
| overlay | **pop-up** |
| streaming / live transcription | **Live** |
| chunk | **split** |
| Voice Activity Detection (VAD) | **silence trimming** |
| post-processing / "Cleanup with LLM" | **AI cleanup** |
| push to talk | **hold to talk** |

---

## 1. Navigation & tabs

| Key | Current | Proposed |
|---|---|---|
| `sidebar.models` | Models | **Accuracy** |
| `sidebar.personalization` | Personalization | Personalization *(keep)* |
| `sidebar.history` | History | History *(keep)* |
| `sidebar.settings` | Settings | Settings *(keep)* |
| `sidebar.help` | Help | Help *(keep)* |

## 2. Accuracy tab (was "Models")

| Key | Current | Proposed |
|---|---|---|
| `settings.models.title` | Transcription Models | **Speed & accuracy** |
| `settings.models.description` | Select a transcription model or download additional models. Different models offer varying levels of accuracy and speed. | **Choose how fast or how accurate your voice typing should be.** |
| `settings.models.tier.title` | Transcription tier | **Choose your level** |
| `settings.models.tier.accuracy` | Accuracy | Accuracy *(keep)* |
| `settings.models.tier.speed` | Speed | Speed *(keep)* |
| `settings.models.wizard.q1.title` | What matters more to you? | *(keep)* |
| `settings.models.wizard.q1.hint` | There is no single best model. Faster ones start typing sooner, slower ones make fewer mistakes. | **There's no single best choice. Faster options start typing sooner; slower ones make fewer mistakes.** |
| `settings.models.wizard.q2.title` | What do you mostly dictate? | **What do you mostly type by voice?** |
| `settings.models.wizard.q2.hint` | Some models are built for short bursts, others hold context over long passages. | **Some options are built for short bursts, others for long passages.** |
| `settings.models.wizard.result.hint` | Based on your answers, this is the best fit. | *(keep)* |

*(Tier labels Fastest/Fast/Balanced/Accurate/Most accurate stay — they're already plain. The full catalogue is Debug-gated, so its jargon is now power-user-only.)*

## 3. Settings page (the everyday screen)

| Key | Current | Proposed |
|---|---|---|
| `settings.preferences.hotkey` | Push-to-dictate hotkey | **Voice typing shortcut** |
| `settings.preferences.rebind` | Rebind | **Change** |
| `settings.preferences.unbound` | Not set | *(keep)* |
| `settings.preferences.more` | More settings | *(keep)* |
| `settings.preferences.moreDescription` | Everything else, tucked away. | *(keep)* |
| `settings.preferences.lightMode` | Light mode | *(keep)* |
| `settings.preferences.lightModeDescription` | Use the light theme. Off is dark. For system-follow, see the theme option under More settings. | **Use the light theme. Off is dark. To follow your system, see the theme option in More settings.** |
| `settings.preferences.chunkLongAudio` | Chunk long recordings | **Split long recordings** |
| `settings.preferences.chunkLongAudioDescription` | Split long recordings into ~30-second pieces at natural pauses before transcribing. Faster and easier on memory… Short dictations are unaffected. | **Split long recordings into ~30-second pieces at natural pauses before typing them out. Faster and easier on memory… Short recordings are unaffected.** |
| `settings.general.pushToTalk.label` | Push To Talk | **Hold to talk** |
| `settings.general.pushToTalk.description` | Hold to record, release to stop | *(keep)* |

## 4. Recording pop-up (overlay)

| Key | Current | Proposed |
|---|---|---|
| `overlay.transcribing` | Transcribing... | **Typing…** |
| `overlay.listening` | LISTENING | *(keep)* |
| `overlay.preparing` | WARMING UP | *(keep)* |
| `overlay.words` / `inserted` | {{count}} WORDS | *(keep)* |
| `overlay.noSpeech` | NO SPEECH | *(keep)* |
| `overlay.cleanupOn/Off` | CLEANUP ON / OFF | *(keep — already plain)* |

## 5. First run & permissions

| Key | Current | Proposed |
|---|---|---|
| `onboarding.subtitle` | To get started, choose a transcription model | **To get started, choose your speed and accuracy** |
| `onboarding.permissions.microphone.description` | Required to hear your voice for transcription. | **Required to hear your voice.** |
| `onboarding.permissions.accessibility.description` | Required to type transcribed text into your applications. | **Required to type your words into other apps.** |
| `accessibility.permissionsDescription` | DW Bridges needs accessibility permissions to type transcribed text. | **DW Bridges needs accessibility permission to type what you say.** |

## 6. Personalization

| Key | Current | Proposed |
|---|---|---|
| `settings.personalization.description` | Names, sites and terms the team says often. Added words are weighted during transcription. | **Names, sites and terms your team says often, so they come out right when you type by voice.** |
| `settings.personalization.teach.step1Hint` | …Do it in a few slots so we catch every way your model spells it. | **…Do it in a few slots so we catch every way the app spells it.** |
| `settings.personalization.teach.slotPlaceholder` | What your model heard… | **What the app heard…** |
| `settings.personalization.teach.reviewNothing` | Nothing to correct. Your model already spelled it right every time. | **Nothing to correct. The app already spelled it right every time.** |

## 7. Help & Feedback — already plain, keep as-is.

## 8. Lower priority — Advanced & Debug (power-user, behind Debug mode)

These are only reachable with Debug on, so they're lower stakes. Recommended:
keep the technical terms here (VAD, ONNX, transcribe.cpp, paste method, etc.) —
the people who open Debug expect them, and plain-washing them loses precision.
Two exceptions worth doing for consistency if you want:

| Key | Current | Proposed |
|---|---|---|
| `settings.models.cleanup.label` | Cleanup with LLM | **AI cleanup** |
| `settings.debug.postProcessingToggle.label` | Post Processing | **AI cleanup** |

## Decisions to confirm
1. **"voice typing"** as the standard verb (vs. "dictation"/"talk to type"). Recommended — it's the term Google/Windows use, so it's the most widely understood.
2. Overlay `Transcribing…` → **`Typing…`** — OK, or keep "Transcribing…"?
3. Tab is **Accuracy** (confirmed). Page title **"Speed & accuracy"** — good, or prefer just "Accuracy"?
4. Leave Advanced/Debug technical (recommended), or plain-wash those too?
