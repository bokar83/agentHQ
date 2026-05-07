"""
The Forge CLI -- Unified command-line interface for The Forge 2.0.

Usage:
    forge log "message" --agent Agent --status Success
    forge task add "title" --priority P1 --due 2026-04-12
    forge task done <page_id>
    forge pipeline add "Company" --value 5000 --status Discovery
    forge revenue 2500 --source Consulting --buyer "Acme"
    forge content idea "title" --platform LinkedIn --topic AI
    forge content queue <page_id> --scheduled 2026-04-10
    forge content posted <page_id>
    forge kpi refresh
    forge status
    forge p0 "Task name"
    forge p0 "Task name" --date YYYY-MM-DD
    forge p0 list
    forge streak
    forge checkin --nn 1,2,3
    forge phase get
    forge phase set N
    forge phase check
    forge weekly
"""
import argparse
import hashlib
import sys
from datetime import date, timedelta

sys.stdout.reconfigure(encoding="utf-8")

from skills.forge_cli import config
from skills.forge_cli.databases import ForgeDB
from skills.forge_cli.kpi import KPIRefresher
from skills.forge_cli.system_config import SystemConfig, load_forge_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="forge", description="The Forge 2.0 CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # -- log --
    log_p = subparsers.add_parser("log", help="Log an agent action")
    log_p.add_argument("message", help="Action description")
    log_p.add_argument("--agent", default="System", help="Agent name")
    log_p.add_argument("--status", default="Success", choices=["Success", "In Progress", "Failed"])

    # -- task --
    task_p = subparsers.add_parser("task", help="Manage tasks")
    task_sub = task_p.add_subparsers(dest="task_command")
    task_add = task_sub.add_parser("add", help="Add a task")
    task_add.add_argument("title", help="Task title")
    task_add.add_argument("--priority", default="P2", choices=["P1", "P2", "P3", "High", "Medium", "Low"])
    task_add.add_argument("--due", default="", help="Due date (YYYY-MM-DD)")
    task_add.add_argument("--owner", default="Boubacar")
    task_done = task_sub.add_parser("done", help="Mark task done")
    task_done.add_argument("page_id", help="Notion page ID of the task")

    # -- pipeline --
    pipe_p = subparsers.add_parser("pipeline", help="Manage consulting pipeline")
    pipe_sub = pipe_p.add_subparsers(dest="pipeline_command")
    pipe_add = pipe_sub.add_parser("add", help="Add a lead")
    pipe_add.add_argument("company", help="Company name")
    pipe_add.add_argument("--contact", default="")
    pipe_add.add_argument("--email", default="")
    pipe_add.add_argument("--value", type=int, default=0)
    pipe_add.add_argument("--status", default="New")
    pipe_add.add_argument("--source", default="LinkedIn")

    # -- revenue --
    rev_p = subparsers.add_parser("revenue", help="Log revenue")
    rev_p.add_argument("amount", type=float, help="Dollar amount")
    rev_p.add_argument("--source", default="Consulting")
    rev_p.add_argument("--buyer", default="")
    rev_p.add_argument("--description", default="")

    # -- content --
    cont_p = subparsers.add_parser("content", help="Manage content board")
    cont_sub = cont_p.add_subparsers(dest="content_command")
    cont_idea = cont_sub.add_parser("idea", help="Add content idea")
    cont_idea.add_argument("title", help="Post title or headline")
    cont_idea.add_argument("--platform", default="LinkedIn", help="Comma-separated platforms")
    cont_idea.add_argument("--topic", default="", help="Comma-separated topics")
    cont_idea.add_argument("--type", default="Post", dest="content_type")
    cont_queue = cont_sub.add_parser("queue", help="Queue content for posting")
    cont_queue.add_argument("page_id", help="Content page ID")
    cont_queue.add_argument("--scheduled", required=True, help="Scheduled date (YYYY-MM-DD)")
    cont_posted = cont_sub.add_parser("posted", help="Mark content as posted")
    cont_posted.add_argument("page_id", help="Content page ID")

    # -- kpi --
    kpi_p = subparsers.add_parser("kpi", help="KPI operations")
    kpi_sub = kpi_p.add_subparsers(dest="kpi_command")
    kpi_sub.add_parser("refresh", help="Refresh KPI callout blocks")

    # -- status --
    subparsers.add_parser("status", help="Print system status summary")

    # -- p0 --
    p0_p = subparsers.add_parser("p0", help="Set or view the P0 (single most important task of the day) for a day")
    p0_p.add_argument("p0_arg", nargs="?", default=None, help="Task name, 'list', or 'complete'")
    p0_p.add_argument("--date", dest="p0_date", default="", help="Date (YYYY-MM-DD), defaults to today")
    p0_p.add_argument("--day-type", dest="day_type", default="A-Day", choices=["A-Day", "B-Day"], help="A-Day=revenue focus, B-Day=admin/recovery")

    # -- streak --
    subparsers.add_parser("streak", help="Show and update execution streak")

    # -- checkin --
    checkin_p = subparsers.add_parser("checkin", help="Daily check-in with non-negotiables")
    checkin_p.add_argument("--nn", required=True, help="Comma-separated NN numbers, e.g. 1,2,3")

    # -- phase --
    phase_p = subparsers.add_parser("phase", help="Phase management")
    phase_sub = phase_p.add_subparsers(dest="phase_command")
    phase_sub.add_parser("get", help="Show current phase info")
    phase_set = phase_sub.add_parser("set", help="Advance to next phase")
    phase_set.add_argument("phase_number", type=int, help="Phase number (0-3)")
    phase_sub.add_parser("check", help="Check unlock criteria for next phase")

    # -- weekly --
    subparsers.add_parser("weekly", help="Generate weekly review")

    return parser


NN_COUNT_BY_PHASE = {0: 3, 1: 5, 2: 5, 3: 5}

NN_LABELS = {
    1: "NN1: Move",
    2: "NN2: Revenue Action",
    3: "NN3: P0 Done",
    4: "NN4: Shutdown Run",
    5: "NN5: Screens Off",
}


def run_command(args):
    db = ForgeDB()

    if args.command == "log":
        result = db.log_action(args.message, agent=args.agent, status=args.status)
        print(f"Logged: {result.get('url', result.get('id'))}")

    elif args.command == "task":
        if args.task_command == "add":
            result = db.add_task(args.title, priority=args.priority, due=args.due, owner=args.owner)
            print(f"Task added: {result.get('url', result.get('id'))}")
        elif args.task_command == "done":
            result = db.mark_task_done(args.page_id)
            print(f"Task marked done: {args.page_id}")

    elif args.command == "pipeline":
        if args.pipeline_command == "add":
            result = db.add_pipeline_lead(args.company, contact=args.contact, email=args.email, value=args.value, status=args.status, source=args.source)
            print(f"Lead added: {result.get('url', result.get('id'))}")

    elif args.command == "revenue":
        result = db.log_revenue(args.amount, source=args.source, buyer=args.buyer, description=args.description)
        print(f"Revenue logged: {result.get('url', result.get('id'))}")

    elif args.command == "content":
        if args.content_command == "idea":
            platforms = [p.strip() for p in args.platform.split(",")]
            topics = [t.strip() for t in args.topic.split(",")] if args.topic else []
            result = db.add_content_idea(args.title, platforms=platforms, topics=topics, content_type=args.content_type)
            print(f"Idea added: {result.get('url', result.get('id'))}")
        elif args.content_command == "queue":
            result = db.update_content_status(args.page_id, status="Queued", scheduled_date=args.scheduled)
            print(f"Content queued for {args.scheduled}")
        elif args.content_command == "posted":
            result = db.update_content_status(args.page_id, status="Posted", posted_date=date.today().isoformat())
            print(f"Content marked posted: {args.page_id}")

    elif args.command == "kpi":
        if args.kpi_command == "refresh":
            _run_kpi_refresh(db)

    elif args.command == "status":
        _run_status(db)

    elif args.command == "p0":
        _run_p0(db, args, sc=SystemConfig(client=db.client))

    elif args.command == "streak":
        _run_streak(db)

    elif args.command == "checkin":
        _run_checkin(db, args)

    elif args.command == "phase":
        _run_phase(db, args)

    elif args.command == "weekly":
        _run_weekly(db)


# ---- KPI Refresh (extended) ----

def _run_kpi_refresh(db: ForgeDB):
    kpi = KPIRefresher(client=db.client)
    results = kpi.refresh_all()
    for r in results:
        print(r)

    # Extended: quotes + streak + motivation + phase + week grid
    sc = SystemConfig(client=db.client)
    cfg = sc.get()
    streak = cfg["streak"]
    phase_label = cfg["phase_label"]
    forge_cfg = load_forge_config()
    client = db.client

    # Rotating quote -- deterministic by date, changes daily
    QUOTES = [
        ("The secret of getting ahead is getting started.", "Mark Twain"),
        ("You don't rise to the level of your goals. You fall to the level of your systems.", "James Clear"),
        ("Revenue is the applause of a market that values what you do.", "Unknown"),
        ("Do the work. The work is the shortcut.", "Seth Godin"),
        ("Every action you take is a vote for the person you want to become.", "James Clear"),
        ("Chase the vision, not the money. The money will end up following you.", "Tony Hsieh"),
        ("If you are not embarrassed by the first version of your product, you've launched too late.", "Reid Hoffman"),
        ("The best time to plant a tree was 20 years ago. The second best time is now.", "Chinese Proverb"),
        ("Discipline equals freedom.", "Jocko Willink"),
        ("Work like there is someone working 24 hours a day to take it all away from you.", "Mark Cuban"),
        ("It's not about ideas. It's about making ideas happen.", "Scott Belsky"),
        ("You are what you repeatedly do. Excellence is not an act but a habit.", "Aristotle"),
        ("The way to get started is to quit talking and begin doing.", "Walt Disney"),
        ("Small daily improvements compound into remarkable results.", "Unknown"),
        ("Stop selling. Start helping.", "Zig Ziglar"),
        ("Your network is your net worth.", "Porter Gale"),
        ("The goal is not to be perfect by the end. The goal is to be better today.", "Simon Sinek"),
        ("Revenue solves all known startup problems.", "Unknown"),
        ("Done is better than perfect.", "Sheryl Sandberg"),
        ("Show me your calendar and I'll show you your priorities.", "Unknown"),
        ("Focus is a matter of deciding what things you're not going to do.", "John Carmack"),
        ("A year from now you'll wish you had started today.", "Karen Lamb"),
        ("The most dangerous risk of all: playing it too safe.", "Unknown"),
        ("Build something 100 people love, not something 1 million people kind of like.", "Paul Graham"),
        ("If you want to go fast, go alone. If you want to go far, go together.", "African Proverb"),
        ("Discipline is choosing between what you want now and what you want most.", "Augusta F. Kantra"),
        ("The entrepreneur always searches for change, responds to it, and exploits it.", "Peter Drucker"),
        ("Your most important task today: one revenue conversation.", "Unknown"),
        ("Winners are not people who never fail, but people who never quit.", "Edwin Louis Cole"),
        ("A year from now you'll wish you had started today.", "Karen Lamb"),
    ]
    day_index = int(hashlib.md5(date.today().isoformat().encode()).hexdigest(), 16) % len(QUOTES)
    q_text, q_author = QUOTES[day_index]
    quote_text = f'"{q_text}" -- {q_author}'
    if "quotes_callout_id" in forge_cfg and forge_cfg["quotes_callout_id"]:
        client.update_block(forge_cfg["quotes_callout_id"], {
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": quote_text}}],
                "icon": {"type": "emoji", "emoji": "\U0001f4ac"},
                "color": "yellow_background",
            }
        })

    # Update streak callout
    day_word = "day" if streak == 1 else "days"
    streak_text = f"Execution Streak: {streak} {day_word} | {phase_label}"
    client.update_block(forge_cfg["streak_callout_id"], {
        "callout": {
            "rich_text": [{"type": "text", "text": {"content": streak_text}}],
            "icon": {"type": "emoji", "emoji": "\U0001f525"},
            "color": "orange_background",
        }
    })

    # Motivation message
    STREAK_MESSAGES = [
        (0, 0, "Day zero. Set your P0 and run the shutdown ritual tonight."),
        (1, 6, "Building the foundation. Don't break the chain."),
        (7, 13, "One week in. This is where most people quit."),
        (14, 20, "Halfway to Phase 1 unlock. Stay boring."),
        (21, 29, "Almost there. One clean week left."),
        (30, 9999, "Phase 1 unlock criteria met. Check your revenue log."),
    ]
    motivation = "Day zero. Set your P0 and run the shutdown ritual tonight."
    for low, high, msg in STREAK_MESSAGES:
        if low <= streak <= high:
            motivation = msg
            break
    icon = "\U0001f977" if cfg["phase"] < 3 else "\U0001f451"
    client.update_block(forge_cfg["motivation_callout_id"], {
        "callout": {
            "rich_text": [{"type": "text", "text": {"content": motivation}}],
            "icon": {"type": "emoji", "emoji": icon},
            "color": "blue_background",
        }
    })

    # This Week grid rebuild
    DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    today = date.today()
    monday = today - timedelta(days=today.weekday())

    week_p0_pages = client.query_database(
        config.TASKS_DB,
        filter_obj={
            "and": [
                {"property": "P0", "checkbox": {"equals": True}},
                {"property": "Due Date", "date": {"on_or_after": monday.isoformat()}},
                {"property": "Due Date", "date": {"on_or_before": (monday + timedelta(days=4)).isoformat()}},
            ]
        },
    )
    by_day = {}
    for p in week_p0_pages:
        due = (p["properties"].get("Due Date", {}).get("date") or {}).get("start")
        if due:
            by_day[due] = p

    STATUS_COLOR = {
        "Done": "green_background",
        "In Progress": "yellow_background",
        "Not Started": "default",
        "Killed": "red_background",
    }

    nn_total = NN_COUNT_BY_PHASE.get(cfg["phase"], 5)
    for i, (day_key, day_label) in enumerate(zip(DAY_NAMES, DAY_LABELS)):
        target_date = (monday + timedelta(days=i)).isoformat()
        block_id = forge_cfg["week_grid_ids"][day_key]
        if target_date in by_day:
            p = by_day[target_date]
            props = p["properties"]
            task_name = "".join([t["plain_text"] for t in (props.get("Task", {}).get("title") or [])])
            task_name = task_name[:40] if len(task_name) > 40 else task_name
            status = (props.get("Status", {}).get("select") or {}).get("name", "Not Started")
            nns = props.get("Non-Negotiables", {}).get("multi_select") or []
            nn_done = len(nns)
            text = f"{day_label} / A-Day\n{task_name}\n{status}\nNN: {nn_done}/{nn_total}"
            color = STATUS_COLOR.get(status, "default")
        else:
            text = f"{day_label} / A-Day\nNo P0 set\n--\nNN: 0/{nn_total}"
            color = "gray_background"
        client.update_block(block_id, {
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
                "icon": {"type": "emoji", "emoji": "\U0001f4c5"},
                "color": color,
            }
        })

    # Phase block
    phase = cfg["phase"]
    phase_start = cfg["phase_start"]
    days_in_phase = (date.today() - date.fromisoformat(phase_start)).days
    criteria = SystemConfig.UNLOCK_CRITERIA.get(phase, [])
    unlock_parts = []
    for label, key, _ in criteria:
        mark = "x" if cfg.get(key, False) else " "
        short = label.split(": ", 1)[1] if ": " in label else label
        unlock_parts.append(f"[{mark}] {short}")
    unlock_str = "  ".join(unlock_parts) if unlock_parts else "No criteria"
    phase_text = f"{cfg['phase_label']} | Day {days_in_phase} | Unlock: {unlock_str}"
    if "phase_callout_id" in forge_cfg and forge_cfg["phase_callout_id"]:
        client.update_block(forge_cfg["phase_callout_id"], {
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": phase_text}}],
                "icon": {"type": "emoji", "emoji": "\u2699\ufe0f"},
                "color": "gray_background",
            }
        })

    # Log
    db.log_action("KPI refresh complete", agent="ForgeOS", status="Success")
    print("Quote + streak + motivation + phase + week grid updated.")


# ---- Status ----

def _run_status(db: ForgeDB):
    kpi = KPIRefresher(client=db.client)
    sc = SystemConfig(client=db.client)
    cfg = sc.get()
    print("\n  The Forge 2.0 -- Status")
    print("  " + "=" * 35)
    print(f"  Pipeline:      ${kpi.compute_pipeline_total():,.0f}")
    print(f"  Revenue MTD:   ${kpi.compute_revenue_mtd():,.0f}")
    print(f"  Posts (month):  {kpi.compute_posts_this_month()}")
    print(f"  Tasks (week):  {kpi.compute_tasks_done_this_week()}")
    print(f"  Streak:        {cfg['streak']} days")
    print(f"  Phase:         {cfg['phase_label']}")
    print("  " + "=" * 35 + "\n")


# ---- P0 ----
# P0 = the single most important task of the day. One task. Non-negotiable.
# If nothing else gets done today, the P0 gets done.

def _run_p0(db: ForgeDB, args, sc: SystemConfig = None):
    if args.p0_arg == "list":
        _p0_list(db)
        return

    if args.p0_arg == "complete":
        _p0_complete(db, sc)
        return

    if not args.p0_arg:
        print("P0 = the single most important task of the day (one task, non-negotiable).")
        print("Usage: forge p0 \"Task name\" [--date YYYY-MM-DD] [--day-type A-Day|B-Day]")
        print("       forge p0 list")
        print("       forge p0 complete")
        return

    task_name = args.p0_arg
    target_date = args.p0_date if args.p0_date else date.today().isoformat()
    day_type = args.day_type

    existing = db.get_p0_for_date(target_date)
    if existing:
        old_title = "".join([t["plain_text"] for t in (existing["properties"].get("Task", {}).get("title") or [])])
        print(f"Existing P0 for {target_date}: {old_title}")
        answer = input("Replace it? (yes/no): ").strip().lower()
        if answer != "yes":
            print("Cancelled.")
            return
        db.uncheck_p0(existing["id"])

    if sc is None:
        sc = SystemConfig(client=db.client)
    phase = sc.get()["phase"]
    db.create_p0(task_name, target_date, phase=phase, day_type=day_type)
    print(f"P0 set for {target_date}: {task_name} [{day_type}]")


def _p0_complete(db: ForgeDB, sc: SystemConfig = None):
    """Mark today's P0 as Done and update streak."""
    today_str = date.today().isoformat()
    today_p0 = db.get_p0_for_date(today_str)
    if not today_p0:
        print("No P0 found for today. Run: forge p0 \"Task name\"")
        return

    title = "".join([t["plain_text"] for t in (today_p0["properties"].get("Task", {}).get("title") or [])])
    status = (today_p0["properties"].get("Status", {}).get("select") or {}).get("name", "")
    if status == "Done":
        print(f"P0 already Done: {title}")
        return

    db.mark_task_done(today_p0["id"])

    if sc is None:
        sc = SystemConfig(client=db.client)
    cfg = sc.get()
    count, qualifying_ids = db.calculate_streak()
    for pid in qualifying_ids:
        db.set_streak_anchor(pid, True)
    new_longest = max(count, cfg["longest_streak"])
    streak_updates = {"streak": count, "longest_streak": new_longest}
    # Auto-trigger 30-day streak unlock
    if count >= 30 and not cfg["p0_1_streak"]:
        streak_updates["p0_1_streak"] = True
        print("UNLOCK: 30-day streak criteria met.")
    sc.update(**streak_updates)

    day_word = "day" if count == 1 else "days"
    print(f"P0 Done: {title}")
    print(f"Streak: {count} {day_word}. Run: forge kpi refresh")


def _p0_list(db: ForgeDB):
    today_str = date.today().isoformat()
    tomorrow_str = (date.today() + timedelta(days=1)).isoformat()

    today_p0 = db.get_p0_for_date(today_str)
    tomorrow_p0 = db.get_p0_for_date(tomorrow_str)

    if today_p0:
        title = "".join([t["plain_text"] for t in (today_p0["properties"].get("Task", {}).get("title") or [])])
        status = (today_p0["properties"].get("Status", {}).get("select") or {}).get("name", "Not Started")
        print(f"Today ({today_str}):    {title} [{status}]")
    else:
        print(f"Today ({today_str}):    No P0 set")

    if tomorrow_p0:
        title = "".join([t["plain_text"] for t in (tomorrow_p0["properties"].get("Task", {}).get("title") or [])])
        status = (tomorrow_p0["properties"].get("Status", {}).get("select") or {}).get("name", "Not Started")
        print(f"Tomorrow ({tomorrow_str}): {title} [{status}]")
    else:
        print(f"Tomorrow ({tomorrow_str}): No P0 set")
        print("No P0 set for tomorrow. Set it during tonight's shutdown ritual.")


# ---- Streak ----

def _run_streak(db: ForgeDB):
    count, qualifying_ids = db.calculate_streak()
    sc = SystemConfig(client=db.client)
    cfg = sc.get()
    prev_longest = cfg["longest_streak"]

    # Clear old streak anchors not in qualifying_ids
    old_anchors = db.client.query_database(
        config.TASKS_DB,
        filter_obj={"property": "Streak Anchor", "checkbox": {"equals": True}},
    )
    for page in old_anchors:
        if page["id"] not in qualifying_ids:
            db.set_streak_anchor(page["id"], False)

    # Mark qualifying tasks as streak anchors
    for pid in qualifying_ids:
        db.set_streak_anchor(pid, True)

    # Update SystemConfig
    new_longest = max(count, prev_longest)
    updates = {"streak": count, "longest_streak": new_longest}
    if count == 0:
        updates["streak_start"] = date.today().isoformat()
    # Do not reset streak_start when count > 0; it was set correctly when the streak began
    sc.update(**updates)

    print(f"Current streak: {count} days")
    print(f"Longest streak: {new_longest} days")
    if count > 0:
        print("Keep it going: complete today's P0 and run forge checkin")
    else:
        print("Streak is at zero. Set today's P0 with: forge p0 [task]")
        print("Complete it, then run: forge checkin --nn 1,2,3")


# ---- Checkin ----

def _run_checkin(db: ForgeDB, args):
    sc = SystemConfig(client=db.client)
    cfg = sc.get()
    phase = cfg["phase"]

    # Parse NN list
    nn_list = [int(n.strip()) for n in args.nn.split(",") if n.strip().isdigit()]

    # Phase 0 gate
    if phase == 0:
        blocked = [n for n in nn_list if n in (4, 5)]
        if blocked:
            print("NN4 and NN5 activate at Phase 1. Nice try though.")
            sys.exit(1)

    # Find today's P0
    today_str = date.today().isoformat()
    today_p0 = db.get_p0_for_date(today_str)
    if not today_p0:
        print("No P0 found for today. Run forge p0 first.")
        return

    # Build NN labels
    selected_labels = [NN_LABELS[n] for n in nn_list if n in NN_LABELS]

    # Update P0 task with Non-Negotiables
    db.client.update_page(today_p0["id"], properties={
        "Non-Negotiables": {"multi_select": [{"name": label} for label in selected_labels]},
    })

    nn_total = NN_COUNT_BY_PHASE.get(phase, 5)
    all_nns_done = len(selected_labels) == nn_total

    # Auto-mark P0 Done when all NNs are complete
    p0_marked_done = False
    current_status = (today_p0["properties"].get("Status", {}).get("select") or {}).get("name", "")
    if all_nns_done and current_status != "Done":
        db.mark_task_done(today_p0["id"])
        p0_marked_done = True

    # Run streak calculation and update SystemConfig
    count, qualifying_ids = db.calculate_streak()
    for pid in qualifying_ids:
        db.set_streak_anchor(pid, True)
    prev_longest = cfg["longest_streak"]
    new_longest = max(count, prev_longest)
    streak_updates = {"streak": count, "longest_streak": new_longest}
    # Auto-trigger unlock criteria
    if count >= 30 and not cfg.get("p0_1_streak", False):
        streak_updates["p0_1_streak"] = True
        print("UNLOCK: 30-day streak criteria met.")
    sc.update(**streak_updates)

    # Check A-Day revenue warning
    day_type = (today_p0["properties"].get("Day Type", {}).get("select") or {}).get("name", "")
    if day_type == "A-Day":
        todays_tasks = db.get_todays_tasks()
        has_revenue_action = any(
            t["properties"].get("Revenue Action", {}).get("checkbox", False)
            for t in todays_tasks
        )
        if not has_revenue_action:
            print("Warning: Today is an A-Day but no revenue action task is checked.")

    # Tomorrow P0
    tomorrow_str = (date.today() + timedelta(days=1)).isoformat()
    tomorrow_p0 = db.get_p0_for_date(tomorrow_str)
    tomorrow_name = "not set"
    if tomorrow_p0:
        tomorrow_name = "".join([t["plain_text"] for t in (tomorrow_p0["properties"].get("Task", {}).get("title") or [])])

    day_word = "day" if count == 1 else "days"
    print(f"Checked in. NNs complete: {len(selected_labels)}/{nn_total}. Streak: {count} {day_word}.")
    if p0_marked_done:
        print("P0 marked Done automatically.")
    elif not all_nns_done:
        print(f"P0 not yet Done -- complete remaining NNs, then run: forge p0 complete")
    print(f"Tomorrow's P0: {tomorrow_name}")
    print("Run: forge kpi refresh to update your dashboard.")


# ---- Phase ----

def _run_phase(db: ForgeDB, args):
    if args.phase_command == "get":
        _phase_get(db)
    elif args.phase_command == "set":
        _phase_set(db, args.phase_number)
    elif args.phase_command == "check":
        _phase_check(db)
    else:
        print("Usage: forge phase get | forge phase set N | forge phase check")


def _phase_get(db: ForgeDB):
    sc = SystemConfig(client=db.client)
    cfg = sc.get()
    phase = cfg["phase"]
    phase_start = cfg["phase_start"]
    days_in_phase = (date.today() - date.fromisoformat(phase_start)).days

    print(f"Current Phase: {phase}")
    print(f"Label: {cfg['phase_label']}")
    print(f"Active since: {phase_start} ({days_in_phase} days)")
    print(f"Current streak: {cfg['streak']} days")

    # Next phase
    next_phase = phase + 1
    if next_phase in SystemConfig.PHASE_LABELS:
        print(f"Next phase: {SystemConfig.PHASE_LABELS[next_phase]}")
    else:
        print("Next phase: None (max phase reached)")

    # Unlock criteria
    criteria = SystemConfig.UNLOCK_CRITERIA.get(phase, [])
    if criteria:
        print("Unlock criteria:")
        for label, key, _desc in criteria:
            checked = cfg.get(key, False)
            mark = "x" if checked else " "
            print(f"  [{mark}] {label}")
    else:
        print("No unlock criteria defined for this phase.")


def _phase_set(db: ForgeDB, target_phase: int):
    sc = SystemConfig(client=db.client)
    cfg = sc.get()
    current = cfg["phase"]

    if target_phase not in (0, 1, 2, 3):
        print("Phase must be 0, 1, 2, or 3.")
        return

    if target_phase != current + 1:
        print(f"Cannot jump from Phase {current} to Phase {target_phase}. Next valid phase is {current + 1}.")
        return

    # Check unlock criteria
    criteria = SystemConfig.UNLOCK_CRITERIA.get(current, [])
    all_met = all(cfg.get(key, False) for _, key, _ in criteria)

    if not all_met:
        print(f"Not all unlock criteria are met for Phase {target_phase}. Run forge phase check to see what is missing.")
        answer = input("Override anyway? (yes/no): ").strip().lower()
        if answer != "yes":
            print("Cancelled.")
            return

    label = SystemConfig.PHASE_LABELS[target_phase]
    sc.update(phase=target_phase, phase_label=label, phase_start=date.today().isoformat())
    print(f"Phase {target_phase} activated: {label}")
    print("The dashboard has been updated.")


def _phase_check(db: ForgeDB):
    sc = SystemConfig(client=db.client)
    cfg = sc.get()
    phase = cfg["phase"]
    criteria = SystemConfig.UNLOCK_CRITERIA.get(phase, [])

    if not criteria:
        print(f"No unlock criteria defined for Phase {phase}.")
        return

    print(f"Phase {phase} unlock criteria for Phase {phase + 1}:")
    all_met = True
    for label, key, desc in criteria:
        checked = cfg.get(key, False)
        mark = "x" if checked else " "
        print(f"  [{mark}] {label}")
        if not checked:
            all_met = False
            if "streak" in key.lower() or "streak" in desc.lower():
                print(f"        Current streak: {cfg['streak']} / Required: 30")

    if all_met:
        print(f"\nAll criteria met. Ready to advance.")
        print(f"Run: forge phase set {phase + 1}")
    else:
        print(f"\nSome criteria are not yet met.")


# ---- Weekly ----

def _run_weekly(db: ForgeDB):
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)

    # Get week tasks
    week_tasks = db.get_week_tasks()

    # P0 completion (Mon-Fri)
    p0_done = 0
    p0_total = 0
    revenue_actions = 0
    outcomes_filled = 0
    for t in week_tasks:
        props = t["properties"]
        due = (props.get("Due Date", {}).get("date") or {}).get("start", "")
        is_p0 = props.get("P0", {}).get("checkbox", False)
        if is_p0 and due and due <= friday.isoformat():
            p0_total += 1
            status = (props.get("Status", {}).get("select") or {}).get("name", "")
            if status == "Done":
                p0_done += 1
        if props.get("Revenue Action", {}).get("checkbox", False):
            revenue_actions += 1
        outcome = props.get("Outcome", {}).get("rich_text") or []
        if outcome and any(o.get("plain_text", "").strip() for o in outcome):
            outcomes_filled += 1

    # Content stats
    posted_pages = db.client.query_database(
        config.CONTENT_DB,
        filter_obj={
            "and": [
                {"property": "Posted Date", "date": {"on_or_after": monday.isoformat()}},
                {"property": "Posted Date", "date": {"on_or_before": friday.isoformat()}},
            ]
        },
    ) if config.CONTENT_DB else []
    posted = len(posted_pages)

    queued_pages = db.client.query_database(
        config.CONTENT_DB,
        filter_obj={"property": "Status", "select": {"equals": "Queued"}},
    ) if config.CONTENT_DB else []
    queued = len(queued_pages)

    # System config
    sc = SystemConfig(client=db.client)
    cfg = sc.get()
    days_in_phase = (today - date.fromisoformat(cfg["phase_start"])).days

    print(f"\n=== Weekly Review: Week of {monday.isoformat()} ===")
    print(f"P0 completion: {p0_done}/{p0_total if p0_total else 5} days")
    print(f"Current streak: {cfg['streak']} days")
    print(f"Revenue actions this week: {revenue_actions}")
    print(f"Content posted: {posted} | Queued: {queued}")
    print(f"Phase: {cfg['phase_label']} | Days in phase: {days_in_phase}")
    print("===")

    # Create weekly review page in Notion
    forge_cfg = load_forge_config()
    template_id = forge_cfg.get("weekly_review_template_id", "")

    review_title = f"Week of {monday.isoformat()} Review"
    stats_text = (
        f"P0 completion: {p0_done}/{p0_total if p0_total else 5} days\n"
        f"Current streak: {cfg['streak']} days\n"
        f"Revenue actions this week: {revenue_actions}\n"
        f"Content posted: {posted} | Queued: {queued}\n"
        f"Phase: {cfg['phase_label']} | Days in phase: {days_in_phase}"
    )

    # Create as child of the template's parent (The Forge 2.0 page)
    try:
        template_page = db.client.get_page(template_id)
        parent_id = template_page.get("parent", {}).get("page_id", "")
        if not parent_id:
            parent_id = template_page.get("parent", {}).get("database_id", "")

        if parent_id:
            result = db.client._request("post", "pages", json={
                "parent": {"page_id": parent_id},
                "properties": {
                    "title": [{"text": {"content": review_title}}],
                },
                "children": [
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "Stats"}}],
                        },
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": stats_text}}],
                        },
                    },
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "Wins"}}],
                        },
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": ""}}],
                        },
                    },
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "Lessons"}}],
                        },
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": ""}}],
                        },
                    },
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "Next Week Focus"}}],
                        },
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": ""}}],
                        },
                    },
                ],
            })
            page_url = result.get("url", result.get("id", ""))
            print(f"\nWeekly review page created: {page_url}")
        else:
            print("\nCould not determine parent page for weekly review.")
    except Exception as e:
        print(f"\nCould not create weekly review page: {e}")

    print("Open The Forge 2.0 to complete your written review.")


def kpi_refresh():
    """Public entry point for the scheduler -- runs full KPI refresh."""
    db = ForgeDB()
    _run_kpi_refresh(db)


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    run_command(args)


if __name__ == "__main__":
    main()
