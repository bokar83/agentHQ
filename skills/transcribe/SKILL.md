---
name: transcribe
description: Transcribes audio files, video files, folders, and YouTube URLs using the OpenAI Whisper API with optional Google Drive and NotebookLM routing. Triggers on "transcribe", "get transcript", "speech to text", "transcribe this audio", "transcribe this video".
---

# Transcribe Skill

Transcribe audio files, video files, or YouTube URLs using OpenAI Whisper API.
Saves transcripts as Google Docs in Drive. NotebookLM routing is optional and must be explicitly requested.

## Trigger

Use when the user says any of:
- `/transcribe`
- "transcribe this file / these files / this folder"
- "transcribe this YouTube video"
- "get transcript for"
- "transcribe the audio/video files"

## Capabilities

- Local audio: .m4a, .mp3, .wav, .ogg, .flac, .aac
- Local video: .mp4, .mov, .avi, .mkv, .webm (audio extracted automatically)
- Folder: transcribes all audio/video files found in the folder
- YouTube URLs: audio downloaded via yt-dlp, then transcribed
- Multilingual: auto-detects language (99 languages — works for EN, FR, AR, etc.)
- Hex-named files: auto-titles the transcript from first meaningful sentence
- Files over 25MB: split into 10-min chunks via ffmpeg, then concatenated

## Primary Job

Produce a high-quality transcript and save it to Google Drive as a Google Doc.
Where it goes after that (NotebookLM, Notion, email) is a separate decision per batch.

## NotebookLM Routing — Optional

OFF by default. Only add to a notebook when the user explicitly says to.
Pass `--notebook <ID>` to enable.

Default notebook when routing is requested: `CW_Audience Engine`
Notebook ID: `e246e525-8618-47ef-afd6-e279eed17d37`

## Default Drive Destination

`05_Learning/05_Social_Growth/03_Transcripts/`
Folder ID: `1Wn8dW6pF8tKPBaj1THN3mcFXYPBCVRBA`

Override with `--drive-folder <ID>` for other destinations.

## File Naming Convention

`LEARNING_[topic]_transcript_[YYYY-MM-DD]_[short-descriptor]`

Examples:
- `LEARNING_x-twitter_transcript_2026-04-14_101tips`
- `LEARNING_x-twitter_transcript_2026-04-14_real-algo-hacks`

Hex-named files (e.g. `6654c18f0d980.mp3`) are auto-titled from transcript content.

## How to Run

Script lives at: `D:\Ai_Sandbox\agentsHQ\skills\transcribe\transcribe.py`

### Single file
```
python skills/transcribe/transcribe.py "D:\path\to\audio.m4a"
```

### Folder (batch — all audio/video files)
```
python skills/transcribe/transcribe.py "D:\path\to\folder"
```

### With NotebookLM routing
```
python skills/transcribe/transcribe.py "D:\path\to\folder" --notebook e246e525-8618-47ef-afd6-e279eed17d37
```

### YouTube URL
```
python skills/transcribe/transcribe.py "https://www.youtube.com/watch?v=xxxxx" --notebook e246e525-8618-47ef-afd6-e279eed17d37
```

### Force language
```
python skills/transcribe/transcribe.py "D:\path\to\audio.mp3" --language fr
```

### Local only (no Drive upload)
```
python skills/transcribe/transcribe.py "D:\path\to\audio.m4a" --no-upload
```

## Options Reference

| Option | Default | Description |
|--------|---------|-------------|
| `--notebook ID` | none | NotebookLM notebook ID to add transcript to |
| `--drive-folder ID` | 03_Transcripts | Drive folder ID for upload |
| `--language xx` | auto | Force language code (en, fr, ar, es...) |
| `--no-upload` | off | Save locally only, skip Drive |
| `--no-notebooklm` | off | Skip NotebookLM even if --notebook passed |
| `--date YYYY-MM-DD` | today | Override date in output filename |

## Dependencies

All installed on local machine:
- `openai` (pip) — Whisper API
- `yt-dlp` (pip) — YouTube download
- `ffmpeg` — file splitting (at WinGet path)
- `gws` — Google Drive upload
- `nlm` — NotebookLM (at Python Scripts path)

OPENAI_API_KEY must be in `D:\Ai_Sandbox\agentsHQ\.env` or environment.

## Key Paths

- ffmpeg: `C:\Users\HUAWEI\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe`
- nlm: `C:\Users\HUAWEI\AppData\Roaming\Python\Python313\Scripts\nlm.exe`
- Work dir: `D:\Ai_Sandbox\agentsHQ\tmp_upload\` (auto-created, auto-cleaned)

## Notes

- nlm outputs a Unicode checkmark that errors on Windows cp1252 terminals — cosmetic only, operation succeeds
- gws requires upload files to be inside the agentsHQ working directory — script handles this automatically
- Transcript .txt files are saved to tmp_upload/ during processing, then cleaned up after Drive upload confirms
- Re-running on the same file skips transcription if .txt already exists in tmp_upload/
