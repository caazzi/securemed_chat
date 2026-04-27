import pytest
import httpx
from securemed_chat.main import app
from securemed_chat.core.config import SECUREMED_API_KEY
import redis.asyncio as redis
import os

@pytest.mark.asyncio
async def test_rate_limit_session_init():
    headers = {"X-API-KEY": SECUREMED_API_KEY}
    payload = {
        "age_bracket": "26-35",
        "sex": "Female",
        "lang": "en",
        "specialist": "Cardiology",
        "chief_complaint": "Chest pain",
        "duration": "2 days",
        "smoking": "No",
        "alcohol": "No"
    }

    # Clear redis for testing
    r = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
    await r.flushdb()

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        # First and second requests should succeed
        resp1 = await client.post("/api/session/init", json=payload, headers=headers)
        assert resp1.status_code == 200
        
        resp2 = await client.post("/api/session/init", json=payload, headers=headers)
        assert resp2.status_code == 200

        # Third request should be rate limited (limit=2)
        resp3 = await client.post("/api/session/init", json=payload, headers=headers)
        assert resp3.status_code == 429
        assert "Too many session requests" in resp3.json()["detail"]

    await r.aclose()

@pytest.mark.asyncio
async def test_session_quota():
    headers = {"X-API-KEY": SECUREMED_API_KEY}
    payload = {
        "age_bracket": "26-35",
        "sex": "Female",
        "lang": "en",
        "specialist": "Cardiology",
        "chief_complaint": "Valid complaint",
        "duration": "1 day",
        "smoking": "No",
        "alcohol": "No"
    }

    # Clear redis
    r = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
    await r.flushdb()

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        # Create 5 sessions (limit=5)
        for i in range(5):
            resp = await client.post("/api/session/init", json=payload, headers=headers)
            if resp.status_code == 429 and "Too many session requests" in resp.json()["detail"]:
                # Manually clear the rate limit key to test quota
                await r.delete("rate_limit:init:127.0.0.1")
                resp = await client.post("/api/session/init", json=payload, headers=headers)
            
            assert resp.status_code == 200

        # 6th session should hit quota
        await r.delete("rate_limit:init:127.0.0.1")
        resp6 = await client.post("/api/session/init", json=payload, headers=headers)
        assert resp6.status_code == 429
        assert "Daily session limit reached" in resp6.json()["detail"]

    await r.aclose()
