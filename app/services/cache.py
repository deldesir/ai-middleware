import redis.asyncio as redis
import os
import time

# Configuration
VALKEY_URL = os.getenv("VALKEY_URL", "redis://127.0.0.1:6379/1") # DB 1 (RapidPro usually uses 0/1, let's use 2 to be safe? Or 1 if unused. RapidPro uses 1 for cache usually. Let's use 5 for AI safety)
VALKEY_URL = os.getenv("VALKEY_URL", "redis://127.0.0.1:6379/5") 

pool = redis.ConnectionPool.from_url(VALKEY_URL)

async def get_redis():
    return redis.Redis(connection_pool=pool)

async def check_health():
    try:
        r = await get_redis()
        return await r.ping()
    except Exception:
        return False

async def mark_key_failure(api_key: str, cooldown_seconds: int):
    """
    Marks an API key as failed for a specific duration.
    """
    r = await get_redis()
    # We store the 'ready_at' timestamp
    ready_at = time.time() + cooldown_seconds
    await r.setex(f"key_fail:{api_key[-6:]}", cooldown_seconds, str(ready_at))
    # Note: We use last 6 chars as ID to avoid storing full secret. 
    # Actually, we need unique ID. Let's hash it or assume last 6 is unique enough for this pool.
    # For safety, let's hash it.
    import hashlib
    key_hash = hashlib.md5(api_key.encode()).hexdigest()
    await r.setex(f"key_fail:{key_hash}", cooldown_seconds, str(ready_at))

async def get_key_readiness(api_key: str) -> float:
    """
    Returns the timestamp when the key will be ready. 
    0 if ready now.
    """
    r = await get_redis()
    import hashlib
    key_hash = hashlib.md5(api_key.encode()).hexdigest()
    
    val = await r.get(f"key_fail:{key_hash}")
    if val:
        return float(val)
    return 0.0
