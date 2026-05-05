"""
spend_snapshot.py - Daily provider spend snapshot.

Fires once per day at 23:55 MT via heartbeat. Pulls live figures from
OpenRouter's auth/key + credits endpoints and upserts one row per day
into provider_billing. This gives us true historical spend so the
dashboard can compare this week vs last week, this month vs last month, YTD.

Table schema (created on first run if missing):
    provider_billing(
        id           SERIAL PRIMARY KEY,
        provider     TEXT NOT NULL,          -- 'openrouter'
        day          DATE NOT NULL,          -- MT date
        usd_today    NUMERIC(10,6),          -- rolling daily from provider
        usd_week     NUMERIC(10,6),          -- rolling weekly
        usd_month    NUMERIC(10,6),          -- rolling monthly
        usd_lifetime NUMERIC(10,6),          -- total_usage all time
        balance_usd  NUMERIC(10,6),          -- credits remaining
        raw_json     TEXT,                   -- full API response for audit
        ts           TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE(provider, day)               -- upsert key
    )
"""
from __future__ import annotations

import json
import logging
import os
import urllib.request
from datetime import date, datetime, timezone

logger = logging.getLogger("agentsHQ.spend_snapshot")

PROVIDER = "openrouter"
MONTHLY_BUDGET_USD = 60.0


def _ensure_table(cur) -> None:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS provider_billing (
            id           SERIAL PRIMARY KEY,
            provider     TEXT NOT NULL,
            day          DATE NOT NULL,
            usd_today    NUMERIC(10,6),
            usd_week     NUMERIC(10,6),
            usd_month    NUMERIC(10,6),
            usd_lifetime NUMERIC(10,6),
            balance_usd  NUMERIC(10,6),
            raw_json     TEXT,
            ts           TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(provider, day)
        )
    """)


def _fetch_openrouter() -> dict:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")

    def _get(url):
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())

    key_data = _get("https://openrouter.ai/api/v1/auth/key").get("data", {})
    credit_data = _get("https://openrouter.ai/api/v1/credits").get("data", {})

    total_credits = float(credit_data.get("total_credits", 0) or 0)
    total_usage = float(credit_data.get("total_usage", 0) or 0)

    return {
        "usd_today":    round(float(key_data.get("usage_daily",   0) or 0), 6),
        "usd_week":     round(float(key_data.get("usage_weekly",  0) or 0), 6),
        "usd_month":    round(float(key_data.get("usage_monthly", 0) or 0), 6),
        "usd_lifetime": round(total_usage, 6),
        "balance_usd":  round(total_credits - total_usage, 6),
        "raw_key":      key_data,
        "raw_credits":  credit_data,
    }


def take_snapshot() -> dict:
    """
    Pull live OpenRouter figures and upsert into provider_billing.
    Returns the row dict. Non-fatal on DB errors (logs + returns data anyway).
    """
    try:
        data = _fetch_openrouter()
    except Exception as e:
        logger.error(f"spend_snapshot: fetch failed: {e}")
        return {}

    today_mt = datetime.now(tz=timezone.utc).astimezone(
        __import__("zoneinfo", fromlist=["ZoneInfo"]).ZoneInfo("America/Denver")
    ).date()

    raw = json.dumps({"key": data["raw_key"], "credits": data["raw_credits"]})

    try:
        from memory import _pg_conn
        conn = _pg_conn()
        try:
            cur = conn.cursor()
            _ensure_table(cur)
            cur.execute("""
                INSERT INTO provider_billing
                    (provider, day, usd_today, usd_week, usd_month, usd_lifetime, balance_usd, raw_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (provider, day) DO UPDATE SET
                    usd_today    = EXCLUDED.usd_today,
                    usd_week     = EXCLUDED.usd_week,
                    usd_month    = EXCLUDED.usd_month,
                    usd_lifetime = EXCLUDED.usd_lifetime,
                    balance_usd  = EXCLUDED.balance_usd,
                    raw_json     = EXCLUDED.raw_json,
                    ts           = NOW()
            """, (
                PROVIDER, today_mt,
                data["usd_today"], data["usd_week"], data["usd_month"],
                data["usd_lifetime"], data["balance_usd"], raw,
            ))
            conn.commit()
            cur.close()
            logger.info(
                f"spend_snapshot: saved {today_mt} OR today=${data['usd_today']:.4f} "
                f"week=${data['usd_week']:.4f} month=${data['usd_month']:.4f} "
                f"balance=${data['balance_usd']:.2f}"
            )
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"spend_snapshot: DB write failed: {e}")

    return {
        "day": str(today_mt),
        "usd_today": data["usd_today"],
        "usd_week": data["usd_week"],
        "usd_month": data["usd_month"],
        "usd_lifetime": data["usd_lifetime"],
        "balance_usd": data["balance_usd"],
    }


def get_historical(days: int = 90) -> list[dict]:
    """
    Return daily provider_billing rows newest-first for the last N days.
    Used by get_spend() for week-over-week / month-over-month comparisons.
    """
    try:
        from memory import _pg_conn
        conn = _pg_conn()
        try:
            cur = conn.cursor()
            _ensure_table(cur)
            cur.execute("""
                SELECT day, usd_today, usd_week, usd_month, usd_lifetime, balance_usd
                  FROM provider_billing
                 WHERE provider = %s
                   AND day >= CURRENT_DATE - %s
                 ORDER BY day DESC
            """, (PROVIDER, days))
            rows = cur.fetchall()
            cur.close()
            return [
                {
                    "day": str(r[0]),
                    "usd_today":    float(r[1] or 0),
                    "usd_week":     float(r[2] or 0),
                    "usd_month":    float(r[3] or 0),
                    "usd_lifetime": float(r[4] or 0),
                    "balance_usd":  float(r[5] or 0),
                }
                for r in rows
            ]
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"get_historical: {e}")
        return []


def _fetch_elevenlabs_mtd() -> float:
    """Sum cost_ledger elevenlabs_tts rows for current calendar month."""
    try:
        from memory import _pg_conn
        conn = _pg_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT COALESCE(SUM(amount_usd), 0)
                  FROM cost_ledger
                 WHERE tool = 'elevenlabs_tts'
                   AND date >= date_trunc('month', CURRENT_DATE)::date
                """
            )
            val = cur.fetchone()[0]
            cur.close()
            return round(float(val), 4)
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"spend_snapshot: elevenlabs MTD fetch failed: {e}")
        return 0.0


def spend_snapshot_tick() -> None:
    """Heartbeat callback: take snapshot and send Telegram summary."""
    result = take_snapshot()
    if not result:
        return
    try:
        from notifier import send_message
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        if chat_id:
            el_mtd = _fetch_elevenlabs_mtd()
            el_line = f"ElevenLabs MTD: ${el_mtd:.4f}\n" if el_mtd > 0 else ""
            send_message(chat_id, (
                f"SPEND SNAPSHOT ({result['day']})\n"
                f"Today:    ${result['usd_today']:.2f}\n"
                f"Week:     ${result['usd_week']:.2f}\n"
                f"Month:    ${result['usd_month']:.2f}\n"
                f"Lifetime: ${result['usd_lifetime']:.2f}\n"
                f"Balance:  ${result['balance_usd']:.2f}\n"
                f"{el_line}"
            ))
    except Exception as e:
        logger.warning(f"spend_snapshot: Telegram notify failed: {e}")
