#!/usr/bin/env python3
"""Bulk-create Gumroad products from a manifest JSON.

Reads docs/products/gumroad-manifest-2026-05-16.json (built by listing-draft agent).
Creates each product via Gumroad v2 API. Uploads deliverable file from
docs/products/<slug>/deliverable/. Logs success/failure with short_url per SKU.

Env required (read from container): GUMROAD_ACCESS_TOKEN, GUMROAD_USERNAME

Usage:
    docker exec orc-crewai python3 /app/scripts/gumroad_bulk_create.py --dry-run
    docker exec orc-crewai python3 /app/scripts/gumroad_bulk_create.py --batch 0:5

Manifest schema (one entry per SKU):
{
  "slug": "start-ai-24h",
  "name": "Start AI Within 24 Hours",
  "price_cents": 2700,
  "description_md": "...",
  "tags": ["ai", "starter"],
  "deliverable_path": "docs/products/start-ai-24h/deliverable/start-ai-24h-v1.pdf",
  "custom_permalink": "start-ai-24h",
  "is_tiered_membership": false,
  "preview_url": "https://products-plum-seven.vercel.app/start-ai-24h/"
}
"""
import argparse
import json
import os
import sys
from pathlib import Path

import requests

GUMROAD_API = "https://api.gumroad.com/v2"


def _token() -> str:
    tok = os.environ.get("GUMROAD_ACCESS_TOKEN", "").strip()
    if not tok:
        sys.exit("GUMROAD_ACCESS_TOKEN missing from env")
    return tok


def list_existing() -> dict[str, dict]:
    r = requests.get(
        f"{GUMROAD_API}/products",
        params={"access_token": _token()},
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        sys.exit(f"list failed: {data}")
    return {p.get("name", "").lower(): p for p in data.get("products", [])}


def create_product(entry: dict, dry_run: bool = False) -> dict:
    """Create one Gumroad product."""
    payload = {
        "access_token": _token(),
        "name": entry["name"],
        "price": entry["price_cents"],
        "description": entry["description_md"],
        "tags": ",".join(entry.get("tags", [])),
    }
    if entry.get("custom_permalink"):
        payload["custom_permalink"] = entry["custom_permalink"]
    if entry.get("preview_url"):
        payload["preview_url"] = entry["preview_url"]

    if dry_run:
        return {
            "slug": entry["slug"],
            "status": "DRY",
            "would_create": entry["name"],
            "price_cents": entry["price_cents"],
        }

    r = requests.post(f"{GUMROAD_API}/products", data=payload, timeout=30)
    try:
        d = r.json()
    except Exception:
        return {"slug": entry["slug"], "status": "ERR_JSON", "http": r.status_code, "body": r.text[:300]}

    if not d.get("success"):
        return {"slug": entry["slug"], "status": "ERR_API", "body": d}

    product = d.get("product", {})
    product_id = product.get("id")
    short_url = product.get("short_url")

    deliverable = entry.get("deliverable_path")
    upload_result = None
    if product_id and deliverable:
        upload_result = upload_file(product_id, deliverable)

    return {
        "slug": entry["slug"],
        "status": "OK",
        "product_id": product_id,
        "short_url": short_url,
        "uploaded": upload_result,
    }


def upload_file(product_id: str, deliverable_path: str) -> dict:
    """Upload deliverable file to a Gumroad product."""
    fpath = Path(deliverable_path)
    if not fpath.exists():
        return {"status": "MISSING_FILE", "path": str(fpath)}

    with fpath.open("rb") as fh:
        files = {"file": (fpath.name, fh)}
        data = {"access_token": _token()}
        r = requests.post(
            f"{GUMROAD_API}/products/{product_id}/files",
            data=data,
            files=files,
            timeout=120,
        )
    try:
        d = r.json()
    except Exception:
        return {"status": "ERR_JSON", "http": r.status_code, "body": r.text[:300]}
    if not d.get("success"):
        return {"status": "ERR_UPLOAD", "body": d}
    return {"status": "OK", "file_id": d.get("file", {}).get("id")}


def publish_product(product_id: str) -> dict:
    r = requests.put(
        f"{GUMROAD_API}/products/{product_id}/enable",
        data={"access_token": _token()},
        timeout=20,
    )
    try:
        return r.json()
    except Exception:
        return {"status": "ERR_JSON", "body": r.text[:300]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="/app/docs/products/gumroad-manifest-2026-05-16.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch", default="0:30", help="slice e.g. 0:5")
    parser.add_argument("--publish", action="store_true", help="publish after upload")
    args = parser.parse_args()

    if not Path(args.manifest).exists():
        sys.exit(f"manifest not found: {args.manifest}")

    entries = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    start, end = [int(x) for x in args.batch.split(":")]
    entries = entries[start:end]

    existing = list_existing() if not args.dry_run else {}
    results = []
    for entry in entries:
        name_key = entry["name"].lower()
        if not args.dry_run and name_key in existing:
            results.append({"slug": entry["slug"], "status": "SKIP_EXISTS", "short_url": existing[name_key].get("short_url")})
            continue
        result = create_product(entry, dry_run=args.dry_run)
        if args.publish and result.get("status") == "OK" and result.get("product_id"):
            result["published"] = publish_product(result["product_id"])
        results.append(result)
        print(json.dumps(result, indent=2))

    log_path = Path("/app/agent_outputs/gumroad_bulk_create_log.json")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nLog written: {log_path}")
    print(f"\nSummary: {len([r for r in results if r['status']=='OK'])} OK, {len([r for r in results if r['status'].startswith('ERR')])} ERR, {len([r for r in results if r['status']=='SKIP_EXISTS'])} SKIP")


if __name__ == "__main__":
    main()
