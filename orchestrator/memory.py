"""
memory.py — Agent Memory Interface
=====================================
All memory operations for agentsHQ go through this module.

Two memory stores:
  1. Qdrant (vector DB) — semantic similarity search across past tasks
  2. PostgreSQL — structured archive of every execution

Agents query memory at the start of tasks to surface
relevant past work. This is how the system learns over time.
"""

import os
import json
import logging
import uuid
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Qdrant connection
QDRANT_URL = os.environ.get("QDRANT_URL", "http://agentshq-qdrant-1:6333")
QDRANT_COLLECTION = "agentshq_memory"


def get_qdrant_client():
    """Get a Qdrant client instance."""
    try:
        from qdrant_client import QdrantClient
        return QdrantClient(url=QDRANT_URL)
    except Exception as e:
        logger.warning(f"Qdrant unavailable: {e}")
        return None


def get_embedding(text: str) -> Optional[list]:
    """Generate an embedding for text using OpenRouter."""
    try:
        import openai
        client = openai.OpenAI(
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000]  # truncate to avoid token limits
        )
        return response.data[0].embedding
    except Exception as e:
        logger.warning(f"Embedding failed: {e}")
        return None


def save_to_memory(
    task_request: str,
    task_type: str,
    result_summary: str,
    files_created: list = None,
    execution_time: float = 0.0,
    from_number: str = "unknown"
) -> bool:
    """
    Save a completed task to both Qdrant and PostgreSQL.
    Called by the orchestrator after every successful execution.
    """
    timestamp = datetime.utcnow().isoformat()
    
    # Save to Qdrant (vector memory)
    try:
        client = get_qdrant_client()
        if client:
            embedding = get_embedding(f"{task_request} {result_summary}")
            if embedding:
                from qdrant_client.models import PointStruct
                
                # Ensure collection exists
                try:
                    client.get_collection(QDRANT_COLLECTION)
                except Exception:
                    from qdrant_client.models import VectorParams, Distance
                    client.create_collection(
                        collection_name=QDRANT_COLLECTION,
                        vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
                    )
                
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "task_request": task_request,
                        "task_type": task_type,
                        "summary": result_summary[:500],
                        "files_created": files_created or [],
                        "execution_time": execution_time,
                        "from_number": from_number,
                        "timestamp": timestamp,
                        "date": timestamp[:10]
                    }
                )
                client.upsert(collection_name=QDRANT_COLLECTION, points=[point])
                logger.info("Task saved to Qdrant memory")
    except Exception as e:
        logger.warning(f"Qdrant save failed (non-fatal): {e}")

    # Save to PostgreSQL (structured archive)
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "orc-postgres"),
            database=os.environ.get("POSTGRES_DB", "postgres"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", ""),
            port=5432
        )
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO conversation_archive
            (from_number, direction, message_text, task_type, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            from_number,
            "outbound",
            result_summary[:2000],
            task_type,
            timestamp
        ))
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Task saved to PostgreSQL archive")
    except Exception as e:
        logger.warning(f"PostgreSQL save failed (non-fatal): {e}")

    return True


def query_memory(query: str, top_k: int = 3, collection: str = None) -> list:
    """
    Query Qdrant for semantically similar past tasks.
    Returns top_k most relevant past tasks.
    Pass collection="agentshq_learnings" to query the learnings store.
    """
    _collection = collection or QDRANT_COLLECTION
    try:
        client = get_qdrant_client()
        if not client:
            return []

        embedding = get_embedding(query)
        if not embedding:
            return []

        results = client.search(
            collection_name=_collection,
            query_vector=embedding,
            limit=top_k,
            score_threshold=0.7
        )

        return [r.payload for r in results]

    except Exception as e:
        logger.warning(f"Memory query failed (non-fatal): {e}")
        return []


def get_conversation_history(session_id: str, limit: int = 10) -> list:
    """
    Retrieve recent conversation history for a Telegram/General session.
    Used by n8n to maintain context across messages.
    """
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "orc-postgres"),
            database=os.environ.get("POSTGRES_DB", "postgres"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", ""),
            port=5432
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT role, content, created_at FROM agent_conversation_history
            WHERE session_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (session_id, limit))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        return [
            {"role": r[0], "content": r[1], "timestamp": str(r[2])}
            for r in reversed(rows)
        ]
    except Exception as e:
        logger.warning(f"History retrieval failed: {e}")
        return []


def save_conversation_turn(session_id: str, role: str, content: str) -> bool:
    """
    Save a single conversation turn (user message or assistant reply) to
    conversation_archive. Used to build session context for follow-up tasks.
    """
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "orc-postgres"),
            database=os.environ.get("POSTGRES_DB", "postgres"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", ""),
            port=5432
        )
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO agent_conversation_history (session_id, role, content, created_at)
            VALUES (%s, %s, %s, %s)
        """, (
            session_id,
            role,
            content[:2000],  # cap to avoid bloating history
            datetime.utcnow().isoformat()
        ))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        logger.warning(f"save_conversation_turn failed (non-fatal): {e}")
        return False


def _pg_conn():
    """Return a psycopg2 connection using env vars."""
    import psycopg2
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "orc-postgres"),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        port=5432
    )


def save_overflow(session_id: str, full_output: str, delivered_chars: int, task_type: str = "") -> bool:
    """Store the full output for a session so 'more' can retrieve the next chunk."""
    try:
        conn = _pg_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO pending_overflow (session_id, full_output, delivered_chars, task_type, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (session_id) DO UPDATE
            SET full_output = EXCLUDED.full_output,
                delivered_chars = EXCLUDED.delivered_chars,
                task_type = EXCLUDED.task_type,
                created_at = EXCLUDED.created_at
        """, (session_id, full_output, delivered_chars, task_type, datetime.utcnow().isoformat()))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        logger.warning(f"save_overflow failed (non-fatal): {e}")
        return False


def get_next_chunk(session_id: str, chunk_size: int = 3700) -> dict:
    """
    Retrieve the next unsent chunk for a session.
    Returns: {found: bool, chunk: str, has_more: bool}
    Advances the delivered_chars pointer after retrieval.
    """
    try:
        conn = _pg_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT full_output, delivered_chars, task_type
            FROM pending_overflow WHERE session_id = %s
        """, (session_id,))
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return {"found": False, "chunk": "", "has_more": False}

        full_output, delivered_chars, task_type = row
        remaining = full_output[delivered_chars:]

        if not remaining.strip():
            # Nothing left — clean up
            cur.execute("DELETE FROM pending_overflow WHERE session_id = %s", (session_id,))
            conn.commit()
            cur.close()
            conn.close()
            return {"found": True, "chunk": "[No more content — that was everything.]", "has_more": False}

        chunk = remaining[:chunk_size]
        new_delivered = delivered_chars + len(chunk)
        has_more = new_delivered < len(full_output)

        if has_more:
            cur.execute("""
                UPDATE pending_overflow SET delivered_chars = %s WHERE session_id = %s
            """, (new_delivered, session_id))
        else:
            cur.execute("DELETE FROM pending_overflow WHERE session_id = %s", (session_id,))

        conn.commit()
        cur.close()
        conn.close()
        return {"found": True, "chunk": chunk, "has_more": has_more}
    except Exception as e:
        logger.warning(f"get_next_chunk failed (non-fatal): {e}")
        return {"found": False, "chunk": "", "has_more": False}


# ── Job Queue ─────────────────────────────────────────────────

def create_job(job_id: str, session_key: str, from_number: str, task: str) -> bool:
    """Insert a new job record with status='pending'."""
    try:
        conn = _pg_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO job_queue (job_id, session_key, from_number, task, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, 'pending', %s, %s)
        """, (job_id, session_key, from_number, task,
              datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        logger.warning(f"create_job failed: {e}")
        return False


def update_job(job_id: str, status: str, result: str = None,
               task_type: str = None, files_created: list = None,
               execution_time: float = None, error: str = None) -> bool:
    """Update a job record with its outcome."""
    try:
        conn = _pg_conn()
        cur = conn.cursor()
        cur.execute("""
            UPDATE job_queue SET
                status = %s,
                result = %s,
                task_type = %s,
                files_created = %s,
                execution_time = %s,
                error = %s,
                updated_at = %s
            WHERE job_id = %s
        """, (status, result, task_type,
              json.dumps(files_created or []),
              execution_time, error,
              datetime.utcnow().isoformat(), job_id))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        logger.warning(f"update_job failed: {e}")
        return False


def get_job(job_id: str) -> dict:
    """Retrieve a job record by ID."""
    try:
        conn = _pg_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT job_id, status, task_type, result, files_created,
                   execution_time, error, created_at, updated_at
            FROM job_queue WHERE job_id = %s
        """, (job_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return {}
        return {
            "job_id":         row[0],
            "status":         row[1],
            "task_type":      row[2],
            "result":         row[3],
            "files_created":  row[4] if isinstance(row[4], list) else [],
            "execution_time": row[5],
            "error":          row[6],
            "created_at":     str(row[7]),
            "updated_at":     str(row[8]),
        }
    except Exception as e:
        logger.warning(f"get_job failed: {e}")
        return {}
