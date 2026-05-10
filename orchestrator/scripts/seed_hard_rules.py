"""
seed_hard_rules.py — bootstrap the memory table with the 11 hard rules
from MEMORY.md / AGENT_SOP.md that every agent must respect.

Run once:
    python3 /app/orchestrator/scripts/seed_hard_rules.py
"""
import os
import sys

import psycopg2

# Allow running from /app root inside container
sys.path.insert(0, "/app")

RULES = [
    {
        "title": "Check access before claiming none",
        "rule": "Grep MEMORY.md + .env before saying 'I don't have access to X'. Telegram, VPS, Drive, GWS are ALL wired.",
        "reason": "Agents waste time asking Boubacar for access that is already configured.",
        "applies_to": "all",
        "tags": ["access", "infra"],
        "external_id": "hard-rule-check-access",
    },
    {
        "title": "Sabbath: no work Sunday",
        "rule": "Sunday = no work, no contact, no scheduled sends. Saturday = light, trade-only. 99% of outreach M-F.",
        "reason": "Boubacar observes Sabbath. Scheduling outreach on Sunday violates a personal hard constraint.",
        "applies_to": "outreach",
        "tags": ["schedule", "sabbath"],
        "external_id": "hard-rule-sabbath",
    },
    {
        "title": "Email both addresses",
        "rule": "Always send to bokar83@gmail.com AND boubacar@catalystworks.consulting. Send via gws in container, NOT Gmail MCP draft.",
        "reason": "Boubacar monitors both inboxes; missing one means missed notifications.",
        "applies_to": "outreach",
        "tags": ["email", "gws"],
        "external_id": "hard-rule-email-both",
    },
    {
        "title": "Never delete assets — archive instead",
        "rule": "Never delete files, records, or assets. Archive or holding pen only.",
        "reason": "Deletion is irreversible. Archiving preserves recovery options.",
        "applies_to": "all",
        "tags": ["archive", "assets"],
        "external_id": "hard-rule-no-delete",
    },
    {
        "title": "Never say FGM — always 1stGen",
        "rule": "Never use the term FGM. Always use '1stGen' or '1stGen Money' instead.",
        "reason": "FGM is a banned term; brand is officially renamed to 1stGen Money.",
        "applies_to": "content",
        "tags": ["brand", "1stgen"],
        "external_id": "hard-rule-no-fgm",
    },
    {
        "title": "Verified stats only",
        "rule": "Every stat needs a source URL in Notion before publish. No unverified numbers in content.",
        "reason": "Publishing wrong stats damages credibility and can create legal exposure.",
        "applies_to": "content",
        "tags": ["stats", "research"],
        "external_id": "hard-rule-verified-stats",
    },
    {
        "title": "Vercel = preview only, Hostinger = production",
        "rule": "Vercel is for preview and mobile testing ONLY. All production websites deploy to Hostinger.",
        "reason": "Production traffic must go through Hostinger; Vercel previews are not stable URLs for clients.",
        "applies_to": "deploy",
        "tags": ["vercel", "hostinger", "deploy"],
        "external_id": "hard-rule-vercel-preview-only",
    },
    {
        "title": "No push/deploy without gate review",
        "rule": "Never git push to main, SSH orc_rebuild.sh, or merge to main unless explicitly acting as Gate with Boubacar's inputs.",
        "reason": "Unreviewed pushes to production can break live pipelines and client-facing systems.",
        "applies_to": "deploy",
        "tags": ["gate", "git", "deploy"],
        "external_id": "hard-rule-gate-review",
    },
    {
        "title": "No Loom — use HyperFrames or screen-recorded MP4",
        "rule": "Never propose Loom. Use HyperFrames pitch reel, screen-recorded MP4, or no video.",
        "reason": "Loom is not in the approved tool stack and creates dependency on a third-party free tier.",
        "applies_to": "content",
        "tags": ["video", "loom"],
        "external_id": "hard-rule-no-loom",
    },
    {
        "title": "First name only in content",
        "rule": "Use 'Boubacar' not 'Boubacar Barry' in signature, byline, and body copy.",
        "reason": "Brand voice uses first name only. Full name in content feels formal and off-brand.",
        "applies_to": "content",
        "tags": ["brand", "voice"],
        "external_id": "hard-rule-first-name-only",
    },
    {
        "title": "Container deploy = git pull + docker compose up, NOT rebuild",
        "rule": "Code deploy: git pull && docker compose up -d orchestrator (~10 sec). Only rebuild when requirements.txt changes.",
        "reason": "Code dirs are volume-mounted. Rebuilding for code changes wastes 3-5 min and risks downtime.",
        "applies_to": "deploy",
        "tags": ["docker", "deploy", "infra"],
        "external_id": "hard-rule-no-rebuild-for-code",
    },
]


def main():
    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "agentshq-postgres-1"),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        port=5432,
    )
    cur = conn.cursor()

    for r in RULES:
        content = f"Rule: {r['rule']}\nReason: {r['reason']}\nApplies to: {r['applies_to']}"
        cur.execute(
            """
            INSERT INTO memory (source, category, title, content, tags, pipeline,
                                relevance_boost, external_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source, external_id)
            WHERE external_id IS NOT NULL
            DO UPDATE SET
                content = EXCLUDED.content,
                tags = EXCLUDED.tags,
                updated_at = NOW()
            RETURNING id
            """,
            (
                "seed_hard_rules",
                "hard_rule",
                r["title"],
                content,
                r["tags"],
                "general",
                2.0,
                r["external_id"],
            ),
        )
        row = cur.fetchone()
        print(f"  id={row[0]}  {r['title']}")

    conn.commit()
    conn.close()
    print(f"\nSeeded {len(RULES)} hard rules.")


if __name__ == "__main__":
    main()
