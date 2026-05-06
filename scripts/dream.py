#!/usr/bin/env python3
"""
dream.py — Local Dreams-style memory consolidation with human-in-the-loop approval.

Flow:
    1. [auto] Scan memory/ + recent git history
    2. [auto] Claude proposes changes, writes dream-output/ + PROPOSAL.md
    3. [you]  Read PROPOSAL.md, decide: approve / reject / edit
    4. [auto] python scripts/dream.py --apply   → implements approved changes

Usage:
    python scripts/dream.py              # run scan + propose (step 1-2)
    python scripts/dream.py --apply      # implement proposal (step 4)
    python scripts/dream.py --status     # show current proposal status
    python scripts/dream.py --sessions N # how many recent commits to mine (default: 30)
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
import requests
from pathlib import Path
from datetime import datetime

import anthropic

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent
MEMORY_DIR = Path(os.environ.get(
    "MEMORY_DIR",
    r"C:\Users\HUAWEI\.claude\projects\d--Ai-Sandbox-agentsHQ\memory"
))
HANDOFF_DIR = REPO_ROOT / "docs" / "handoff"
OUTPUT_DIR = MEMORY_DIR / "dream-output"
ARCHIVE_DIR = MEMORY_DIR / "dream-archive"
PROPOSAL_FILE = OUTPUT_DIR / "PROPOSAL.md"
APPROVAL_FILE = OUTPUT_DIR / "APPROVAL.txt"

MODEL = "claude-opus-4-7"
MAX_TOKENS = 16000

# ── Telegram ──────────────────────────────────────────────────────────────────

def _tg_send(text: str) -> int | None:
    """Send message to owner Telegram chat. Returns message_id or None."""
    token = os.environ.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return None
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    last_id = None
    for chunk in chunks:
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": chunk},
                timeout=10,
            )
            if resp.ok:
                last_id = resp.json().get("result", {}).get("message_id")
        except Exception:
            pass
    return last_id


def _tg_send_with_buttons(text: str) -> int | None:
    """Send proposal with ✅ Approve / ❌ Reject inline buttons. Returns message_id."""
    token = os.environ.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return None
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    last_id = None
    for i, chunk in enumerate(chunks):
        payload: dict = {"chat_id": chat_id, "text": chunk}
        # Only attach buttons to last chunk
        if i == len(chunks) - 1:
            payload["reply_markup"] = {
                "inline_keyboard": [[
                    {"text": "✅ Approve", "callback_data": "dream:approve"},
                    {"text": "❌ Reject",  "callback_data": "dream:reject"},
                ]]
            }
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json=payload, timeout=10,
            )
            if r.ok:
                last_id = r.json().get("result", {}).get("message_id")
        except Exception:
            pass
    return last_id


def _tg_register_window(msg_id: int) -> None:
    """Tell the orchestrator container to register a dream reply window for msg_id."""
    vps_url = os.environ.get("ORCHESTRATOR_URL", "http://72.60.209.109:8000")
    try:
        requests.post(
            f"{vps_url}/dream/register-window",
            json={"msg_id": msg_id},
            timeout=5,
        )
    except Exception:
        pass  # non-fatal — /dream approve fallback still works


# ── Helpers ───────────────────────────────────────────────────────────────────

def read_memory_files() -> dict[str, str]:
    files = {}
    for p in sorted(MEMORY_DIR.glob("*.md")):
        if p.name.endswith(".original.md"):
            continue
        if p.name in ("MEMORY_ARCHIVE.md",):
            continue
        try:
            files[p.name] = p.read_text(encoding="utf-8")
        except Exception as e:
            print(f"  warn: could not read {p.name}: {e}", file=sys.stderr)
    return files


def read_session_transcripts(n_commits: int) -> str:
    lines = []
    try:
        log = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "log",
             f"-{n_commits}", "--pretty=format:COMMIT %h %ai %s",
             "--name-only", "--diff-filter=AM"],
            text=True, stderr=subprocess.DEVNULL
        )
        lines.append("=== RECENT GIT COMMITS ===")
        lines.append(log[:8000])
    except Exception:
        lines.append("(git log unavailable)")

    handoff_files = sorted(HANDOFF_DIR.glob("*.md"), reverse=True)[:5] if HANDOFF_DIR.exists() else []
    for hf in handoff_files:
        try:
            content = hf.read_text(encoding="utf-8")[:3000]
            lines.append(f"\n=== HANDOFF: {hf.name} ===")
            lines.append(content)
        except Exception:
            pass

    return "\n".join(lines)


def build_prompt(memory_files: dict[str, str], transcripts: str) -> str:
    files_block = ""
    for name, content in memory_files.items():
        files_block += f"\n\n--- FILE: {name} ---\n{content}"

    return f"""You are a memory consolidation agent. Analyze the memory store and propose changes.

YOUR OUTPUT must be a JSON object with two sections:
1. "proposal" — human-readable change list (markdown) for Boubacar to approve
2. "files" — the actual new file contents to write if approved

ANALYSIS RULES:
- Merge duplicates: files covering same rule/fact → one file (list which files merged)
- Resolve contradictions: keep LATEST value, note what changed
- Archive stale project_* entries: shipped work, old state → prefix output name with "ARCHIVE_"
- Surface new insights from transcripts: patterns not yet written down → new feedback file
- Compress verbose files: keep every rule, cut waffle. Target ≤150 words per file.
- MEMORY.md: rebuild index, keep "always-load zone" structure, hard cap 200 lines
- Keep all four frontmatter fields: name, description, type, body

PROPOSAL FORMAT (the "proposal" field) must be readable markdown:

## Memory Dream Proposal — {datetime.now().strftime('%Y-%m-%d')}

### Files to MERGE (N files → 1)
- `file_a.md` + `file_b.md` → `file_a.md`
  Reason: [why they overlap]
  What changes: [what the merged version says that neither said cleanly]

### Files to ARCHIVE (stale state)
- `project_x.md` → ARCHIVE (reason: shipped 2026-05-04, no longer active state)

### Files to COMPRESS (verbose → tight)
- `feedback_x.md`: [what gets cut]

### New insights surfaced from git/handoffs
- [new rule observed] → `feedback_new_thing.md`

### MEMORY.md changes
- Removed N entries (archived files)
- Added N entries (new insights)
- New line count: N

### No change
- [list files not touched and why]

---

Respond with JSON only, no prose outside it:
{{
  "proposal": "<the full markdown proposal above>",
  "files": {{
    "filename.md": "full new content",
    "ARCHIVE_old_project.md": "full content — will be moved to dream-archive/",
    "MEMORY.md": "new index content"
  }}
}}

=== CURRENT MEMORY FILES ===
{files_block}

=== SESSION TRANSCRIPTS ===
{transcripts[:6000]}

Today: {datetime.now().strftime('%Y-%m-%d')}
"""


# ── Step 1-2: Scan + Propose ──────────────────────────────────────────────────

def run_propose(n_commits: int) -> None:
    client = anthropic.Anthropic()

    print("Reading memory files...")
    memory_files = read_memory_files()
    print(f"  {len(memory_files)} files")

    print(f"Mining {n_commits} recent commits + handoff docs...")
    transcripts = read_session_transcripts(n_commits)

    print(f"Calling {MODEL} to analyze and propose... (1-3 min)")
    with client.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": build_prompt(memory_files, transcripts)}]
    ) as stream:
        response = stream.get_final_message()

    text = next((b.text for b in response.content if b.type == "text"), "")
    print(f"  {response.usage.output_tokens} output tokens")

    # Strip markdown fences if present
    text = text.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]

    try:
        result = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"ERROR: response not valid JSON: {e}", file=sys.stderr)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "_raw_response.txt").write_text(text, encoding="utf-8")
        print("Raw saved to dream-output/_raw_response.txt")
        raise

    # Write outputs
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Clear previous run
    for f in OUTPUT_DIR.glob("*.md"):
        f.unlink()
    if APPROVAL_FILE.exists():
        APPROVAL_FILE.unlink()

    # Write proposed files
    for filename, content in result.get("files", {}).items():
        (OUTPUT_DIR / filename).write_text(content, encoding="utf-8")

    # Write human-readable proposal
    proposal_text = result.get("proposal", "(no proposal generated)")
    proposal_full = f"""{proposal_text}

---
## To approve or reject this proposal:

Edit this file OR create dream-output/APPROVAL.txt with one of:
  APPROVE       — implement all proposed changes
  REJECT        — discard, keep current memory unchanged
  APPROVE EXCEPT <filename1>, <filename2>  — implement all but these files

Then run: python scripts/dream.py --apply
"""
    PROPOSAL_FILE.write_text(proposal_full, encoding="utf-8")

    print(f"\nProposal written to: {PROPOSAL_FILE}")
    print(f"Proposed file changes in: {OUTPUT_DIR}")

    # Send to Telegram
    summary = result.get("proposal", "(no proposal)")[:3000]
    if len(result.get("proposal", "")) > 3000:
        summary += f"\n\n[...truncated. Full proposal in PROPOSAL.md]"
    tg_text = summary + "\n\n---\nTap a button or reply: approve / reject / approve except X, Y"
    msg_id = _tg_send_with_buttons(tg_text)
    if msg_id:
        # Write .pending so VPS knows a proposal exists (survives container restart)
        PENDING_FILE = OUTPUT_DIR / ".pending"
        chat_id = os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID", "")
        PENDING_FILE.write_text(chat_id, encoding="utf-8")
        _tg_register_window(msg_id)
        print(f"Proposal sent to Telegram with buttons (msg_id={msg_id}).")
    else:
        print("Telegram not configured or send failed.")
        print("Fallback: create dream-output/APPROVAL.txt then run --apply")


# ── Step 4: Apply on Approval ─────────────────────────────────────────────────

def run_apply() -> None:
    if not PROPOSAL_FILE.exists():
        print("ERROR: No proposal found. Run without --apply first.", file=sys.stderr)
        sys.exit(1)

    # Read approval decision
    if not APPROVAL_FILE.exists():
        print("ERROR: No APPROVAL.txt found in dream-output/.", file=sys.stderr)
        print("Create dream-output/APPROVAL.txt with: APPROVE / REJECT / APPROVE EXCEPT <files>")
        sys.exit(1)

    decision = APPROVAL_FILE.read_text(encoding="utf-8").strip().upper()

    if decision.startswith("REJECT"):
        print("Decision: REJECTED. Memory store unchanged.")
        shutil.rmtree(OUTPUT_DIR)
        print("dream-output/ cleared.")
        return

    # Parse exclusions
    excluded = set()
    if decision.startswith("APPROVE EXCEPT"):
        rest = APPROVAL_FILE.read_text(encoding="utf-8").strip()
        rest = rest[len("APPROVE EXCEPT"):].strip()
        excluded = {f.strip() for f in rest.split(",")}
        print(f"Decision: APPROVE EXCEPT {excluded}")
    elif decision.startswith("APPROVE"):
        print("Decision: APPROVE ALL")
    else:
        print(f"ERROR: Unrecognized decision: {decision!r}", file=sys.stderr)
        print("Must be: APPROVE / REJECT / APPROVE EXCEPT <file1>, <file2>")
        sys.exit(1)

    # Archive current memory files before applying
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_archive = ARCHIVE_DIR / f"pre_dream_{ts}"
    session_archive.mkdir()

    archived_count = 0
    for p in MEMORY_DIR.glob("*.md"):
        if p.name in ("MEMORY_ARCHIVE.md",):
            continue
        shutil.copy2(p, session_archive / p.name)
        archived_count += 1
    print(f"Archived {archived_count} originals to {session_archive.name}/")

    # Apply proposed files
    applied = []
    skipped = []
    for src in OUTPUT_DIR.glob("*.md"):
        if src.name in ("PROPOSAL.md",):
            continue
        if src.name in excluded:
            skipped.append(src.name)
            continue

        if src.name.startswith("ARCHIVE_"):
            dest = ARCHIVE_DIR / src.name
        else:
            dest = MEMORY_DIR / src.name

        shutil.copy2(src, dest)
        applied.append(src.name)

    print(f"Applied: {len(applied)} files")
    if skipped:
        print(f"Skipped (excluded): {skipped}")

    # Clean up dream-output
    shutil.rmtree(OUTPUT_DIR)
    print("dream-output/ cleared.")
    print("\nDone. Memory store updated. Start a new session to validate.")


# ── Status ────────────────────────────────────────────────────────────────────

def run_status() -> None:
    if not OUTPUT_DIR.exists() or not PROPOSAL_FILE.exists():
        print("No active proposal. Run: python scripts/dream.py")
        return

    print(f"Active proposal: {PROPOSAL_FILE}")
    files = list(OUTPUT_DIR.glob("*.md"))
    print(f"Proposed files: {len(files)}")

    if APPROVAL_FILE.exists():
        decision = APPROVAL_FILE.read_text(encoding="utf-8").strip()
        print(f"Approval set: {decision}")
        print("Ready to apply: python scripts/dream.py --apply")
    else:
        print("Waiting for approval. Create dream-output/APPROVAL.txt")

    print(f"\n--- PROPOSAL SUMMARY ---")
    proposal = PROPOSAL_FILE.read_text(encoding="utf-8")
    # Print first 50 lines
    lines = proposal.splitlines()[:50]
    print("\n".join(lines))
    if len(proposal.splitlines()) > 50:
        print(f"\n... ({len(proposal.splitlines()) - 50} more lines in {PROPOSAL_FILE})")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Local Dreams-style memory consolidation")
    parser.add_argument("--apply", action="store_true",
                        help="Implement approved proposal")
    parser.add_argument("--status", action="store_true",
                        help="Show current proposal status")
    parser.add_argument("--sessions", type=int, default=30, metavar="N",
                        help="Recent commits to mine (default: 30)")
    args = parser.parse_args()

    if args.apply:
        run_apply()
    elif args.status:
        run_status()
    else:
        run_propose(n_commits=args.sessions)


if __name__ == "__main__":
    main()
