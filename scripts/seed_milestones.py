#!/usr/bin/env python3
"""Atlas M26 -- one-time idempotent milestone seed.
Inserts all milestones across 5 roadmaps into orc-postgres milestones table.
Safe to re-run: uses INSERT ... ON CONFLICT DO NOTHING.
Usage: python scripts/seed_milestones.py [--dry-run]
"""
from __future__ import annotations
import argparse, os, sys

# Format: (codename, mid, title, status, blocked_by, eta, notes)
MILESTONES = [
    # ATLAS
    ("atlas","M1","L4 Close-Loop","shipped",None,"2026-04-25","Telegram 3-button row, Notion Status + task_outcomes"),
    ("atlas","M2","Skip Self-Heal","shipped",None,"2026-04-25","griot_scheduler backfills skipped slots same-day"),
    ("atlas","M3","Reconciliation Polling","blocked","7 days tap-failure data from M1","2026-05-11+","Query LI/X, auto-flip Notion status on missed taps"),
    ("atlas","M3.7","Voice Learning Layer","shipped",None,"2026-05-06","Voice fingerprint + Earned Insight Gate in agents.py"),
    ("atlas","M4","Concierge Crew","shipped",None,"2026-05-08","Log triage, approval_queue. 10 tests."),
    ("atlas","M5","Chairman Crew (L5 Learn)","active","7 task_outcomes in DB","2026-05-11","enabled=false dry_run=true. Gate lifts when DB reaches 7 outcomes."),
    ("atlas","M6","Hunter Crew","shipped",None,"2026-05-05","50 leads/day. sw_email_log T1-T5 tracking live."),
    ("atlas","M7a/b","Auto-Publish via Blotato","shipped",None,"2026-04-25","L3 closed. Mon-Sat, time slots, past-due stagger."),
    ("atlas","M8","CEO Desk Dashboard","active",None,None,"Dashboard live. Decision Inbox partial."),
    ("atlas","M8b","Live Agent Graph","shipped",None,"2026-05-10","Polls /atlas/agents every 30s."),
    ("atlas","M9-12","Chat Contracts Routing Startup","shipped",None,"2026-04-26","Full chat loop, autonomy contracts, OpenRouter, env hard-fail."),
    ("atlas","M13-15","Spend Notion Links Task Add","shipped",None,"2026-04-30","Provider billing API, clickable Notion, /task add."),
    ("atlas","M16","Cross-provider token tracking","blocked","3 months OR data","2026-08-01","No public API for Claude Code / Codex / Console."),
    ("atlas","M17","Kie.ai Spend Tracking","blocked","Kie usage API exists",None,"Credits-remaining only today."),
    ("atlas","M18","HALO Loop","blocked","OTel instrumentation + 50 traces","2026-05-18","Instrument heartbeat ticks with OTel JSONL."),
    ("atlas","M19","Atlas CRM Dashboard","shipped",None,"2026-05-10","Native Supabase sales board. Replaces Notion CRM."),
    ("atlas","M20","Native Social Publisher","blocked","$5K MRR OR Blotato fails",None,"Direct OAuth YT/IG/TikTok/LI/X."),
    ("atlas","M21-22","Overnight Ambient LLM Blog","blocked","M18 data + ranking signal",None,"Laptop-off agent runs."),
    ("atlas","M23","Agent-to-Agent Spawning","shipped",None,"2026-05-10","spawner.py + minion_worker. /atlas/agents. 10 tests."),
    ("atlas","M24","Hermes Self-Healing Execution","shipped",None,"2026-05-10","Worktree sandbox isolation for autonomous edits."),
    ("atlas","M25","Event-Driven Agent Message Bus","blocked","M23 + M24 stable 30 days","2026-06-10","Ambient execution loop across agents."),
    ("atlas","M9d","Deep Memory Garden A/B/C","blocked","Sequential A then B then C","2026-05-18","Weekly synthesis, distillation, connections."),
    ("atlas","M26","Live Roadmap DB","active",None,"2026-05-10","milestones table + flip_milestone + /shipped + webchat intent."),
    # ECHO
    ("echo","Substrate","tasks table + coordination primitives","shipped",None,None,"claim/enqueue/propose/ack/reject live on orc-postgres"),
    ("echo","M1","/propose /ack /reject commands","shipped",None,"2026-05-10","Infrastructure shipped. Commit use case descoped 2026-05-10."),
    ("echo","M2","Second proposal kind","descoped",None,None,"Gate assumed wrong use case. Jumping to M3 directly."),
    ("echo","M2.5","Push Gate file-locking","shipped",None,None,"gate_agent.py Layer 3. CLAUDE.md file-lock Layer 1."),
    ("echo","M3","Multi-agent ingestion","active","No blockers",None,"Wire Griot/Hunter/Studio/Concierge to Echo queue."),
    ("echo","M4","Auto-detection","deferred","M1-M3 in real use",None,"Convention-driven /propose is the right primitive."),
    ("echo","M5","Reversible redirection","deferred","3 rollback incidents needed",None,"git stash/reset sufficient today."),
    # COMPASS
    ("compass","M0","Governance scaffolding","shipped",None,"2026-05-02","GOVERNANCE.md 64-line routing table + folder-purpose hook."),
    ("compass","M1","AGENTS.md compliance audit","shipped",None,"2026-05-02","100% folder coverage. 17 AGENTS.md written."),
    ("compass","M2","5 enforcement hooks","shipped",None,"2026-05-02","memory-frontmatter, session-log, redundancy, doc-size, retirement. 31 tests."),
    ("compass","M2.5","Routing evaluator (gbrain)","shipped",None,"2026-05-09","check_routing_gaps.py live."),
    ("compass","M2.5b","Routing fixtures 100% + strict mode","shipped",None,"2026-05-10","69/69 skills have fixtures. Hook flips to strict mode. Compass complete."),
    ("compass","M3","Quarterly purge cadence","shipped",None,"2026-08-02","Cron armed. Fires automatically."),
    ("compass","M4","LLM-readable governance manifest","shipped",None,"2026-05-02","governance.manifest.json + validator + 7 tests."),
    ("compass","M5","output/ submodule reconciliation","shipped",None,"2026-05-02","gitmodules canonicalized."),
    ("compass","M6","Security scan gate v1+v2+v3","shipped",None,"2026-05-04","7 scan patterns + acceptance fixtures."),
    ("compass","M6-audit","Monthly config self-audit","queued",None,"2026-05-16","4 checks: secrets, hook shell-outs, broad permissions, non-TLS MCPs."),
    ("compass","M7","Branch discipline + secret scan hardening","shipped",None,"2026-05-10","CLAUDE_AGENT_ID injection, vendor token scanner, gate-side token scan."),
    # STUDIO
    ("studio","M1","Engine + 3-channel batch","shipped",None,"2026-04-25","Trend Scout + Pipeline DB + QA Crew."),
    ("studio","M2","Brand Identity","shipped",None,"2026-05-03","Brand bibles + DESIGN.md palettes locked for all 3 channels."),
    ("studio","M3","Content Production Pipeline","shipped",None,"2026-05-05","Script, voice, visuals, ffmpeg, Drive. 11 QA checks."),
    ("studio","M3.4","Scene Motion Upgrade","shipped",None,"2026-05-10","Hook+Climax, Kai Seedance video."),
    ("studio","M3.5","Channel Cloner Pipeline","blocked","M3 confirmed working video",None,"Reference channels, style profile, scripts."),
    ("studio","M3.6","Content Intelligence Layer","active","M5 analytics ROI proof",None,"Dossiers injecting into script crew."),
    ("studio","M3.7","Content Multiplier + Remix QA","shipped",None,"2026-05-07","9 pieces/source, 3-verdict QA, Telegram callbacks wired."),
    ("studio","M4","Multi-Channel Publish Pipeline","active","30-day platform warm-up","2026-06-09","All Blotato account IDs wired. First TikTok live 2026-05-10."),
    ("studio","M5","Performance Tracking + Analytics","blocked","10+ published assets/channel","2026-06-15","M5-lite TikTok scraper running."),
    ("studio","M6","Monetization Wiring","blocked","YT: 1k subs / 4k watch-hours",None,"AdSense application + affiliate signups."),
    ("studio","M7","Channel 3 (Wealth Atlas)","blocked","M6 on one channel + 30 days stable",None,"Engine exists. Brand + niche tuning only."),
    ("studio","M8","Channel 4 + Operations Layer","blocked","M7 stable for 60 days","2027",None),
    # HARVEST
    ("harvest","R1","First Signal Works contract","active","Rod reply hold ends 2026-05-14","2026-05-14","Demo site + audit brief sent. $500 setup + $497/mo."),
    ("harvest","R1a","Score-report conversion methodology","active",None,None,"8-step playbook + hook-and-deliverable architecture locked."),
    ("harvest","R1c","website-teardown skill","shipped",None,"2026-05-04","6-phase thin orchestrator. Internal viability + client-facing reports."),
    ("harvest","R1d","catalystworks.consulting self-teardown","shipped",None,"2026-05-01","Verdict: ITERATE. 9 patches queued."),
    ("harvest","R1e","catalystworks.consulting v3-WOW","active","Tier 2 due 2026-05-15",None,"Three.js hero + Constraints AI demo + Calendly CTA."),
    ("harvest","R1f","frontend-design art direction lift","shipped",None,"2026-05-04","6-field Kie prompt template + design-audit.md 80+ checks."),
    ("harvest","R1g","Enrichment pipeline + harvest-until-50","shipped",None,"2026-05-07","Hunter wired. Apollo two-step fixed. 50 leads/day target."),
    ("harvest","R2","SaaS Audit offer ($500 flat)","shipped",None,"2026-05-04","PDF + Drive link + SW T5 sequence Day 17 upsell."),
    ("harvest","R3","First CW Signal Session ($497)","blocked","R1 closes OR LinkedIn converts",None,"Discovery Call OS v2.0 ready."),
    ("harvest","R4","We are your AI dept SKU ($997/mo)","blocked","R1 + R3 both close",None,"One offer page. Zero new infra."),
    ("harvest","R5","Client portal","blocked","First client explicitly requests it",None,"Try weekly email report first."),
    ("harvest","R6","Repeatable lead source","blocked","100+ contacts + 30 days data","2026-06-07",None),
    ("harvest","R7","transcript-style-dna lift test","active",None,"2026-06-01","KEEP if 20pct+ reply lift vs baseline. DELETE if not."),
    ("harvest","R-auto","CW AI automation delivery ($3-5K/build)","blocked","R1 closes OR inbound inquiry","2026-07-04","n8n-mcp installed."),
    ("harvest","R-news","The Weekly Signal newsletter","active",None,None,"Listmonk self-hosted. Growth target: 500 subs."),
    ("harvest","R-sever","Notion CRM sever","shipped",None,"2026-05-07","Sync code deleted. Supabase = sole SOR."),
    ("harvest","R-brand","Brand guide audit + rebuild","queued",None,"2026-06-17","CW/SW/Studio/humanatwork.ai consistency audit."),
]


def seed(dry_run: bool = False) -> None:
    if dry_run:
        for (codename, mid, title, status, blocked_by, eta, notes) in MILESTONES:
            print(f"  DRY: {codename}/{mid} [{status}] {title[:55]}")
        print(f"Total: {len(MILESTONES)} milestones")
        return
    import psycopg2
    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "orc-postgres"),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        port=5432,
    )
    cur = conn.cursor()
    inserted = skipped = 0
    for (codename, mid, title, status, blocked_by, eta, notes) in MILESTONES:
        is_shipped = status == "shipped"
        cur.execute(
            "INSERT INTO milestones (codename, mid, title, status, blocked_by, eta, notes, shipped_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, " + ("NOW()" if is_shipped else "NULL") + ") "
            "ON CONFLICT (codename, mid) DO NOTHING",
            (codename, mid, title, status, blocked_by, eta, notes),
        )
        if cur.rowcount:
            inserted += 1
        else:
            skipped += 1
    conn.commit()
    print(f"Seed complete: {inserted} inserted, {skipped} skipped (already existed).")
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Atlas M26 milestones table")
    parser.add_argument("--dry-run", action="store_true", help="print rows without inserting")
    args = parser.parse_args()
    seed(dry_run=args.dry_run)
