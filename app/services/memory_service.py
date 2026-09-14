import os
import json
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Graceful Redis connection with local in-memory fallback
try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=1)
    redis_client.ping()
    USE_REDIS = True
except Exception:
    USE_REDIS = False
    LOCAL_MEMORY_CACHE = {}

def get_conversation_history(user_id: str, limit: int = 5) -> list:
    """Retrieve recent multi-turn conversation messages."""
    if USE_REDIS:
        try:
            raw_history = redis_client.lrange(f"session:{user_id}", -limit, -1)
            return [json.loads(item) for item in raw_history]
        except Exception:
            pass
    return LOCAL_MEMORY_CACHE.get(user_id, [])[-limit:]

def add_message_to_memory(user_id: str, role: str, content: str):
    """Append query or resolution message to conversation memory."""
    payload = json.dumps({"role": role, "content": content})
    if USE_REDIS:
        try:
            key = f"session:{user_id}"
            redis_client.rpush(key, payload)
            redis_client.expire(key, 86400)  # 24-hour TTL
            return
        except Exception:
            pass
            
    if user_id not in LOCAL_MEMORY_CACHE:
        LOCAL_MEMORY_CACHE[user_id] = []
    LOCAL_MEMORY_CACHE[user_id].append({"role": role, "content": content})