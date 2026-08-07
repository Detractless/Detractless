# Audio enhancement / voice cleanup — research notes (ON HOLD)

**Status: parked (2026-08-06).** Investigated whether adding an audio-cleanup /
voice-enhancement stage would help. Conclusion: **not worth integrating right
now.** Revisit only if a clear need appears (users reporting bad transcription in
genuinely noisy environments, or a real demand for "studio-quality" saved
recordings). This note exists so the next attempt starts from the findings, not
from scratch.

## The original idea
"Clean up the microphone audio (like Voicemod) so the AI transcribes better."

## What was actually measured
A standalone test harness (outside the app, in `se-test/`) using the app's own
`handy.exe --transcribe-file --json` CLI (same Parakeet model the app uses) so
accuracy + latency were measured on **real user recordings**, not a lab dataset.

Model tested: **MossFormer2_SE_48K** (ClearerVoice-Studio) — a 2025 SOTA *denoiser*.

### Finding 1 — denoising does NOT help transcription (and hurts under noise)
- On the user's **real recordings** (already fairly clean): raw vs. enhanced
  transcripts were **byte-for-byte identical** across 6 clips. Enhancement is a
  **no-op for accuracy** on clean input.
- On **synthetically noised** clips (pink + babble @ 5 dB SNR): enhancement made
  WER **worse** every time (12.9%→22.6%, 20.0%→26.7%, 39.8%→52.3%).
- This matches independent 2025 research: **"When De-noising Hurts: A Systematic
  Study of Speech Enhancement Effects on Modern Medical ASR"** (arXiv 2512.17562)
  — enhanced audio lost to noisy audio in all 40 configs (up to 46.6% WER
  increase). Modern ASR (Parakeet/Whisper) is trained on huge noisy corpora and
  is already noise-robust; the denoiser's artifacts are OFF the recogniser's
  training distribution.
- **Takeaway:** never put an enhancer in front of the transcriber. Trust the
  model's built-in robustness + the existing VAD.

### Finding 2 — latency cost (this machine, CPU, AMD Radeon iGPU box)
- MossFormer2 enhancement ran at **~0.4–1.0× real-time** on CPU (a 42 s clip took
  ~42 s). One-time model load ~11–50 s. Transcription itself stays fast (~0.8–1 s
  warm). So enhancement would roughly double-to-match the wait per dictation.

### Finding 3 — the real goal was mis-framed
The user actually wanted the **voice to sound fuller / clearer / "professional"**
— a *restoration/enhancement* task — NOT *denoising* (which strips signal, drops
the level, and dulls the voice; that level drop is what the user noticed).

- Right category = **generative speech restoration**: **Resemble Enhance**
  (MIT, github.com/resemble-ai/resemble-enhance — tops DNSMOS) and **VoiceFixer**
  (MIT, github.com/haoheliu/voicefixer — also does bandwidth super-resolution for
  "presence"). Both 2024–2025, permissive, commercial-OK.
- **Crucial boundary:** these are GENERATIVE — they reconstruct the voice and can
  subtly alter words. Fine for **playback/export of saved recordings**; must
  **never** feed the transcriber.
- Level drop is separately fixable with **loudness normalization** (~-16 LUFS,
  e.g. `pyloudnorm`).

## If/when revisited — the plan
1. Scope it as **"make saved History recordings sound polished for playback/
   export"** only. NOT a transcription feature (proven dead end).
2. Use **Resemble Enhance** (quality leader) or **VoiceFixer**; add loudness
   normalization after.
3. Test on **genuinely noisy real recordings** from the user (fan/TV/café), raw
   vs. enhanced, and judge by ear — that's the only untested scenario where value
   could exist.

## Environment gotchas (so the next attempt doesn't re-hit them)
- Machine has only **Python 3.14** (too new for PyTorch). Used **`uv`** (installed
  to user space, no admin) to get **Python 3.12** and a venv at `se-test/.venv`.
- **Torch 2.13 CPU** installed fine; ClearerVoice/MossFormer2 works.
- **Resemble Enhance is blocked** on this box: it depends on `deepspeed==0.12.4`,
  which won't build on no-admin Windows, and its inference code
  (`resemble_enhance.enhancer.inference`) imports `deepspeed` at module load, so
  `--no-deps` doesn't rescue it. **VoiceFixer** (pure PyTorch, no deepspeed) is the
  practical substitute to test next time.
- `se-test/` holds the harness (`enhance.py`, `make_noisy.py`, `batch*.py`) and a
  ~2 GB venv. Safe to delete; regenerate from these notes if needed.
