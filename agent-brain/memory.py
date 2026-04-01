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
            host=os.environ.get("POSTGRES_HOST", "agentshq-postgres-1"),
            database=os.environ.get("POSTGRES_DB", "postgres"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", ""),
            port=5432
        )
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO conversation_archive
            (session_id, role, content, created_at, metadata)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            from_number,
            "agent",
            result_summary,
            timestamp,
            json.dumps({
                "task_type": task_type,
                "files": files_created or [],
                "execution_time": execution_time,
                "original_request": task_request
            })
        ))
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Task saved to PostgreSQL archive")
    except Exception as e:
        logger.warning(f"PostgreSQL save failed (non-fatal): {e}")

    return True


def query_memory(query: str, top_k: int = 3) -> list:
    """
    Query Qdrant for semantically similar past tasks.
    Returns top_k most relevant past tasks.
    """
    try:
        client = get_qdrant_client()
        if not client:
            return []
        
        embedding = get_embedding(query)
        if not embedding:
            return []
        
        results = client.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=embedding,
            limit=top_k,
            score_threshold=0.7  # only return genuinely similar results
        )
        
        return [r.payload for r in results]
        
    except Exception as e:
        logger.warning(f"Memory query failed (non-fatal): {e}")
        return []


def get_conversation_history(session_id: str, limit: int = 10) -> list:
    """
    Retrieve recent conversation history for a Telegram session.
    Used by n8n to maintain context across messages.
    """
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "agentshq-postgres-1"),
            database=os.environ.get("POSTGRES_DB", "postgres"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", ""),
            port=5432
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT role, content, created_at FROM conversation_archive
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
