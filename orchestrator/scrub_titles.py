"""Strip ' -- LinkedIn' / ' -- X' / em dashes from Content Board titles."""
import os
import re
import sys

sys.path.insert(0, "/app")
from skills.forge_cli.notion_client import NotionClient

DB = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")
n = NotionClient(secret=os.environ["NOTION_SECRET"])

pages = n.query_database(DB, filter_obj=None)
fixed = 0
for p in pages:
    props = p.get("properties", {})
    tp = props.get("Title", {}).get("title", [])
    if not tp:
        continue
    old = "".join(x.get("plain_text", "") for x in tp)
    new = old
    for tag in [" -- LinkedIn", " -- X", " -- LinkedIn [X]", " [X]"]:
        new = new.replace(tag, "")
    new = new.replace("--", ".").replace("—", ".").replace("–", ".")
    new = re.sub(r"\s+\.", ".", new).strip()
    if new != old:
        n.update_page(p["id"], {"Title": {"title": [{"text": {"content": new[:200]}}]}})
        print(f"{p['id']}: {old!r} -> {new!r}")
        fixed += 1

print(f"\nFixed {fixed} titles")
