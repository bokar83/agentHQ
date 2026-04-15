```python
# =============================================================================
# USAGE INSTRUCTIONS
# =============================================================================
# This script sends a task message to the Orchestrator agent requesting
# extraction of a video transcript from a Google Drive video file.
#
# HOW TO RUN:
# python send_to_orchestrator.py
#
# REQUIREMENTS:
# pip install requests
#
# CONFIGURATION:
# - Set ORCHESTRATOR_API_URL to your Orchestrator endpoint
# - Set ORCHESTRATOR_API_KEY if authentication is required
# - The script will poll for completion and print the transcript
#
# EXPECTED OUTPUT:
# - JSON response with transcript text and metadata
# - Transcript saved to 'transcript_output.json' in the working directory
# =============================================================================

import json
import time
import logging
import requests
from datetime import datetime, timezone
from typing import Optional

# ---------------------------------------------------------------------------
# LOGGING SETUP
# ---------------------------------------------------------------------------
logging.basicConfig(
 level=logging.INFO,
 format="%(asctime)s [%(levelname)s] %(message)s",
 datefmt="%Y-%m-%dT%H:%M:%S"
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
# Replace with your actual Orchestrator endpoint and API key
ORCHESTRATOR_API_URL: str = "http://localhost:8000/orchestrator/task" # <-- UPDATE THIS
ORCHESTRATOR_API_KEY: str = "" # <-- UPDATE THIS if auth is required

# Polling configuration
POLL_INTERVAL_SECONDS: int = 5 # How often to check for completion
MAX_WAIT_SECONDS: int = 600 # Maximum wait time (10 minutes)
RETRY_ATTEMPTS: int = 3 # Retries on network failure
RETRY_BACKOFF_BASE: int = 2 # Exponential backoff base (seconds)

# Video details
VIDEO_URL: str = "https://drive.google.com/file/d/1yQyoUiH8jobHcx6n9vy5hSGRAMzEJ0ow/view?usp=drivesdk"
FILE_ID: str = "1yQyoUiH8jobHcx6n9vy5hSGRAMzEJ0ow"
OUTPUT_FILE: str = "transcript_output.json"


# ---------------------------------------------------------------------------
# TASK MESSAGE BUILDER
# ---------------------------------------------------------------------------
def build_task_message() -> dict:
 """
 Constructs the structured task message to send to the Orchestrator.
 The message content is exactly as specified by the user.
 """
 return {
 "agent": "orchestrator",
 "action": "delegate_task",
 "task": {
 "type": "video_transcript_extraction",
 # --- EXACT MESSAGE AS REQUESTED ---
 "message": "Get the transcript of this video. https://drive.google.com/file/d/1yQyoUiH8jobHcx6n9vy5hSGRAMzEJ0ow/view?usp=drivesdk",
 "video_url": VIDEO_URL,
 "file_id": FILE_ID,
 "source": "google_drive"
 },
 "priority": "normal",
 "callback_required": True,
 "submitted_at": datetime.now(timezone.utc).isoformat()
 }


# ---------------------------------------------------------------------------
# HTTP HELPER WITH RETRY + EXPONENTIAL BACKOFF
# ---------------------------------------------------------------------------
def post_with_retry(
 url: str,
 payload: dict,
 headers: dict,
 attempts: int = RETRY_ATTEMPTS
) -> Optional[requests.Response]:
 """
 Sends a POST request with retry logic and exponential backoff.

 Args:
 url: Target endpoint URL.
 payload: JSON payload to send.
 headers: HTTP headers (including auth if needed).
 attempts: Number of retry attempts before giving up.

 Returns:
 requests.Response on success, None on total failure.
 """
 for attempt in range(1, attempts + 1):
 try:
 logger.info(f"Attempt {attempt}/{attempts}: POST {url}")
 response = requests.post(
 url,
 json=payload,
 headers=headers,
 timeout=30 # 30-second connection timeout
 )
 response.raise_for_status() # Raise on 4xx/5xx
 return response

 except requests.exceptions.ConnectionError as e:
 logger.warning(f"Connection error: {e}")
 except requests.exceptions.Timeout:
 logger.warning("Request timed out.")
 except requests.exceptions.HTTPError as e:
 logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
 # Don't retry on client errors (4xx), they won't self-resolve
 if e.response.status_code < 500:
 return None

 if attempt < attempts:
 wait = RETRY_BACKOFF_BASE ** attempt
 logger.info(f"Retrying in {wait}s...")
 time.sleep(wait)

 logger.error("All retry attempts exhausted.")
 return None


# ---------------------------------------------------------------------------
# POLL FOR TASK COMPLETION
# ---------------------------------------------------------------------------
def poll_for_result(task_id: str, headers: dict) -> Optional[dict]:
 """
 Polls the Orchestrator status endpoint until the task completes
 or the maximum wait time is exceeded.

 Args:
 task_id: The task ID returned by the Orchestrator on submission.
 headers: HTTP headers for authenticated requests.

 Returns:
 The completed task result dict, or None on timeout/failure.
 """
 status_url = f"{ORCHESTRATOR_API_URL}/{task_id}/status"
 elapsed = 0

 logger.info(f"Polling for task completion (max {MAX_WAIT_SECONDS}s)...")

 while elapsed < MAX_WAIT_SECONDS:
 try:
 response = requests.get(status_url, headers=headers, timeout=15)
 response.raise_for_status()
 data = response.json()

 status = data.get("status", "unknown")
 logger.info(f"Task status: {status} (elapsed: {elapsed}s)")

 if status == "completed":
 return data # Task finished, return full result
 elif status in ("failed", "error"):
 logger.error(f"Task failed: {data.get('error', 'Unknown error')}")
 return None
 # Otherwise: still processing, keep polling

 except requests.exceptions.RequestException as e:
 logger.warning(f"Poll request failed: {e}")

 time.sleep(POLL_INTERVAL_SECONDS)
 elapsed += POLL_INTERVAL_SECONDS

 logger.error(f"Timed out after {MAX_WAIT_SECONDS}s waiting for transcript.")
 return None


# ---------------------------------------------------------------------------
# SAVE TRANSCRIPT TO FILE
# ---------------------------------------------------------------------------
def save_transcript(result: dict) -> None:
 """
 Saves the transcript result to a local JSON file.

 Args:
 result: The completed task result from the Orchestrator.
 """
 output = {
 "status": "success",
 "transcript": result.get("transcript", ""),
 "metadata": {
 "video_url": VIDEO_URL,
 "duration": result.get("duration", "unknown"),
 "language": result.get("language", "unknown"),
 "extraction_method": result.get("extraction_method", "unknown"),
 "timestamp": datetime.now(timezone.utc).isoformat()
 }
 }

 with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
 json.dump(output, f, indent=2, ensure_ascii=False)

 logger.info(f"Transcript saved to: {OUTPUT_FILE}")
 print("\n" + "=" * 60)
 print("TRANSCRIPT PREVIEW (first 500 chars):")
 print("=" * 60)
 print(output["transcript"][:500])
 print("=" * 60)


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------
def main() -> None:
 """
 Main execution flow:
 1. Build the task message
 2. Send to Orchestrator
 3. Poll for completion
 4. Save and display transcript
 """
 # Build headers
 headers = {"Content-Type": "application/json"}
 if ORCHESTRATOR_API_KEY:
 headers["Authorization"] = f"Bearer {ORCHESTRATOR_API_KEY}"

 # Step 1: Build the task message
 task_message = build_task_message()
 logger.info("Task message constructed:")
 logger.info(json.dumps(task_message, indent=2))

 # Step 2: Send to Orchestrator
 logger.info(f"Sending task to Orchestrator at: {ORCHESTRATOR_API_URL}")
 response = post_with_retry(ORCHESTRATOR_API_URL, task_message, headers)

 if response is None:
 logger.error("Failed to deliver task to Orchestrator. Aborting.")
 # Save the task message locally so it can be retried manually
 with open("pending_task.json", "w") as f:
 json.dump(task_message, f, indent=2)
 logger.info("Task message saved to 'pending_task.json' for manual retry.")
 return

 # Parse the Orchestrator's acknowledgement
 ack = response.json()
 task_id = ack.get("task_id")
 logger.info(f"Orchestrator acknowledged task. Task ID: {task_id}")

 if not task_id:
 logger.error("No task_id in Orchestrator response. Cannot poll for status.")
 logger.error(f"Full response: {ack}")
 return

 # Step 3: Poll for completion
 result = poll_for_result(task_id, headers)

 if result is None:
 logger.error("Could not retrieve transcript from Orchestrator.")
 return

 # Step 4: Save and display transcript
 save_transcript(result)
 logger.info("Done. Transcript extraction complete.")


# ---------------------------------------------------------------------------
# STANDALONE DEMO MODE
# (Runs without a live Orchestrator, shows the message that would be sent)
# ---------------------------------------------------------------------------
def demo_mode() -> None:
 """
 Demonstrates the task message that will be sent to the Orchestrator.
 Use this to verify the message format before connecting to a live system.
 """
 print("\n" + "=" * 60)
 print("ORCHESTRATOR TASK MESSAGE (DEMO MODE)")
 print("=" * 60)
 task_message = build_task_message()
 print(json.dumps(task_message, indent=2))
 print("=" * 60)
 print("\nEXACT MESSAGE TO ORCHESTRATOR:")
 print(f' "{task_message["task"]["message"]}"')
 print("=" * 60)
 print("\nTo send to a live Orchestrator:")
 print(" 1. Set ORCHESTRATOR_API_URL in the script")
 print(" 2. Set ORCHESTRATOR_API_KEY if required")
 print(" 3. Run: python send_to_orchestrator.py --live")
 print("=" * 60 + "\n")


if __name__ == "__main__":
 import sys

 if "--live" in sys.argv:
 # Live mode: actually send to Orchestrator
 main()
 else:
 # Default: demo mode (safe, no network calls)
 demo_mode()
```