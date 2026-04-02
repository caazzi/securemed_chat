import os
import json
import uuid
import logging
from typing import Dict, Any
import redis.asyncio as redis

# 30 minutes in seconds
SESSION_TTL = 30 * 60

# Redis connection setup
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Lazy-loaded connection pool
_redis_pool = None

def get_redis() -> redis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_pool

async def create_session(data: Dict[str, Any]) -> str:
    """Creates a new session and returns the session ID."""
    session_id = str(uuid.uuid4())
    client = get_redis()
    await client.setex(
        f"session:{session_id}",
        SESSION_TTL,
        json.dumps(data)
    )
    logging.info(f"Created new session {session_id}")
    return session_id

async def get_session(session_id: str) -> Dict[str, Any]:
    """Retrieves session data by ID. Returns empty dict if not found."""
    if not session_id:
        return {}
    
    client = get_redis()
    data = await client.get(f"session:{session_id}")
    if data:
        # Refresh TTL on access
        await client.expire(f"session:{session_id}", SESSION_TTL)
        return json.loads(data)
    return {}

async def update_session(session_id: str, new_data: Dict[str, Any]) -> None:
    """Merges new data into an existing session."""
    if not session_id:
        return
        
    client = get_redis()
    current_data = await get_session(session_id)
    current_data.update(new_data)
    
    await client.setex(
        f"session:{session_id}",
        SESSION_TTL,
        json.dumps(current_data)
    )
