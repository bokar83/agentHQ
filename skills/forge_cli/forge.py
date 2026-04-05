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
"""
import argparse
import sys
from skills.forge_cli.databases import ForgeDB
from skills.forge_cli.kpi import KPIRefresher


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

    return parser


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
            from datetime import date as d
            result = db.update_content_status(args.page_id, status="Queued", scheduled_date=args.scheduled)
            print(f"Content queued for {args.scheduled}")
        elif args.content_command == "posted":
            from datetime import date as d
            result = db.update_content_status(args.page_id, status="Posted", posted_date=d.today().isoformat())
            print(f"Content marked posted: {args.page_id}")

    elif args.command == "kpi":
        if args.kpi_command == "refresh":
            kpi = KPIRefresher()
            results = kpi.refresh_all()
            for r in results:
                print(r)

    elif args.command == "status":
        kpi = KPIRefresher()
        print("\n  The Forge 2.0 -- Status")
        print("  " + "=" * 35)
        print(f"  Pipeline:      ${kpi.compute_pipeline_total():,.0f}")
        print(f"  Revenue MTD:   ${kpi.compute_revenue_mtd():,.0f}")
        print(f"  Posts (month):  {kpi.compute_posts_this_month()}")
        print(f"  Tasks (week):  {kpi.compute_tasks_done_this_week()}")
        print("  " + "=" * 35 + "\n")


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    run_command(args)


if __name__ == "__main__":
    main()
