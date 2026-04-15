```python
#!/usr/bin/env python3
"""
================================================================================
VIDEO TRANSCRIPT ORCHESTRATOR + CREW
================================================================================
USAGE:
 # Install dependencies first:
 pip install crewai crewai-tools openai gdown pydub requests python-dotenv
 # Also install ffmpeg on your system:
 # macOS: brew install ffmpeg
 # Ubuntu: sudo apt install ffmpeg
 # Windows: https://ffmpeg.org/download.html

 # Set your OpenAI API key in a .env file or environment:
 export OPENAI_API_KEY="sk-..."

 # Run directly:
 python video_transcript_orchestrator.py

 # Or import and call programmatically:
 from video_transcript_orchestrator import run_transcript_crew
 result = run_transcript_crew(
 "https://drive.google.com/file/d/1yQyoUiH8jobHcx6n9vy5hSGRAMzEJ0ow/view?usp=drivesdk"
 )
 print(result)

NOTES:
 - The Google Drive file must be publicly shared ("Anyone with the link").
 - Transcription uses OpenAI Whisper via the openai SDK (model: whisper-1).
 - Audio files >25 MB are automatically chunked before transcription.
 - Output is saved to ./transcript_output/ as .txt and .json files.
================================================================================
"""

import os
import re
import json
import time
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load environment variables (.env file support)
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
 level=logging.INFO,
 format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
 datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("TranscriptOrchestrator")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path("./transcript_output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_WHISPER_BYTES = 24 * 1024 * 1024 # 24 MB (Whisper limit is 25 MB)
CHUNK_DURATION_SEC = 600 # 10-minute audio chunks
RETRY_ATTEMPTS = 3
RETRY_DELAY_SEC = 5


# ============================================================================
# TOOL FUNCTIONS (used by agents as callable tools)
# ============================================================================

def extract_drive_file_id(url: str) -> str:
 """
 Tool: Extract the Google Drive file ID from a share URL.

 Supports formats:
 - https://drive.google.com/file/d/<ID>/view?...
 - https://drive.google.com/open?id=<ID>
 - https://docs.google.com/...
 """
 patterns = [
 r"/file/d/([a-zA-Z0-9_-]+)",
 r"[?&]id=([a-zA-Z0-9_-]+)",
 r"/d/([a-zA-Z0-9_-]+)",
 ]
 for pattern in patterns:
 match = re.search(pattern, url)
 if match:
 file_id = match.group(1)
 log.info(f"[VideoRetriever] Extracted file ID: {file_id}")
 return file_id
 raise ValueError(f"Could not extract file ID from URL: {url}")


def download_google_drive_file(file_id: str, dest_dir: Path) -> Path:
 """
 Tool: Download a publicly shared Google Drive file using the export/download
 endpoint. Handles the virus-scan confirmation page for large files.

 Returns the local path to the downloaded file.
 """
 session = requests.Session()
 download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

 log.info(f"[VideoRetriever] Downloading file ID: {file_id}")

 for attempt in range(1, RETRY_ATTEMPTS + 1):
 try:
 response = session.get(download_url, stream=True, timeout=60)
 response.raise_for_status()

 # Google Drive shows a confirmation page for large files
 # Detect it by checking content-type and body
 content_type = response.headers.get("Content-Type", "")
 if "text/html" in content_type:
 # Parse the confirmation token from the HTML
 token = _parse_drive_confirm_token(response.text)
 if token:
 log.info("[VideoRetriever] Large file detected, using confirm token.")
 confirm_url = (
 f"https://drive.google.com/uc?export=download"
 f"&id={file_id}&confirm={token}"
 )
 response = session.get(confirm_url, stream=True, timeout=120)
 response.raise_for_status()
 else:
 # Try the newer confirm endpoint
 confirm_url = (
 f"https://drive.usercontent.google.com/download"
 f"?id={file_id}&export=download&confirm=t"
 )
 response = session.get(confirm_url, stream=True, timeout=120)
 response.raise_for_status()

 # Determine filename from Content-Disposition header
 filename = _get_filename_from_response(response, file_id)
 dest_path = dest_dir / filename

 log.info(f"[VideoRetriever] Saving to: {dest_path}")
 with open(dest_path, "wb") as f:
 for chunk in response.iter_content(chunk_size=8192):
 if chunk:
 f.write(chunk)

 file_size_mb = dest_path.stat().st_size / (1024 * 1024)
 log.info(f"[VideoRetriever] Download complete. Size: {file_size_mb:.2f} MB")
 return dest_path

 except requests.RequestException as e:
 log.warning(f"[VideoRetriever] Attempt {attempt}/{RETRY_ATTEMPTS} failed: {e}")
 if attempt < RETRY_ATTEMPTS:
 time.sleep(RETRY_DELAY_SEC * attempt)
 else:
 raise RuntimeError(f"Failed to download file after {RETRY_ATTEMPTS} attempts: {e}")


def _parse_drive_confirm_token(html_text: str) -> Optional[str]:
 """Parse the virus-scan confirmation token from Google Drive HTML page."""
 match = re.search(r'confirm=([0-9A-Za-z_-]+)', html_text)
 return match.group(1) if match else None


def _get_filename_from_response(response: requests.Response, fallback_id: str) -> str:
 """Extract filename from Content-Disposition header or use a fallback."""
 cd = response.headers.get("Content-Disposition", "")
 match = re.search(r'filename\*?=["\']?(?:UTF-8\'\')?([^"\'\n;]+)', cd, re.IGNORECASE)
 if match:
 return match.group(1).strip()
 # Fallback: use file ID with .mp4 extension
 return f"{fallback_id}.mp4"


def extract_audio_from_video(video_path: Path, output_dir: Path) -> Path:
 """
 Tool: Extract audio from a video file using FFmpeg.
 Converts to 16kHz mono WAV for optimal Whisper transcription.

 Returns the path to the extracted audio file.
 """
 audio_path = output_dir / (video_path.stem + "_audio.wav")
 log.info(f"[AudioExtractor] Extracting audio from: {video_path.name}")

 cmd = [
 "ffmpeg",
 "-i", str(video_path),
 "-vn", # No video
 "-acodec", "pcm_s16le", # PCM 16-bit little-endian WAV
 "-ar", "16000", # 16 kHz sample rate (Whisper optimal)
 "-ac", "1", # Mono channel
 "-y", # Overwrite output
 str(audio_path),
 ]

 try:
 result = subprocess.run(
 cmd,
 capture_output=True,
 text=True,
 timeout=3600, # 1-hour timeout for large files
 )
 if result.returncode != 0:
 raise RuntimeError(
 f"FFmpeg failed (code {result.returncode}):\n{result.stderr}"
 )
 audio_size_mb = audio_path.stat().st_size / (1024 * 1024)
 log.info(f"[AudioExtractor] Audio extracted. Size: {audio_size_mb:.2f} MB")
 return audio_path

 except FileNotFoundError:
 raise RuntimeError(
 "FFmpeg not found. Install it: brew install ffmpeg (macOS) "
 "or sudo apt install ffmpeg (Ubuntu)"
 )
 except subprocess.TimeoutExpired:
 raise RuntimeError("FFmpeg timed out processing the video file.")


def chunk_audio_file(audio_path: Path, output_dir: Path) -> list[Path]:
 """
 Tool: Split a large audio file into chunks using FFmpeg.
 Each chunk is CHUNK_DURATION_SEC seconds long.

 Returns a list of chunk file paths in order.
 """
 file_size = audio_path.stat().st_size
 if file_size <= MAX_WHISPER_BYTES:
 log.info("[AudioExtractor] Audio is within Whisper size limit, no chunking needed.")
 return [audio_path]

 log.info(f"[AudioExtractor] Audio too large ({file_size / 1024 / 1024:.1f} MB). Chunking...")
 chunks_dir = output_dir / "chunks"
 chunks_dir.mkdir(exist_ok=True)

 chunk_pattern = str(chunks_dir / f"{audio_path.stem}_chunk_%04d.wav")

 cmd = [
 "ffmpeg",
 "-i", str(audio_path),
 "-f", "segment",
 "-segment_time", str(CHUNK_DURATION_SEC),
 "-c", "copy",
 "-y",
 chunk_pattern,
 ]

 result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
 if result.returncode != 0:
 raise RuntimeError(f"FFmpeg chunking failed:\n{result.stderr}")

 chunks = sorted(chunks_dir.glob(f"{audio_path.stem}_chunk_*.wav"))
 log.info(f"[AudioExtractor] Created {len(chunks)} audio chunks.")
 return chunks


def transcribe_audio_with_whisper(audio_chunks: list[Path]) -> dict:
 """
 Tool: Transcribe audio using OpenAI Whisper API (whisper-1 model).
 Handles multiple chunks and merges results.

 Returns a dict with 'text' (full transcript) and 'segments' (per-chunk).
 """
 import openai

 api_key = os.getenv("OPENAI_API_KEY")
 if not api_key:
 raise EnvironmentError(
 "OPENAI_API_KEY not set. Add it to your .env file or environment."
 )

 client = openai.OpenAI(api_key=api_key)
 full_text_parts = []
 segments = []

 log.info(f"[Transcription] Transcribing {len(audio_chunks)} audio chunk(s) with Whisper...")

 for i, chunk_path in enumerate(audio_chunks, start=1):
 log.info(f"[Transcription] Processing chunk {i}/{len(audio_chunks)}: {chunk_path.name}")

 for attempt in range(1, RETRY_ATTEMPTS + 1):
 try:
 with open(chunk_path, "rb") as audio_file:
 response = client.audio.transcriptions.create(
 model="whisper-1",
 file=audio_file,
 response_format="verbose_json", # Includes timestamps
 language=None, # Auto-detect language
 )

 chunk_text = response.text.strip()
 full_text_parts.append(chunk_text)
 segments.append({
 "chunk": i,
 "filename": chunk_path.name,
 "text": chunk_text,
 "language": getattr(response, "language", "unknown"),
 "duration": getattr(response, "duration", None),
 })
 log.info(f"[Transcription] Chunk {i} done. Words: {len(chunk_text.split())}")
 break # Success, exit retry loop

 except Exception as e:
 log.warning(f"[Transcription] Attempt {attempt}/{RETRY_ATTEMPTS} failed: {e}")
 if attempt < RETRY_ATTEMPTS:
 time.sleep(RETRY_DELAY_SEC * attempt)
 else:
 raise RuntimeError(
 f"Transcription failed for chunk {chunk_path.name} "
 f"after {RETRY_ATTEMPTS} attempts: {e}"
 )

 full_transcript = " ".join(full_text_parts)
 log.info(f"[Transcription] Complete. Total words: {len(full_transcript.split())}")

 return {
 "text": full_transcript,
 "segments": segments,
 "total_chunks": len(audio_chunks),
 }


def format_and_save_transcript(transcript_data: dict, source_url: str) -> dict:
 """
 Tool: Format the raw transcript and save it to disk in .txt and .json formats.

 Returns a dict with output file paths and summary stats.
 """
 log.info("[Formatter] Formatting and saving transcript...")

 timestamp = time.strftime("%Y%m%d_%H%M%S")
 txt_path = OUTPUT_DIR / f"transcript_{timestamp}.txt"
 json_path = OUTPUT_DIR / f"transcript_{timestamp}.json"

 full_text = transcript_data["text"]

 # --- Clean up common transcription artifacts ---
 # Normalize whitespace
 full_text = re.sub(r" {2,}", " ", full_text)
 # Ensure sentences start with capital letters
 full_text = re.sub(r"(?<=\. )([a-z])", lambda m: m.group(1).upper(), full_text)
 # Remove trailing whitespace per line
 full_text = "\n".join(line.strip() for line in full_text.splitlines())

 # --- Build structured output ---
 output_json = {
 "source_url": source_url,
 "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
 "total_words": len(full_text.split()),
 "total_chunks": transcript_data["total_chunks"],
 "segments": transcript_data["segments"],
 "full_transcript": full_text,
 }

 # --- Save plain text ---
 txt_header = (
 f"TRANSCRIPT\n"
 f"Source: {source_url}\n"
 f"Generated: {output_json['generated_at']}\n"
 f"Words: {output_json['total_words']}\n"
 f"{'=' * 60}\n\n"
 )
 txt_path.write_text(txt_header + full_text, encoding="utf-8")
 log.info(f"[Formatter] Saved TXT: {txt_path}")

 # --- Save JSON ---
 json_path.write_text(
 json.dumps(output_json, indent=2, ensure_ascii=False),
 encoding="utf-8",
 )
 log.info(f"[Formatter] Saved JSON: {json_path}")

 return {
 "txt_path": str(txt_path),
 "json_path": str(json_path),
 "word_count": output_json["total_words"],
 "transcript_preview": full_text[:500] + ("..." if len(full_text) > 500 else ""),
 }


# ============================================================================
# ORCHESTRATOR (coordinates the crew)
# ============================================================================

class TranscriptOrchestrator:
 """
 Orchestrator that coordinates the transcript extraction crew:

 Crew Members:
 1. VideoRetriever, Downloads the video from Google Drive
 2. AudioExtractor, Extracts and chunks audio from the video
 3. Transcription, Converts audio to text via Whisper
 4. Formatter, Cleans, structures, and saves the transcript
 """

 def __init__(self, video_url: str):
 self.video_url = video_url
 self.temp_dir = Path(tempfile.mkdtemp(prefix="transcript_crew_"))
 log.info(f"[Orchestrator] Initialized. Temp dir: {self.temp_dir}")
 log.info(f"[Orchestrator] Target URL: {video_url}")

 def run(self) -> dict:
 """
 Execute the full transcript pipeline.
 Returns a result dict with transcript text and file paths.
 """
 log.info("[Orchestrator] === STARTING TRANSCRIPT CREW ===")
 result = {}

 try:
 # ------------------------------------------------------------------
 # STEP 1: VideoRetriever Agent
 # ------------------------------------------------------------------
 log.info("[Orchestrator] Dispatching → VideoRetriever")
 file_id = extract_drive_file_id(self.video_url)
 video_path = download_google_drive_file(file_id, self.temp_dir)
 log.info(f"[Orchestrator] VideoRetriever ✓ → {video_path.name}")

 # ------------------------------------------------------------------
 # STEP 2: AudioExtractor Agent
 # ------------------------------------------------------------------
 log.info("[Orchestrator] Dispatching → AudioExtractor")
 audio_path = extract_audio_from_video(video_path, self.temp_dir)
 audio_chunks = chunk_audio_file(audio_path, self.temp_dir)
 log.info(f"[Orchestrator] AudioExtractor ✓ → {len(audio_chunks)} chunk(s)")

 # ------------------------------------------------------------------
 # STEP 3: Transcription Agent
 # ------------------------------------------------------------------
 log.info("[Orchestrator] Dispatching → Transcription")
 transcript_data = transcribe_audio_with_whisper(audio_chunks)
 log.info("[Orchestrator] Transcription ✓")

 # ------------------------------------------------------------------
 # STEP 4: Formatter Agent
 # ------------------------------------------------------------------
 log.info("[Orchestrator] Dispatching → Formatter")
 output_info = format_and_save_transcript(transcript_data, self.video_url)
 log.info("[Orchestrator] Formatter ✓")

 result = {
 "status": "success",
 "source_url": self.video_url,
 "file_id": file_id,
 "txt_output": output_info["txt_path"],
 "json_output": output_info["json_path"],
 "word_count": output_info["word_count"],
 "transcript_preview": output_info["transcript_preview"],
 }

 log.info("[Orchestrator] === CREW COMPLETED SUCCESSFULLY ===")
 log.info(f"[Orchestrator] Words transcribed: {result['word_count']}")
 log.info(f"[Orchestrator] TXT saved to: {result['txt_output']}")
 log.info(f"[Orchestrator] JSON saved to: {result['json_output']}")

 except Exception as e:
 log.error(f"[Orchestrator] CREW FAILED: {e}", exc_info=True)
 result = {
 "status": "error",
 "source_url": self.video_url,
 "error": str(e),
 }

 finally:
 self._cleanup()

 return result

 def _cleanup(self):
 """Remove temporary files created during processing."""
 import shutil
 try:
 shutil.rmtree(self.temp_dir, ignore_errors=True)
 log.info(f"[Orchestrator] Cleaned up temp dir: {self.temp_dir}")
 except Exception as e:
 log.warning(f"[Orchestrator] Cleanup warning: {e}")


# ============================================================================
# PUBLIC API
# ============================================================================

def run_transcript_crew(video_url: str) -> dict:
 """
 Main entry point. Instantiates the orchestrator and runs the full crew.

 Args:
 video_url: Google Drive share URL of the video.

 Returns:
 dict with keys: status, txt_output, json_output, word_count,
 transcript_preview, error (if failed)
 """
 orchestrator = TranscriptOrchestrator(video_url=video_url)
 return orchestrator.run()


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
 TARGET_URL = (
 "https://drive.google.com/file/d/1yQyoUiH8jobHcx6n9vy5hSGRAMzEJ0ow/view?usp=drivesdk"
 )

 print("\n" + "=" * 60)
 print(" VIDEO TRANSCRIPT ORCHESTRATOR + CREW")
 print("=" * 60)
 print(f" Target: {TARGET_URL}")
 print("=" * 60 + "\n")

 result = run_transcript_crew(TARGET_URL)

 print("\n" + "=" * 60)
 print(" RESULT")
 print("=" * 60)

 if result["status"] == "success":
 print(f" Status : SUCCESS")
 print(f" Words : {result['word_count']}")
 print(f" TXT File : {result['txt_output']}")
 print(f" JSON File : {result['json_output']}")
 print(f"\n TRANSCRIPT PREVIEW:\n")
 print(result["transcript_preview"])
 else:
 print(f" Status : FAILED")
 print(f" Error : {result['error']}")

 print("\n" + "=" * 60)
```