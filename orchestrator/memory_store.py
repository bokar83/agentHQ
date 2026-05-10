"""
memory_store.py - Read/write interface for the agentsHQ memory table.

All write paths call write(model) where model is one of the 8 types
from memory_models.py. All query paths call query_text() or query_filter().

Connection pattern matches council.py: direct psycopg2 connect via env vars.
All functions are non-fatal on DB failure — they log and return None/[].
"""
from __future__ import annotations

import logging
import os
import re
from typing import Optional

logger = logging.getLogger("agentsHQ.memory_store")

_QUESTION_PREFIXES = re.compile(
    r"^\s*(tell me (about|what you know about)|what (do i|do we) know about|"
    r"show me|find|give me|look up|search for|what is|who is|"
    r"what are my|what are|remind me|remember)\s+",
    re.IGNORECASE,
)


def _clean_query(text: str) -> str:
    """Strip conversational prefixes before passing to tsvector."""
    return _QUESTION_PREFIXES.sub("", text).strip()


def _get_conn():
    import psycopg2
    import psycopg2.extras
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "agentshq-postgres-1"),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def write(model) -> Optional[int]:
    """
    Insert one memory row. model must be a _MemoryBase instance.
    Returns new row id, or None on failure (non-fatal).
    Raises TypeError if model is not a _MemoryBase instance.
    """
    from orchestrator.memory_models import _MemoryBase
    if not isinstance(model, _MemoryBase):
        raise TypeError(
            f"write() requires a memory_models instance, got {type(model)}"
        )
    row = model.to_db_row()
    sql = """
        INSERT INTO memory
            (source, category, title, content, tags, entity_ref,
             external_id, agent_id, pipeline, relevance_boost, expires_at)
        VALUES
            (%(source)s, %(category)s, %(title)s, %(content)s, %(tags)s,
             %(entity_ref)s, %(external_id)s, %(agent_id)s, %(pipeline)s,
             %(relevance_boost)s, %(expires_at)s)
        ON CONFLICT (source, external_id) WHERE external_id IS NOT NULL
            DO UPDATE SET
                content = EXCLUDED.content,
                updated_at = NOW()
        RETURNING id
    """
    conn = None
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(sql, row)
        result = cur.fetchone()
        conn.commit()
        row_id = result["id"] if result else None
        logger.info(f"memory_store: wrote {row['category']} id={row_id}")
        return row_id
    except Exception as e:
        logger.warning(f"memory_store.write failed (non-fatal): {e}")
        return None
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def query_text(
    text: str,
    limit: int = 20,
    pipeline: Optional[str] = None,
    category: Optional[str] = None,
) -> list[dict]:
    """
    Full-text tsvector search. Returns list of row dicts ordered by
    ts_rank * relevance_boost DESC. Returns [] on any failure (non-fatal).
    Strips conversational prefixes before searching.
    """
    clean = _clean_query(text)
    conditions = ["content_tsv @@ websearch_to_tsquery('english', %(text)s)"]
    params: dict = {"text": clean, "limit": limit}
    if pipeline:
        conditions.append("pipeline = %(pipeline)s")
        params["pipeline"] = pipeline
    if category:
        conditions.append("category = %(category)s")
        params["category"] = category
    where = " AND ".join(conditions)
    sql = f"""
        SELECT id, category, title, content, entity_ref, pipeline,
               source, created_at
        FROM memory
        WHERE {where}
        ORDER BY ts_rank(content_tsv, websearch_to_tsquery('english', %(text)s))
                 * relevance_boost DESC
        LIMIT %(limit)s
    """
    conn = None
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.warning(f"memory_store.query_text failed (non-fatal): {e}")
        return []
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def query_filter(
    category: Optional[str] = None,
    pipeline: Optional[str] = None,
    entity_ref: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """
    Structured filter query. Returns list of row dicts. Returns [] on failure.
    """
    conditions = ["1=1"]
    params: dict = {"limit": limit}
    if category:
        conditions.append("category = %(category)s")
        params["category"] = category
    if pipeline:
        conditions.append("pipeline = %(pipeline)s")
        params["pipeline"] = pipeline
    if entity_ref:
        conditions.append("entity_ref = %(entity_ref)s")
        params["entity_ref"] = entity_ref
    where = " AND ".join(conditions)
    sql = f"""
        SELECT id, category, title, content, entity_ref, pipeline,
               source, created_at
        FROM memory
        WHERE {where}
        ORDER BY relevance_boost DESC, created_at DESC
        LIMIT %(limit)s
    """
    conn = None
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.warning(f"memory_store.query_filter failed (non-fatal): {e}")
        return []
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def load_hard_rules() -> list[dict]:
    """
    Return ALL hard_rule rows regardless of age.
    Used at session start for context injection.
    Always-load: hard rules never expire.
    """
    return query_filter(category="hard_rule", limit=100)
