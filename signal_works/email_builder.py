"""
signal_works/email_builder.py
Builds personalized cold emails for Signal Works leads.
Outputs filled email strings and a CSV queue file ready for Gmail.
"""
import os
import csv
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

TEMPLATE_PATH = Path(__file__).parent / "templates" / "cold_email.txt"
CALENDLY_URL = os.environ.get("SIGNAL_WORKS_CALENDLY", "https://calendly.com/boubacarbarry/signal-works")
SENDER_NAME = os.environ.get("SIGNAL_WORKS_SENDER", "Boubacar Barry")

DEMO_URLS = {
    "pediatric dentist": os.environ.get("SIGNAL_WORKS_DEMO_DENTAL", "https://signal-works-demo-dental.vercel.app"),
    "dentist": os.environ.get("SIGNAL_WORKS_DEMO_DENTAL", "https://signal-works-demo-dental.vercel.app"),
    "roofer": os.environ.get("SIGNAL_WORKS_DEMO_ROOFING", "https://signal-works-demo-roofing.vercel.app"),
    "roofing": os.environ.get("SIGNAL_WORKS_DEMO_ROOFING", "https://signal-works-demo-roofing.vercel.app"),
}
DEFAULT_DEMO_URL = "https://signal-works-demo-dental.vercel.app"
LOOM_URL = os.environ.get("SIGNAL_WORKS_LOOM", "https://loom.com/share/REPLACE_WITH_REAL_LOOM")


def _get_competitor_example(niche: str, city: str) -> str:
    return f"another {niche} in {city}"


def build_email(lead: dict) -> str:
    """Fill cold email template for a single lead. Returns complete email with no unfilled placeholders."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    quick_wins_text = "\n".join(
        f"  {i+1}. {win}" for i, win in enumerate(lead.get("ai_quick_wins", ["Optimize your AI presence"]))
    )
    niche = lead.get("niche", "local business")
    demo_url = lead.get("demo_url") or DEMO_URLS.get(niche.lower(), DEFAULT_DEMO_URL)
    loom_url = lead.get("loom_url") or LOOM_URL
    owner_name = lead.get("owner_name") or "there"

    return template.format(
        business_name=lead.get("name", "your business"),
        owner_name=owner_name,
        ai_score=lead.get("ai_score", 0),
        niche=niche,
        city=lead.get("city", "your city"),
        competitor_example=_get_competitor_example(niche, lead.get("city", "")),
        demo_url=demo_url,
        loom_url=loom_url,
        quick_wins=quick_wins_text,
        calendly_url=CALENDLY_URL,
        sender_name=SENDER_NAME,
    )


def build_email_queue(leads: list[dict], output_csv: str = "signal_works/email_queue.csv") -> str:
    """Build a CSV of personalized emails ready for Gmail. Returns path to CSV."""
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for lead in leads:
        if not lead.get("email"):
            logger.warning(f"Skipping {lead['name']} -- no email address")
            continue
        body = build_email(lead)
        lines = body.strip().split("\n")
        subject = lines[0].replace("Subject: ", "").strip()
        body_only = "\n".join(lines[2:]).strip()
        rows.append({
            "to_email": lead["email"],
            "owner_name": lead.get("owner_name", ""),
            "business_name": lead.get("name", ""),
            "subject": subject,
            "body": body_only,
            "ai_score": lead.get("ai_score", 0),
            "niche": lead.get("niche", ""),
            "city": lead.get("city", ""),
        })

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["to_email", "owner_name", "business_name", "subject", "body", "ai_score", "niche", "city"])
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Email queue written: {len(rows)} emails -> {output_csv}")
    return output_csv
