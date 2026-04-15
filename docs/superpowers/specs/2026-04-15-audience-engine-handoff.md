# Handoff: CW_Audience Engine — Social Growth NotebookLM Setup

**Date:** 2026-04-15
**Session goal:** Build the CW_Audience Engine NotebookLM notebook, upload AOP course materials, transcribe all audio/video files.

---

## What was completed

### Infrastructure created
- NotebookLM notebook: **CW_Audience Engine** (ID: `e246e525-8618-47ef-afd6-e279eed17d37`)
- Drive folder: `05_Learning/05_Social_Growth/` (ID: `1lNIFs_2POUdH6iY46T3LYNre8_OtR4wZ`)
  - `01_LinkedIn/` (ID: `1hiBeZ0qp2lEyJXphJBWdfcAvcBM5CGQ3`)
  - `02_X/` (ID: `1_RklVPanx0_QU8Iu07dMwv4cCrQB4ZkU`)
  - `03_Transcripts/` (ID: `1Wn8dW6pF8tKPBaj1THN3mcFXYPBCVRBA`)

### PDFs uploaded and added to NotebookLM (14 files)
All in Drive `02_X/` and added as sources to CW_Audience Engine:
- 101 Ways to Write a Tweet, 17 Secrets, Create 24/7 (x2), Create Grow Profit Twitterpreneur
- Road Maps 1-8 (Personal Branding, Email, Affiliate, Twitter Growth, Content, Peak Performance, Masterclass Tips, Spaces)
- Ultimate Beginner's Guide to X

### Transcribe skill built
- Script: `skills/transcribe/transcribe.py`
- Supports: local file, folder, YouTube URL
- Auto-splits files >25MB via ffmpeg, transcribes via OpenAI Whisper API
- Auto-titles hex-named files from transcript content
- Optional NotebookLM routing (off by default, pass `--notebook ID` to enable)
- Synced to `~/.claude/skills/transcribe/` and VPS

### Dependencies installed
- `yt-dlp` (pip) — YouTube audio download
- `ffmpeg` (winget, Gyan.FFmpeg) — audio splitting
- `OPENAI_API_KEY` added to `.env` and synced to VPS

### Transcription batch — IN PROGRESS
Source folder: `D:\2-Holding--transfer to Google Drive\1-BB Transfers`
33 AOP course files (all from AOP masterclass + CCP/CPG classes)

**Status at handoff:**
- ~28 of 33 transcripts saved to `tmp_upload/*.txt`
- Last batch still running (bg4tiaid0 / b0icezfaa) on final hex mp3 files
- Recurring Drive upload error: `[WinError 2] The system cannot find the file specified`

---

## What needs to be done next session

### 1. Fix Drive upload error (priority 1)
The `[WinError 2]` error in `upload_to_drive()` means `txt_path.relative_to(AGENTSHQ)` is failing for some files — likely because the txt is saved with a long auto-generated name that exceeds Windows path limits, or the relative path resolution breaks when the txt name contains characters gws doesn't like.

**Fix:** In `transcribe.py` `upload_to_drive()`, use absolute path directly instead of relative:
```python
# Replace this:
rel_path = txt_path.relative_to(AGENTSHQ)
--upload str(rel_path).replace("\\", "/")

# With: copy file to AGENTSHQ root first, upload from there, then delete
```
Or: truncate doc_name to 80 chars max to avoid path length issues.

### 2. Upload all completed transcripts to Drive
After fixing the upload bug, run upload-only pass on all `.txt` files in `tmp_upload/`:
```bash
OPENAI_API_KEY=... python skills/transcribe/transcribe.py "D:/2-Holding--transfer to Google Drive/1-BB Transfers" --notebook e246e525-8618-47ef-afd6-e279eed17d37
```
Script skips transcription if `.txt` exists, so it will only do the upload + NotebookLM steps.

### 3. Add transcripts to NotebookLM
Once uploaded to Drive, each file needs to be added as a source to `CW_Audience Engine`.
The script handles this automatically via `nlm source add` if the upload succeeds.

### 4. Verify final count in NotebookLM
```bash
PYTHONUTF8=1 nlm source list e246e525-8618-47ef-afd6-e279eed17d37 | python3 -c "import sys,json; s=json.load(sys.stdin); print(len(s), 'sources')"
```
Expected: 14 PDFs + 33 transcripts = 47 sources total.

### 5. Clean up tmp_upload/
After all uploads confirmed:
```bash
rm -rf D:/Ai_Sandbox/agentsHQ/tmp_upload/*.txt
rm -rf D:/Ai_Sandbox/agentsHQ/tmp_upload/chunks_*
rm D:/Ai_Sandbox/agentsHQ/tmp_upload/run_transcribe.py
rm D:/Ai_Sandbox/agentsHQ/tmp_upload/transcribe_batch.py
```

### 6. Rename hex-named transcripts in Drive
The hex files (9 of them: `6654c18f0d980`, `668c3d8d116fb`, etc.) were auto-titled from transcript content. Verify the auto-generated names make sense in Drive and rename any that are confusing.

### 7. Sync updated transcribe.py to VPS
After fixing the upload bug:
```bash
scp skills/transcribe/transcribe.py root@72.60.209.109:/root/agentsHQ/skills/transcribe/
cp skills/transcribe/transcribe.py ~/.claude/skills/transcribe/
```

---

## Key file locations
- Transcribe script: `d:\Ai_Sandbox\agentsHQ\skills\transcribe\transcribe.py`
- Transcripts in progress: `d:\Ai_Sandbox\agentsHQ\tmp_upload\*.txt`
- Source audio/video: `D:\2-Holding--transfer to Google Drive\1-BB Transfers\`
- OPENAI_API_KEY: in `d:\Ai_Sandbox\agentsHQ\.env` (line 153)
- nlm binary: `C:\Users\HUAWEI\AppData\Roaming\Python\Python313\Scripts\nlm.exe`
- ffmpeg binary: `C:\Users\HUAWEI\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe`

---

## Prompt for tomorrow

> Continue the CW_Audience Engine setup from the handoff at `docs/superpowers/specs/2026-04-15-audience-engine-handoff.md`.
>
> The transcription batch ran overnight. Start by:
> 1. Checking how many `.txt` files are in `tmp_upload/` and which ones are missing
> 2. Fixing the Drive upload `[WinError 2]` bug in `skills/transcribe/transcribe.py`
> 3. Running a clean upload+NotebookLM pass on all completed transcripts
> 4. Verifying the final source count in CW_Audience Engine (target: 47)
> 5. Cleaning up `tmp_upload/`
> 6. Syncing the fixed script to `~/.claude/skills/` and VPS
>
> Do NOT re-transcribe files that already have a `.txt` in `tmp_upload/` — the script handles this automatically via the skip logic.
