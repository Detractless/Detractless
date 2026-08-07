# Specialized language-model research (for the record)

**Date:** 2026-08-06. **Status:** research complete; nothing built.

Goal: for languages currently stuck on the slow, generic Whisper path, find
*specialized* models that are faster and/or more accurate — so DW Bridges can
serve more languages well, not just English.

## How a candidate must be judged (methodology)

Popularity (HF downloads/likes) is a weak *primary* signal — Whisper itself has
the most downloads, yet it is what we are trying to replace. Rank candidates by:

1. **Runnable in our engines (hard filter).** Must be convertible to GGUF or ONNX
   in an architecture DW Bridges supports (whisper, parakeet, canary, sensevoice,
   gigaam, moonshine, cohere, granite, voxtral, qwen-asr, fun-asr, nemotron). A
   wav2vec2 / Kaldi / raw-NeMo model that can't run here is out, however popular.
2. **Per-language accuracy** — from benchmarks (HF Open ASR Leaderboard, FLEURS,
   Common Voice WER) or the model's paper. Not downloads.
3. **Speed + size** — size (parameters) drives speed and RAM, so it drives
   low-end viability. Language *count* does not affect speed; a 0.6B multilingual
   model is as light as a 0.6B English one.
4. **License** — permissive / commercial-OK.
5. **Downloads / likes / community discussion** — tie-breaker and trust signal
   only. (Note: HF has *likes* + download counts, not star ratings or reviews;
   real "reviews" come from leaderboards, papers, and community threads.)

Also note the real cost: adding a model is a **packaging pipeline** (convert →
host under our namespace → add a catalog entry with the right architecture), the
same conversion the existing NeMo/GGUF catalog models went through. Research
yields a shortlist; each ship is work.

## The gap (from the current catalog)

The catalog spans **103 languages**, but:

- **42 already have a modern, non-Whisper option** — every major language: EN, ES,
  FR, DE, PT, IT, NL, RU (GigaAM), ZH/JA/KO/Cantonese (SenseVoice), Arabic, Hindi,
  Vietnamese, Polish, Turkish, etc. These are well served.
- **61 are Whisper-only** — the real gap. High-population ones: Bengali, Urdu,
  Punjabi, Marathi, Telugu, Tamil, Gujarati, Kannada, Malayalam, Hausa, Swahili,
  Yoruba, Amharic, Javanese, Pashto, Sindhi, Nepali, Sinhala, Serbian, Hebrew…

## Top 15 Whisper-only languages by global speakers — findings

The 15 split cleanly into a big win and a hard wall.

### Win: 9 of 15 (the Indic block) — AI4Bharat IndicConformer 600M

- Links: <https://huggingface.co/ai4bharat/indic-conformer-600m-multilingual>,
  <https://github.com/AI4Bharat/IndicConformerASR>
- Covers **22 Indic languages**, including **Bengali, Urdu, Punjabi, Marathi,
  Telugu, Tamil, Gujarati, Kannada, Malayalam** (9 of the 15) — plus extras
  already in our gap list (Assamese, Nepali, Sindhi, Odia, Sanskrit…).
- **MIT license** (commercial-OK).
- **Conformer / NeMo** architecture — same family as our Parakeet/Canary models —
  and **ONNX-exportable**, so it fits the existing engines (no new engine needed).
- **0.6B** — light, low-end friendly (same class as our current fast tiers).
- Verdict: **strongest catch.** One permissive, runnable, modern model retires
  slow Whisper for nearly the whole Indic gap.

### Wall: 6 of 15 (Hausa, Swahili, Yoruba, Amharic, Javanese, Pashto)

No clean option today:

- **Meta MMS** (<https://huggingface.co/facebook/mms-1b-all>) covers all 1,100+
  languages incl. these — but is **CC-BY-NC (non-commercial)** *and* **wav2vec2**
  (an architecture our engines don't run). Doubly disqualified.
- Otherwise mostly **Whisper fine-tunes** (e.g.
  <https://huggingface.co/NCAIR1/Hausa-ASR>) — they run (Whisper arch) and improve
  *accuracy*, but stay **Whisper-slow**, so no speed win.
- 2025 literature confirms African low-resource ASR is still open
  (<https://arxiv.org/html/2510.01145v1>): permissive, fast, non-Whisper models
  largely don't exist yet.

### Summary

| Language(s) | ~Speakers | Best option | Permissive | Runs on our engines | Faster than Whisper |
|---|---|---|---|---|---|
| Bengali, Urdu, Punjabi, Marathi, Telugu, Tamil, Gujarati, Kannada, Malayalam | ~1B | **IndicConformer 600M** | MIT ✅ | NeMo/ONNX ✅ | 0.6B ✅ |
| Hausa, Swahili, Yoruba, Amharic, Javanese, Pashto | ~400M | MMS (blocked) / Whisper fine-tune | ❌ / ⚠️ | ❌ / ✅ | ❌ |

## Recommendation

1. **Pursue IndicConformer.** High leverage — 9 of the top 15 (plus more Indic gap
   languages) with one MIT model that fits our engines. Next step is a scoped look
   at the packaging pipeline (convert to ONNX/GGUF, host, catalog entry).
2. **Keep Whisper for the 6 African/Indonesian/Pashto languages** for now — no
   permissive, runnable, *faster* model exists. If accuracy on one or two matters
   (e.g. Swahili, Amharic), a Whisper fine-tune is the only lever (accuracy up,
   speed unchanged). Revisit in ~6–12 months; the space is moving fast.

## Related decisions (see also)

- Per-language tier lineup + hiding unsupported languages + multilingual model
  swaps (e.g. Fast → Parakeet v3, 25 languages) — discussed separately; the tier
  ladder should adapt to the chosen language and only list languages some model
  supports.
- Low-end rule of thumb: pick by model *size*, not language count.
