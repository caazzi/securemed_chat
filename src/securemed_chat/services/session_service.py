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
    """Creates a new session and returns the session ID using Redis Hashes."""
    session_id = str(uuid.uuid4())
    client = get_redis()
    
    # Serialize complex types (lists/dicts) to JSON strings within the hash fields
    hash_data = {
        k: (json.dumps(v) if isinstance(v, (list, dict)) else v)
        for k, v in data.items()
    }
    
    key = f"session:{session_id}"
    await client.hset(key, mapping=hash_data)
    await client.expire(key, SESSION_TTL)
    
    logging.info(f"Created new session {session_id} as Hash")
    return session_id

async def get_session(session_id: str) -> Dict[str, Any]:
    """Retrieves session data by ID. Returns empty dict if not found."""
    if not session_id:
        return {}
    
    client = get_redis()
    key = f"session:{session_id}"
    raw_data = await client.hgetall(key)
    
    if raw_data:
        # Refresh TTL on access
        await client.expire(key, SESSION_TTL)
        
        # Deserialize complex types
        result = {}
        for k, v in raw_data.items():
            try:
                # Attempt to parse as JSON; if it fails or is not a list/dict, keep as string
                parsed = json.loads(v)
                if isinstance(parsed, (list, dict)):
                    result[k] = parsed
                else:
                    result[k] = v
            except (json.JSONDecodeError, TypeError):
                result[k] = v
        return result
    return {}

async def update_session(session_id: str, new_data: Dict[str, Any]) -> None:
    """Updates specific fields in a session without a full re-fetch (Redundant GET removed)."""
    if not session_id or not new_data:
        return
        
    client = get_redis()
    key = f"session:{session_id}"
    
    # Serialize complex types for partial update
    hash_data = {
        k: (json.dumps(v) if isinstance(v, (list, dict)) else v)
        for k, v in new_data.items()
    }
    
    await client.hset(key, mapping=hash_data)
    await client.expire(key, SESSION_TTL)
    logging.debug(f"Updated session {session_id} fields: {list(new_data.keys())}")

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
