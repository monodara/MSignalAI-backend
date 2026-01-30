import redis
import json
from typing import Any, Dict, Optional, cast
from app.config.settings import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD

redis_kwargs = {
    "host": REDIS_HOST,
    "port": REDIS_PORT,
    "db": REDIS_DB,
    "decode_responses": True
}

if REDIS_PASSWORD:
    redis_kwargs["password"] = REDIS_PASSWORD

redis_client = redis.Redis(**redis_kwargs)

def get_cached_data(key: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves cached data from Redis.
    Parses from JSON string.
    """
    cached_data = redis_client.get(key)
    if cached_data:
        # Explicitly cast cached_data to str to help Pylance
        return json.loads(cast(str, cached_data))
    return None

def set_cached_data(key: str, data: Dict[str, Any], ex: int = 60) -> None:
    """
    Caches data in Redis.
    Serializes to JSON string.
    """
    redis_client.setex(key, ex, json.dumps(data))

def clear_cache(key: str) -> None:
    """
    Deletes a key from the Redis cache.
    """
    redis_client.delete(key)
