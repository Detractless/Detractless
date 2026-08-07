# Local Python / ML Environment Inventory

Read-only discovery for the dictation-cleanup model bake-off. Nothing was installed, modified, or deleted.
Date: 2026-08-06 · Host: Windows 10 IoT Enterprise LTSC 2021

## (A) Python interpreters found

| Interpreter | Version | Path |
|---|---|---|
| System Python (py launcher default `*`) | 3.14 (64-bit) | `C:\Python314\python.exe` |
| Astral / CPython (py launcher tag) | 3.12.13 (64-bit) | managed by uv/Astral (not a plain path) |
| Miniconda `base` | see conda env | `C:\Users\Calibro1\miniconda3\python.exe` |

`where.exe python3` returned nothing; only `python` resolves (to `C:\Python314`). No standalone `C:\Python39/310/311/312`.

## (B) Conda environments

Conda is Miniconda at `C:\Users\Calibro1\miniconda3` (conda.exe under `Scripts`; not on PATH).

| Env | Path |
|---|---|
| `base` | `C:\Users\Calibro1\miniconda3` |
| `mlc-build` | `C:\Users\Calibro1\miniconda3\envs\mlc-build` |

No other conda-meta environments were found under the searched user roots.

## (C) Relevant project folders / venvs found

- `C:\Users\Calibro1\Documents\EmailSummarizer` — **the key find.** A full local-LLM eval project: prebuilt llama.cpp server (CPU + Vulkan), ~12 GGUF models, eval/benchmark harness, an embedded `mlc-llm` build tree, and `temp_repos` (cactus, GenieX, mlc-llm, needle, runanywhere-sdks).
- `C:\Users\Calibro1\Downloads\Enforcer\OS Projects\_Analysis` — matched name filter only; not inspected further (no venv markers nearby).
- `C:\Users\Calibro1\Downloads\IKS_backup_2026-07-29\App\Data\models\iks-canary-flash-q8.gguf` — a stray GGUF (~0.2 GB).
- `C:\Users\Calibro1\Desktop\Graphify\tests\test_ollama.py` — a test file referencing ollama; no ollama runtime binary found.

**No `pyvenv.cfg`, no `Scripts\python.exe` venvs, and no nested `conda-meta` folders** were found under Downloads / Documents / Desktop. Roots `source`, `repos`, `Projects`, `dev` do not exist. So there are no project-local virtualenvs — all Python capability lives in the two conda envs + `C:\Python314`.

## (D) ML packages by environment

Legend: ✓ present (version) · — absent. Checked: torch, transformers, safetensors, onnxruntime(-gpu), llama-cpp-python, mlx/mlx-lm, accelerate, sentencepiece, huggingface_hub, ctranslate2, optimum, numpy.

| Package | conda `base` | conda `mlc-build` | `C:\Python314` |
|---|---|---|---|
| torch | ✓ 2.12.1+cpu | ✓ 2.13.0 | ✓ 2.12.1+cpu |
| torchvision | ✓ 0.27.1+cpu | — | ✓ 0.27.1+cpu |
| transformers | ✓ 5.6.2 | ✓ 5.14.1 | ✓ 5.6.2 |
| safetensors | ✓ 0.8.0 | ✓ 0.8.0 | ✓ 0.8.0 |
| accelerate | ✓ 1.14.0 | — | ✓ 1.14.0 |
| huggingface_hub | ✓ 1.20.1 | ✓ 1.24.0 | ✓ 1.20.1 |
| sentencepiece | ✓ 0.2.2 | ✓ 0.2.2 | ✓ 0.2.2 |
| onnxruntime | ✓ 1.26.0 | — | ✓ 1.26.0 |
| onnxruntime-gpu | — | — | — |
| numpy | ✓ 2.4.6 | ✓ 2.4.6 | ✓ 2.4.6 |
| llama-cpp-python | — | — | — |
| ctranslate2 | — | — | — |
| optimum | — | — | — |
| mlx / mlx-lm | — | — | — (mlx is macOS-only) |

**GPU note:** All torch builds are CPU (`+cpu`) or CPU-default. No `+cu` CUDA torch and no `onnxruntime-gpu` anywhere. Inference via transformers/torch will run on CPU.

## (E) Existing LLM / GGUF runtimes & model files

**Prebuilt llama.cpp server (no build needed):** `C:\Users\Calibro1\Documents\EmailSummarizer\runtime\`
- `llama-bin\llama-server.exe` (+ `llama-server-impl.dll`) — CPU build
- `llama-bin-vulkan\llama-server.exe` (+ dll) — Vulkan (GPU-accelerated) build
- Version: **build 9728 (fabde3bf5)**, Clang 20.1.8, x86_64. Verified `--version` runs.
- Support files: `models.json`, `download.py`, `servers.ps1`, `start_server.ps1`, `t5_server.py`.

**GGUF models already on disk** (`...\EmailSummarizer\runtime\models\`):

| File | Size (GB) |
|---|---|
| gemma-4-E2B-it-Q4_K_M.gguf | 2.89 |
| LFM2.5-1.2B-Instruct-Q8_0.gguf | 1.16 |
| google_gemma-3-1b-it-Q8_0.gguf | 1.00 |
| google_gemma-3-1b-it-Q4_K_M.gguf | 0.75 |
| LFM2-1.2B-Extract-Q4_K_M.gguf | 0.68 |
| LFM2.5-1.2B-Instruct-Q4_K_M.gguf | 0.68 |
| LFM2.5-350M-F16.gguf | 0.66 |
| qwen2.5-0.5b-instruct-q8_0.gguf | 0.63 |
| LFM2.5-230M-F16.gguf | 0.43 |
| LFM2-350M-Extract-Q8_0.gguf | 0.35 |
| LFM2.5-350M-Q8_0.gguf | 0.35 |
| LFM2.5-230M-Q8_0.gguf | 0.23 |

Plus stray: `C:\Users\Calibro1\Downloads\IKS_backup_2026-07-29\App\Data\models\iks-canary-flash-q8.gguf` (~0.2 GB).

No `ollama`, `koboldcpp`, or `llama-cpp-python` install found (only a `test_ollama.py` script referencing it). An MLC-LLM source/build tree exists at `...\EmailSummarizer\mlc-llm` paired with the `mlc-build` conda env.

## (F) Free disk space

Drive C: — **Free: ~7.85 GB** (7,845,834,752 bytes); Used ~230 GB. This is tight — enough for a couple more ~350M-700M GGUFs but NOT for several 1 GB+ models plus a fresh CUDA torch (~2.5 GB) install.

## (G) Bottom line

**Yes — there is a reusable environment; you should not install a fresh stack.**

For **GGUF models** (the primary path for the bake-off):
- Reuse the prebuilt **llama.cpp server** at `C:\Users\Calibro1\Documents\EmailSummarizer\runtime\llama-bin\` (CPU) or `llama-bin-vulkan\` (GPU). It runs today, exposes an OpenAI-compatible HTTP API, and already sits next to a `start_server.ps1` / `servers.ps1` you can crib. Point it at any `.gguf` — including new dictation-cleanup models you drop into `runtime\models\`. No `llama-cpp-python` needed; the server binary is sufficient.
- Several small models (LFM2.5 230M/350M/1.2B, Gemma-3-1B, Qwen2.5-0.5B) are already downloaded and can be baked off immediately.

For **safetensors / transformers models**:
- Reuse conda **`base`** (`C:\Users\Calibro1\miniconda3\python.exe`) or `C:\Python314`. Both already have torch 2.12 (CPU), transformers 5.6.2, safetensors, accelerate, sentencepiece, huggingface_hub, onnxruntime, numpy — a complete CPU inference stack. `C:\Python314` and `base` are effectively identical in packages; conda `base` is the cleaner choice.

**What's missing / caveats:**
- **No GPU acceleration in Python:** torch is CPU-only; no CUDA torch, no onnxruntime-gpu. GPU inference is only available through the **Vulkan llama-server** binary. If you want GPU transformers inference you'd need a CUDA torch install (~2.5 GB) — not advisable given disk space.
- **No `llama-cpp-python`** (only the standalone server) — fine if you talk to the HTTP endpoint; needed only if you want in-process Python bindings.
- **No ctranslate2 / optimum / mlx** — none required for the plan above.
- **Disk is the real constraint (~7.85 GB free).** Prefer reusing already-downloaded GGUFs and small Q4/Q8 quants; avoid new 1 GB+ downloads and avoid a fresh CUDA torch install.

**Recommended reuse:** llama-server (Vulkan or CPU) from EmailSummarizer for GGUF bake-off; conda `base` for any safetensors/transformers runs. Nothing needs installing for the GGUF path.
