"""
transcribe.py — Audio/Video/YouTube transcription tool for agentsHQ

Usage:
  python transcribe.py <path-or-url> [options]

Arguments:
  path-or-url     Local file, folder of audio/video files, or YouTube URL

Options:
  --notebook ID   NotebookLM notebook ID to add transcript to (default: none)
  --drive-folder  Google Drive folder ID for upload (default: 03_Transcripts)
  --language xx   Force language code (e.g. fr, en, ar). Default: auto-detect
  --no-upload     Skip Drive upload (save locally only)
  --no-notebooklm Skip NotebookLM step even if --notebook is passed
  --date YYYY-MM-DD  Override date in filename (default: today)

Examples:
  python transcribe.py "D:/files/audio.m4a"
  python transcribe.py "D:/files/" --notebook e246e525-...
  python transcribe.py "https://www.youtube.com/watch?v=xxxxx" --notebook e246e525-...
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
import tempfile
import re
from pathlib import Path
from datetime import date

# ── Constants ────────────────────────────────────────────────────────────────

AGENTSHQ = Path(r"D:\Ai_Sandbox\agentsHQ")
WORK_DIR = AGENTSHQ / "tmp_upload"
FFMPEG = r"C:\Users\HUAWEI\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe"
NLM = r"C:\Users\HUAWEI\AppData\Roaming\Python\Python313\Scripts\nlm.exe"
DEFAULT_DRIVE_FOLDER = "1Wn8dW6pF8tKPBaj1THN3mcFXYPBCVRBA"  # 05_Social_Growth/03_Transcripts/  # pragma: allowlist secret
AUDIO_EXTS = {".m4a", ".mp3", ".wav", ".ogg", ".flac", ".aac"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
MAX_CHUNK_BYTES = 20 * 1024 * 1024  # 20MB — under Whisper's 25MB limit

# ── Setup ────────────────────────────────────────────────────────────────────

def get_openai_client():
    from openai import OpenAI
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        env_file = AGENTSHQ / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("OPENAI_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    if not key:
        raise RuntimeError("OPENAI_API_KEY not found. Set it in .env or environment.")
    return OpenAI(api_key=key)


# ── File resolution ──────────────────────────────────────────────────────────

def is_youtube_url(s):
    return "youtube.com" in s or "youtu.be" in s

def resolve_inputs(path_or_url):
    """Return list of (source_label, local_path) tuples."""
    if is_youtube_url(path_or_url):
        return [("youtube", path_or_url)]
    p = Path(path_or_url)
    if p.is_dir():
        files = [f for f in p.iterdir()
                 if f.suffix.lower() in AUDIO_EXTS | VIDEO_EXTS]
        if not files:
            print(f"No audio/video files found in {p}")
            sys.exit(1)
        return [("local", f) for f in sorted(files)]
    if p.is_file():
        return [("local", p)]
    raise FileNotFoundError(f"Not found: {path_or_url}")


# ── YouTube download ─────────────────────────────────────────────────────────

def download_youtube(url, out_dir):
    """Download YouTube audio to mp3. Returns Path to downloaded file."""
    out_template = str(out_dir / "yt_%(id)s.%(ext)s")
    cmd = ["yt-dlp", "-x", "--audio-format", "mp3",
           "--audio-quality", "64K",
           "-o", out_template, url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr[-400:]}")
    # Find the downloaded file
    files = list(out_dir.glob("yt_*.mp3"))
    if not files:
        raise RuntimeError("yt-dlp ran but no mp3 found")
    return files[0]


# ── Audio splitting ──────────────────────────────────────────────────────────

def split_audio(src, chunk_dir):
    """Split file into ~20MB mp3 chunks. Returns sorted list of chunk Paths."""
    chunk_dir.mkdir(parents=True, exist_ok=True)
    # Use Windows short path format to avoid spaces breaking ffmpeg segment muxer
    pattern = str(chunk_dir / "chunk_%03d.mp3")
    cmd = [FFMPEG, "-y", "-i", str(src),
           "-vn",
           "-acodec", "libmp3lame", "-ab", "64k",
           "-f", "segment", "-segment_time", "600",
           pattern]
    result = subprocess.run(cmd, capture_output=True, text=True,
                            env={**os.environ, "TEMP": str(chunk_dir)})
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr[-400:]}")
    chunks = sorted(chunk_dir.glob("chunk_*.mp3"))
    if not chunks:
        raise RuntimeError(f"ffmpeg ran but no chunks found in {chunk_dir}")
    return chunks


# ── Transcription ────────────────────────────────────────────────────────────

def transcribe_chunk(client, chunk_path, language=None):
    params = {"model": "whisper-1", "response_format": "text"}
    if language:
        params["language"] = language
    with open(chunk_path, "rb") as f:
        return client.audio.transcriptions.create(file=f, **params)

def transcribe_source(client, local_path, language=None):
    """Split and transcribe a local file. Returns full transcript string."""
    safe_stem = re.sub(r'[^a-zA-Z0-9]', '_', local_path.stem)[:20]
    chunk_dir = WORK_DIR / f"chunks_{safe_stem}"
    try:
        size = local_path.stat().st_size
        if size <= MAX_CHUNK_BYTES:
            print(f"  File under 20MB, transcribing directly...")
            return transcribe_chunk(client, local_path, language)

        print(f"  Splitting {size // (1024*1024)}MB file into chunks...")
        chunks = split_audio(local_path, chunk_dir)
        print(f"  {len(chunks)} chunks created")

        parts = []
        for i, chunk in enumerate(chunks, 1):
            print(f"  Chunk {i}/{len(chunks)} ({chunk.stat().st_size // 1024}KB)...", end=" ", flush=True)
            text = transcribe_chunk(client, chunk, language)
            words = len(text.split())
            print(f"{words} words")
            parts.append(text)
        return "\n\n".join(parts)
    finally:
        shutil.rmtree(chunk_dir, ignore_errors=True)


# ── Naming ───────────────────────────────────────────────────────────────────

def make_doc_name(original_name, today, prefix="x-twitter"):
    stem = Path(original_name).stem
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', stem).strip('-').lower()[:45].rstrip('-')
    return f"LEARNING_{prefix}_transcript_{today}_{slug}"

def infer_title_from_transcript(text, fallback):
    """Use first meaningful line of transcript as title for hex-named files."""
    for line in text.splitlines():
        line = line.strip()
        if len(line) > 20:
            slug = re.sub(r'[^a-zA-Z0-9]+', '-', line[:50]).strip('-').lower()
            return slug
    return fallback


# ── Drive upload ─────────────────────────────────────────────────────────────

def upload_to_drive(txt_path, doc_name, folder_id):
    """Upload txt as Google Doc. Returns Drive file ID."""
    rel_path = txt_path.relative_to(AGENTSHQ)
    cmd = [
        "gws", "drive", "files", "create",
        "--json", json.dumps({"name": doc_name, "parents": [folder_id], "mimeType": "application/vnd.google-apps.document"}),
        "--upload", str(rel_path).replace("\\", "/"),
        "--upload-content-type", "text/plain"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(AGENTSHQ))
    if result.returncode != 0:
        raise RuntimeError(f"gws upload failed: {result.stderr[-300:]}")
    data = json.loads(result.stdout)
    return data["id"]


# ── NotebookLM ───────────────────────────────────────────────────────────────

def add_to_notebooklm(notebook_id, drive_id):
    env = {**os.environ, "PYTHONUTF8": "1"}
    result = subprocess.run(
        [NLM, "source", "add", notebook_id, "--drive", drive_id],
        capture_output=True, text=True, env=env
    )
    if result.returncode != 0 and "charmap" not in result.stderr:
        raise RuntimeError(f"nlm failed: {result.stderr[-200:]}")


# ── Hex file detection ───────────────────────────────────────────────────────

def is_hex_named(filename):
    stem = Path(filename).stem.strip('_')
    return bool(re.match(r'^[0-9a-f]{8,}$', stem))


# ── Main processing ──────────────────────────────────────────────────────────

def process_one(source_type, source, client, args, today):
    """Process a single file or YouTube URL. Returns (doc_name, drive_id) or raises."""
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    tmp_audio = None

    # Resolve to local file
    if source_type == "youtube":
        print(f"\nDownloading YouTube audio: {source}")
        tmp_audio = download_youtube(source, WORK_DIR)
        local_path = tmp_audio
        original_name = source.split("v=")[-1][:20] + "_youtube"
    else:
        local_path = Path(source)
        original_name = local_path.name

    # Determine doc name
    prefix = "x-twitter"  # default; could be param later
    if is_hex_named(original_name):
        # Transcribe first, then use content for name
        print(f"\nTranscribing: {original_name} (hex-named, will auto-title)")
        transcript = transcribe_source(client, local_path, args.language)
        slug = infer_title_from_transcript(transcript, Path(original_name).stem[:30])
        doc_name = f"LEARNING_{prefix}_transcript_{today}_{slug}"
    else:
        doc_name = make_doc_name(original_name, today, prefix)
        txt_path = WORK_DIR / f"{doc_name}.txt"
        if txt_path.exists():
            print(f"\nSKIP (transcript exists): {original_name}")
            # Still upload if no drive ID yet
            transcript = txt_path.read_text(encoding="utf-8")
        else:
            print(f"\nTranscribing: {original_name} ({local_path.stat().st_size // (1024*1024)}MB)")
            transcript = transcribe_source(client, local_path, args.language)

    # Save transcript
    txt_path = WORK_DIR / f"{doc_name}.txt"
    txt_path.write_text(transcript, encoding="utf-8")
    word_count = len(transcript.split())
    print(f"  Transcript: {word_count} words -> {doc_name}.txt")

    drive_id = None
    if not args.no_upload:
        print(f"  Uploading to Drive...")
        drive_id = upload_to_drive(txt_path, doc_name, args.drive_folder)
        print(f"  Drive ID: {drive_id}")

        if args.notebook and not args.no_notebooklm:
            print(f"  Adding to NotebookLM...")
            add_to_notebooklm(args.notebook, drive_id)
            print(f"  Added to notebook.")

    # Cleanup tmp youtube audio
    if tmp_audio and tmp_audio.exists():
        tmp_audio.unlink()

    return doc_name, drive_id


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio/video/YouTube to Google Drive")
    parser.add_argument("source", help="File path, folder path, or YouTube URL")
    parser.add_argument("--notebook", default=None, help="NotebookLM notebook ID")
    parser.add_argument("--drive-folder", default=DEFAULT_DRIVE_FOLDER, help="Drive folder ID")
    parser.add_argument("--language", default=None, help="Force language (e.g. en, fr, ar)")
    parser.add_argument("--no-upload", action="store_true", help="Skip Drive upload")
    parser.add_argument("--no-notebooklm", action="store_true", help="Skip NotebookLM")
    parser.add_argument("--date", default=str(date.today()), help="Date for filename")
    args = parser.parse_args()

    client = get_openai_client()
    inputs = resolve_inputs(args.source)
    today = args.date

    print(f"Found {len(inputs)} file(s) to process")
    results, errors = [], []

    for source_type, source in inputs:
        try:
            doc_name, drive_id = process_one(source_type, source, client, args, today)
            results.append((str(source), doc_name, drive_id))
        except Exception as e:
            print(f"  ERROR: {e}")
            errors.append((str(source), str(e)))

    print(f"\n{'='*60}")
    print(f"DONE: {len(results)} transcribed, {len(errors)} errors")
    if errors:
        print("\nErrors:")
        for f, e in errors:
            print(f"  {Path(f).name}: {e}")

    # Clean up empty tmp dir
    try:
        if WORK_DIR.exists() and not any(WORK_DIR.iterdir()):
            WORK_DIR.rmdir()
    except Exception:
        pass


if __name__ == "__main__":
    main()
