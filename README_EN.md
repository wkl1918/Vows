# Vows (VoxFlow Open-Source Package)

✨🎬🌍🚀 A reproducible AI video dubbing pipeline.

Languages: [简体中文](README.md) · [English](README_EN.md) · [日本語](README_JA.md)

## 🎯 Project Overview

Vows is an engineering pipeline for multilingual AI dubbing and translation. The goal is to transform an input source video into a publishable output video in a selected target language (50 supported languages).

It is not a single model demo script. It is a complete, reproducible, fallback-capable, and extensible system.

Core capabilities:

1. Automatic audio extraction and vocal separation (reduce background interference)
2. ASR + speaker diarization (organize text by timeline and speakers)
3. LLM translation by segments (fallback to source text on failure)
4. IndexTTS voice cloning (automatic EdgeTTS fallback on failure)
5. Timeline-aligned mixing and export (optional hard subtitle burn-in)
6. Script mode, API mode, and one-click drag-and-drop bat mode

One-line summary:

Audio Extraction -> Vocal Separation -> ASR + Speaker Diarization -> LLM Translation -> TTS Cloning/Fallback -> Mix & Export

---

## 🆚 Result Comparison

### Case 1: TED (with hard subtitles)
- Source video:

https://github.com/user-attachments/assets/6d045aa6-6eec-4c29-8a7f-918809bea939

- Output video:

https://github.com/user-attachments/assets/ead60688-c0de-4ee9-983d-e3d9af182b16


Comparison highlights:
1. Keeps original pacing and timeline, with segment-aligned dubbing
2. Produces target-language dubbing with visible subtitles
3. Voice style stays close to reference speaker, with automatic fallback for failed segments

### Case 2: Trump (without subtitles)
- Source video:

https://github.com/user-attachments/assets/b396c851-d8c8-44a2-ba6f-4cba41926812

- Output video:

https://github.com/user-attachments/assets/7b0c1728-c79d-4841-9d07-616031f63096

Comparison highlights:
1. Outputs dubbed video without subtitle burn-in
2. Keeps natural relation between background and voice in final mix
3. If any translation/cloning step fails, fallback keeps the whole task finishable

---

## 📚 Documentation

1. File map: `docs/FILES_ZH.md`
2. Compliance: `docs/COMPLIANCE_ZH.md`

---

## 🧰 1. Requirements (Windows)

1. OS: Windows 10/11
2. Python: 3.10 or 3.11
3. Conda: recommended (Anaconda/Miniconda)
4. CUDA: optional (recommended if NVIDIA GPU available)
5. FFmpeg: available via system PATH or `tools/ffmpeg`
6. Node.js: required only for frontend (Node 18+ recommended)

---

## 📥 2. Clone Repository

```powershell
git clone https://github.com/wkl1918/Vows
cd Vows
```

---

## 🐍 3. Create Python Env and Install Backend Dependencies

```powershell
conda create -n VoxFlow python=3.10 -y
conda activate VoxFlow
pip install -r backend/requirements.txt
```

---

## 🧠 4. Prepare IndexTTS2 (separate repo)

This repository does not redistribute IndexTTS weights and cache. Prepare them from upstream:

1. Official upstream: `https://github.com/index-tts/index-tts`
2. Clone to a local path, e.g. `D:\AI\index-tts-main`

3. Download `checkpoints` and dependencies

### Option A (recommended): HuggingFace CLI

In the VoxFlow environment:

```powershell
conda activate VoxFlow
pip install -U "huggingface_hub[cli]"
```

Prepare local directory:

```powershell
mkdir D:\AI -Force
cd D:\AI
git clone https://github.com/index-tts/index-tts.git index-tts-main
cd index-tts-main
```

Download model to `checkpoints`:

```powershell
hf download IndexTeam/IndexTTS-2 --local-dir checkpoints
```

If network is slow in mainland China, use mirror:

```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
hf download IndexTeam/IndexTTS-2 --local-dir checkpoints
```

Quick validation:

```powershell
Test-Path D:\AI\index-tts-main\checkpoints\config.yaml
Test-Path D:\AI\index-tts-main\checkpoints\gpt.pth
Test-Path D:\AI\index-tts-main\checkpoints\s2mel.pth
```

All should return `True`.

4. Configure `INDEXTTS_DIR` in `.env`

Edit `D:\Vows\backend\.env` and set:

```env
INDEXTTS_DIR=D:/AI/index-tts-main
```

Notes:
1. Use your actual path.
2. `/` path style is recommended and works on Windows.
3. Do not point to `checkpoints`; point to the `index-tts-main` root.

5. Quick check before starting backend:

```powershell
python -c "import os; p=os.getenv('INDEXTTS_DIR'); print('INDEXTTS_DIR=',p)"
```

If configured correctly, cloning stage should no longer report `IndexTTS config not found`.

---

## ⚙️ 5. Configure Environment Variables

Copy template first:

```powershell
Copy-Item backend/.env.example backend/.env
```

Then edit `backend/.env` with at least:

```env
HF_TOKEN=hf_xxx
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
INDEXTTS_DIR=D:/AI/index-tts-main
```

Notes:
1. `HF_TOKEN`: for pyannote/huggingface access.
2. `LLM_API_KEY`: for translation provider (Qwen/DeepSeek/OpenAI-compatible).
3. `INDEXTTS_DIR`: local IndexTTS code directory.
4. If not configured, system skips cloning and falls back to EdgeTTS.

Proxy example if needed:

```env
HTTP_PROXY=http://127.0.0.1:7897
HTTPS_PROXY=http://127.0.0.1:7897
```

---

## 🚀 6. Start Backend

```powershell
conda activate VoxFlow
cd backend
python app.py
```

Success indicator:

`Uvicorn running on http://127.0.0.1:8000`

---

## 💻 7. Start Frontend (optional)

```powershell
cd frontend
npm install
npm run dev
```

---

## 🧭 8. How to Run

You can switch target language in 3 ways:

### 8.1 Frontend mode (simplest)
1. Start backend: `python backend/app.py`
2. Start frontend: `cd frontend && npm install && npm run dev`
3. Select target language (50 options) and upload file

### 8.2 Drag-and-drop bat mode
1. Drag video onto:
- `一键处理视频.bat` (no hard subtitles)
- `一键处理视频并加硬字幕.bat` (with hard subtitles)
2. If 2nd argument is not passed, script prompts language code list
3. You can also pass language in CLI:

```powershell
一键处理视频.bat "D:\demo.mp4" en
一键处理视频并加硬字幕.bat "D:\demo.mp4" ja
```

### 8.3 Python script mode (most controllable)

```powershell
python run_task.py "D:/path/to/input.mp4" zh
python run_task_with_subtitles.py "D:/path/to/input.mp4" ja
```

2nd parameter is target language code. Default is `zh`.

---

Supported language codes (50):
- `zh` Chinese
- `en` English
- `ja` Japanese
- `ko` Korean
- `es` Spanish
- `fr` French
- `de` German
- `ru` Russian
- `it` Italian
- `pt` Portuguese
- `ar` Arabic
- `hi` Hindi
- `th` Thai
- `vi` Vietnamese
- `tr` Turkish
- `nl` Dutch
- `pl` Polish
- `id` Indonesian
- `ms` Malay
- `fa` Persian
- `uk` Ukrainian
- `cs` Czech
- `sk` Slovak
- `hu` Hungarian
- `ro` Romanian
- `bg` Bulgarian
- `hr` Croatian
- `sl` Slovenian
- `sr` Serbian
- `da` Danish
- `sv` Swedish
- `no` Norwegian
- `fi` Finnish
- `et` Estonian
- `lv` Latvian
- `lt` Lithuanian
- `el` Greek
- `he` Hebrew
- `bn` Bengali
- `ta` Tamil
- `te` Telugu
- `mr` Marathi
- `gu` Gujarati
- `kn` Kannada
- `ml` Malayalam
- `ur` Urdu
- `sw` Swahili
- `af` Afrikaans
- `fil` Filipino
- `ca` Catalan

Important note: if translation API fails, system falls back to source text, so output language may appear unchanged. Check `LLM_API_KEY` and network/proxy settings.

---

## 🔁 9. Pipeline and Fallback Strategy

1. Audio extraction from source video
2. Vocal separation with Demucs
3. Speech recognition via Whisper
4. Speaker diarization via Pyannote
5. Segment translation via LLM
6. Batch synthesis via IndexTTS
7. Automatic fallback to EdgeTTS on cloning failure
8. Timeline mixing and final export

---

## 📦 10. Output Location

Default output directory:

`backend/storage/outputs/<task_id>/`

Common outputs:
1. `final_<source_video_name>.mp4`
2. `final_<source_video_name>.srt`
3. `final_<source_video_name>_subtitled.mp4`

---

## 🛠️ 11. Troubleshooting (from real logs)

### 11.1 ASR download failure (ProxyError / 127.0.0.1:7897)

Symptom:
`Failed to establish a new connection: [WinError 10061]`

Cause:
Proxy variables are enabled but local proxy is not running.

Fix:
1. Start proxy client and verify port.
2. Or remove/comment `HTTP_PROXY` and `HTTPS_PROXY`.
3. Restart backend.

### 11.2 LLM translation failure (SSL EOF)

Symptom:
`SSLEOFError: EOF occurred in violation of protocol`

Cause:
Network/TLS/proxy interruption.

Fix:
1. Check proxy and network.
2. Retry with another network.
3. System fallback to source text is expected behavior.

### 11.3 Why output is still English instead of Chinese?

Root cause:
Translation stage failed and fell back to source text.

Check order:
1. Confirm `LLM Translation failed` in logs
2. Verify `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`
3. Verify internet/proxy availability

### 11.4 Cloning stage stalls or no wav output

Check:
1. `.env` has correct `INDEXTTS_DIR`
2. `INDEXTTS_DIR/checkpoints/config.yaml` exists
3. Backend env has dependencies (librosa/soundfile/torch)
4. Check IndexTTS subprocess errors in backend logs

### 11.5 Backend window only shows `Active code page: 65001`

Common causes:
Wrong working directory or env not activated.

Fix:
1. Use provided one-click scripts; avoid old complex `start` command chaining.
2. Ensure project structure includes `_start_backend.bat`.

---

## ⚡ 12. Performance and Quality Tips

1. Prefer CUDA for better speed
2. Reference audio: single speaker, clean, little/no background, 5-15s
3. Segment long text for better stability
4. Keep batch cloning to avoid repeated model loading
5. If VRAM is limited, lower concurrency or validate with CPU path first

---

## 🔒 13. Security and Compliance (Important)

1. Never upload real secrets (`.env`, tokens, API keys)
2. Do not upload private or unauthorized user media
3. This repo does not redistribute upstream model weights; users must download and comply with upstream license
4. Follow IndexTTS2 official license and disclaimer
5. Ensure legal authorization for any voice cloning target

---

## 🙏 14. Acknowledgements and Upstream References

1. IndexTTS / IndexTTS2 official repositories and papers
2. Demucs / Whisper / Pyannote / EdgeTTS and other open-source components
3. See `THIRD_PARTY_NOTICES.md`

---

## ⚠️ Disclaimer

This project is for legal and compliant research/engineering use only. Users are solely responsible for media authorization, model licensing, data compliance, and generated content compliance.
