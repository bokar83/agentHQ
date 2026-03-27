"""
security_agent.py — SecureWatch Daily Security Agent
Catalyst Works — agentsHQ

Runs daily to scan for secrets, audit git hygiene, check VPS health,
and send a WhatsApp report to Boubacar.
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "orchestrator"))

from scripts.scan_secrets import scan_workspace_for_secrets
from scripts.audit_git import audit_git_hygiene
from scripts.vps_check import check_vps_health


# ── Config ────────────────────────────────────────────────────────────────────

WORKSPACE_ROOT = str(PROJECT_ROOT)
LOG_DIR = PROJECT_ROOT / "logs" / "security"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Directories to skip during scanning
SCAN_SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "qdrant_data", "postgres_data", "waha_sessions",
}

# Files to skip
SCAN_SKIP_FILES = {
    ".env",  # Allowed to have secrets locally, never committed
}

# ── Main ──────────────────────────────────────────────────────────────────────

def run_daily_scan() -> dict:
    """Run all security checks and return a consolidated report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "status": "CLEAN",
        "findings": [],
        "summary": {},
    }

    print(f"\n🔐 SecureWatch Daily Scan — {report['timestamp']}")
    print("=" * 60)

    # 1. Secret scan
    print("\n[1/3] Scanning workspace for secrets...")
    secret_findings = scan_workspace_for_secrets(
        root=WORKSPACE_ROOT,
        skip_dirs=SCAN_SKIP_DIRS,
        skip_files=SCAN_SKIP_FILES,
    )
    report["summary"]["secrets_found"] = len(secret_findings)
    if secret_findings:
        report["status"] = "CRITICAL"
        report["findings"].extend(secret_findings)
        for f in secret_findings:
            print(f"  ❌ SECRET: {f['file']}:{f['line']} — {f['type']}")
    else:
        print("  ✅ No secrets detected in workspace files")

    # 2. Git hygiene audit
    print("\n[2/3] Auditing git hygiene...")
    git_findings = audit_git_hygiene(workspace=WORKSPACE_ROOT)
    report["summary"]["git_issues"] = len(git_findings)
    if git_findings:
        if report["status"] != "CRITICAL":
            report["status"] = "WARNING"
        report["findings"].extend(git_findings)
        for f in git_findings:
            print(f"  ⚠️  GIT: {f['message']}")
    else:
        print("  ✅ Git hygiene looks good")

    # 3. VPS health check (only runs if VPS_IP is set)
    vps_ip = os.environ.get("VPS_IP")
    if vps_ip:
        print(f"\n[3/3] Checking VPS health ({vps_ip})...")
        vps_findings = check_vps_health(vps_ip)
        report["summary"]["vps_issues"] = len(vps_findings)
        if vps_findings:
            if report["status"] != "CRITICAL":
                report["status"] = "WARNING"
            report["findings"].extend(vps_findings)
            for f in vps_findings:
                print(f"  ⚠️  VPS: {f['message']}")
        else:
            print("  ✅ VPS health looks good")
    else:
        print("\n[3/3] Skipping VPS check (VPS_IP not set in env)")
        report["summary"]["vps_issues"] = "skipped"

    # ── Log report ────────────────────────────────────────────
    log_file = LOG_DIR / f"scan-{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(log_file, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n📄 Report saved to: {log_file}")

    # ── Print summary ─────────────────────────────────────────
    print("\n" + "=" * 60)
    status_icon = "✅" if report["status"] == "CLEAN" else ("🚨" if report["status"] == "CRITICAL" else "⚠️")
    print(f"{status_icon} Overall status: {report['status']}")
    print(f"   Secrets found:  {report['summary'].get('secrets_found', 0)}")
    print(f"   Git issues:     {report['summary'].get('git_issues', 0)}")
    print(f"   VPS issues:     {report['summary'].get('vps_issues', 'skipped')}")

    return report


def format_whatsapp_message(report: dict) -> str:
    """Format the security report for WhatsApp delivery."""
    status = report["status"]
    icon = "✅" if status == "CLEAN" else ("🚨" if status == "CRITICAL" else "⚠️")
    total_issues = (
        report["summary"].get("secrets_found", 0) +
        (report["summary"].get("git_issues", 0) if isinstance(report["summary"].get("git_issues"), int) else 0)
    )

    lines = [
        f"{icon} *SecureWatch Daily Report*",
        f"📅 {report['timestamp'][:10]}",
        f"🔒 Status: *{status}*",
        "",
        f"• Secrets found: {report['summary'].get('secrets_found', 0)}",
        f"• Git issues: {report['summary'].get('git_issues', 0)}",
        f"• VPS issues: {report['summary'].get('vps_issues', 'skipped')}",
    ]

    if report["findings"]:
        lines.append("")
        lines.append("*🔴 Issues requiring attention:*")
        for finding in report["findings"][:5]:  # Limit to 5 for WhatsApp readability
            msg = finding.get("message") or f"{finding.get('type')} in {finding.get('file')}"
            lines.append(f"  • {msg}")
        if len(report["findings"]) > 5:
            lines.append(f"  ... and {len(report['findings']) - 5} more (see log)")

    return "\n".join(lines)


if __name__ == "__main__":
    # Load environment
    env_file = PROJECT_ROOT / "infrasctructure" / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)

    report = run_daily_scan()

    # Exit with non-zero if issues found (useful for CI/cron alerting)
    if report["status"] == "CRITICAL":
        sys.exit(2)
    elif report["status"] == "WARNING":
        sys.exit(1)
    sys.exit(0)
