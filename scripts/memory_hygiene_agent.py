"""Autonomous memory-hygiene agent (Compass C9).

Runs locally on operator workstation (NOT VPS — MEMORY.md is local-only by design,
see feedback_vps_no_memory_load.md). Scheduled via Windows Task Scheduler 1st of
month 06:00 MT.

Job:
1. Count MEMORY.md lines. Tier the result.
2. Scan docs/handoff/ for memory-rule file citations in the last 30 days.
3. Surface promotion candidates (rules cited 3+ times across 3+ distinct sessions).
4. Default: silent OK report written to digest file.
5. Exception (>180 lines OR promotion candidates): send Telegram message.

Decoupled from orchestrator/. Uses Telegram REST directly + local file scan.
No DB. No subprocess. No imports of orchestrator modules.

Exit codes:
  0 = OK (silent or exception alert sent)
  1 = config error (token missing, MEMORY.md not found)
  2 = unexpected exception
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib import request as urlrequest

# ---------- Config ----------

MEMORY_DIR = Path.home() / ".claude" / "projects" / "d--Ai-Sandbox-agentsHQ" / "memory"
MEMORY_FILE = MEMORY_DIR / "MEMORY.md"
REPO_ROOT = Path(__file__).resolve().parent.parent
HANDOFF_DIR = REPO_ROOT / "docs" / "handoff"
DIGEST_OUT = REPO_ROOT / "agent_outputs" / "memory_hygiene"

LINE_CAP_TRUNCATION = 200
LINE_CAP_TARGET = 180
LINE_CAP_WARN = 170
PROMOTION_FIRE_THRESHOLD = 3
COLD_DAYS = 60
CITATION_LOOKBACK_DAYS = 30


def _load_env() -> dict:
    """Read .env from repo root. Returns dict of key=value."""
    env_path = REPO_ROOT / ".env"
    env = {}
    if not env_path.exists():
        return env
    for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip("'\"")
    return env


def _telegram_send(token: str, chat_id: str, text: str) -> bool:
    """Direct Telegram REST. No orchestrator dependency."""
    if not token or not chat_id:
        return False
    if len(text) > 4096:
        text = text[:4090] + "\n[...]"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": str(chat_id), "text": text}).encode("utf-8")
    req = urlrequest.Request(
        url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urlrequest.urlopen(req, timeout=15) as resp:
            return resp.status == 200
    except Exception as exc:
        print(f"telegram_send failed: {exc}", file=sys.stderr)
        return False


# ---------- Job logic ----------

def count_memory_lines() -> int:
    return len(MEMORY_FILE.read_text(encoding="utf-8").splitlines())


def list_memory_topic_files() -> list[Path]:
    """All feedback_*.md / reference_*.md / project_*.md / *_BRAND.md files."""
    if not MEMORY_DIR.is_dir():
        return []
    out = []
    for p in MEMORY_DIR.iterdir():
        if p.is_file() and p.suffix == ".md" and p.name != "MEMORY.md":
            out.append(p)
    return out


_HANDOFF_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def _parse_handoff_date(filename: str) -> datetime | None:
    """Extract YYYY-MM-DD from handoff filename. Returns None if no date prefix."""
    m = _HANDOFF_DATE_RE.search(filename)
    if not m:
        return None
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=timezone.utc)
    except ValueError:
        return None


def collect_handoff_citations(lookback_days: int) -> dict[str, list[str]]:
    """Scan docs/handoff/ for `feedback_*.md` / `reference_*.md` / `project_*.md`
    filename mentions. Returns {filename: [handoff_doc_paths_that_cite_it]}.
    Only counts handoffs whose filename date (YYYY-MM-DD-*.md) is within lookback_days.
    Uses filename date, NOT mtime — archive moves rewrite mtime and would
    silently re-cite stale handoffs.
    """
    if not HANDOFF_DIR.is_dir():
        return {}
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    citations: dict[str, set[str]] = defaultdict(set)
    pattern = re.compile(r"(feedback_[A-Za-z0-9_\-]+\.md|reference_[A-Za-z0-9_\-]+\.md|project_[A-Za-z0-9_\-]+\.md)")
    for handoff in HANDOFF_DIR.rglob("*.md"):
        handoff_date = _parse_handoff_date(handoff.name)
        if handoff_date is None or handoff_date < cutoff:
            continue
        try:
            text = handoff.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in pattern.findall(text):
            citations[m].add(str(handoff.relative_to(REPO_ROOT)))
    return {k: sorted(v) for k, v in citations.items()}


def scan_promotion_candidates(citations: dict[str, list[str]]) -> list[dict]:
    """Files cited >= PROMOTION_FIRE_THRESHOLD across distinct handoffs."""
    candidates = []
    for filename, handoffs in citations.items():
        if len(handoffs) >= PROMOTION_FIRE_THRESHOLD:
            candidates.append({
                "rule": filename,
                "fire_count": len(handoffs),
                "handoffs": handoffs[:5],
            })
    candidates.sort(key=lambda c: -c["fire_count"])
    return candidates


def scan_cold_entries(topic_files: list[Path], citations: dict[str, list[str]]) -> list[str]:
    """Topic files with mtime > COLD_DAYS old AND zero citations in lookback."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=COLD_DAYS)
    cited = set(citations.keys())
    cold = []
    for f in topic_files:
        if f.name in cited:
            continue
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
        except OSError:
            continue
        if mtime < cutoff:
            cold.append(f.name)
    return sorted(cold)


# ---------- Report ----------

def build_report(line_count: int, candidates: list[dict], cold: list[str]) -> tuple[str, str, bool]:
    """Return (severity, text, exception_flag).
    severity = OK | WARN | BLOCK.
    exception_flag = True means send Telegram.
    """
    tier_msg = ""
    severity = "OK"
    exception = False

    if line_count > LINE_CAP_TARGET:
        severity = "BLOCK"
        tier_msg = f"MEMORY.md = {line_count} lines (over {LINE_CAP_TARGET} cap)."
        exception = True
    elif line_count > LINE_CAP_WARN:
        severity = "WARN"
        tier_msg = f"MEMORY.md = {line_count} lines (warn zone {LINE_CAP_WARN}-{LINE_CAP_TARGET})."
    else:
        tier_msg = f"MEMORY.md = {line_count} lines (OK)."

    if candidates:
        exception = True

    lines = [
        f"=== Memory Hygiene Report {datetime.now().strftime('%Y-%m-%d %H:%M')} ===",
        tier_msg,
        f"Promotion candidates: {len(candidates)} (rules fired >= {PROMOTION_FIRE_THRESHOLD}x in last {CITATION_LOOKBACK_DAYS}d)",
        f"Cold entries (>{COLD_DAYS}d, zero recent cites): {len(cold)}",
        "",
    ]

    if candidates:
        lines.append("--- Promotion candidates ---")
        for c in candidates:
            lines.append(f"  [{c['fire_count']}x] {c['rule']}")
            for h in c["handoffs"][:3]:
                lines.append(f"      └─ {h}")
        lines.append("")

    if cold:
        lines.append(f"--- Cold entries (up to 10 shown) ---")
        for name in cold[:10]:
            lines.append(f"  {name}")
        if len(cold) > 10:
            lines.append(f"  ... +{len(cold) - 10} more")
        lines.append("")

    if severity == "BLOCK":
        lines.append(">>> ACTION REQUIRED: MEMORY.md over cap. Run C8 prune again.")
    elif severity == "WARN":
        lines.append(">>> WATCH: approaching cap. Consider promotion of high-fire rules.")
    else:
        lines.append("No action needed.")

    return severity, "\n".join(lines), exception


def write_digest(severity: str, report: str) -> Path:
    DIGEST_OUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d")
    out = DIGEST_OUT / f"memory_hygiene_{stamp}.md"
    out.write_text(f"# Memory Hygiene — {stamp}\n\nSeverity: **{severity}**\n\n```\n{report}\n```\n", encoding="utf-8")
    return out


# ---------- Main ----------

def main(dry_run: bool = False) -> int:
    if not MEMORY_FILE.exists():
        print(f"ERROR: MEMORY.md not found at {MEMORY_FILE}", file=sys.stderr)
        return 1

    line_count = count_memory_lines()
    topic_files = list_memory_topic_files()
    citations = collect_handoff_citations(CITATION_LOOKBACK_DAYS)
    candidates = scan_promotion_candidates(citations)
    cold = scan_cold_entries(topic_files, citations)

    severity, report, exception = build_report(line_count, candidates, cold)
    digest_path = write_digest(severity, report)
    print(f"[memory_hygiene] severity={severity} lines={line_count} candidates={len(candidates)} cold={len(cold)}")
    print(f"[memory_hygiene] digest written: {digest_path}")

    if exception:
        if dry_run:
            print("[memory_hygiene] DRY RUN: would have sent Telegram alert")
        else:
            env = _load_env()
            token = env.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN") or env.get("TELEGRAM_BOT_TOKEN")
            chat_id = env.get("OWNER_TELEGRAM_CHAT_ID") or env.get("TELEGRAM_CHAT_ID")
            if not token or not chat_id:
                print("WARN: no Telegram creds in .env — exception not delivered", file=sys.stderr)
            else:
                sent = _telegram_send(token, chat_id, report)
                print(f"[memory_hygiene] telegram sent: {sent}")

    return 0


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    try:
        sys.exit(main(dry_run=dry_run))
    except Exception as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        sys.exit(2)
