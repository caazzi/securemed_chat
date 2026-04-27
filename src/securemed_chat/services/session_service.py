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

async def check_rate_limit(ip: str, limit: int = 10, window: int = 60) -> bool:
    """
    Checks if the given IP has exceeded the rate limit.
    limit: max requests
    window: time window in seconds
    """
    client = get_redis()
    key = f"rate_limit:{ip}"
    
    # Increment and set TTL if new
    count = await client.incr(key)
    if count == 1:
        await client.expire(key, window)
    
    return count <= limit

async def check_session_quota(ip: str, limit: int = 5) -> bool:
    """
    Checks if the given IP has exceeded the daily session quota.
    limit: max sessions per 24h
    """
    client = get_redis()
    key = f"session_quota:{ip}"
    
    count = await client.get(key)
    if count and int(count) >= limit:
        return False
        
    return True

async def increment_session_quota(ip: str, window: int = 86400) -> None:
    """Increments the session quota count for an IP."""
    client = get_redis()
    key = f"session_quota:{ip}"
    count = await client.incr(key)
    if count == 1:
        await client.expire(key, window)
