import redis
import json
from app.config.settings import REDIS_HOST, REDIS_PORT, REDIS_DB

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

def get_cached_data(key: str):
    cached_data = redis_client.get(key)
    if cached_data:
        return json.loads(cached_data)
    return None

def set_cached_data(key: str, data: dict, ex: int = 60):
    redis_client.setex(key, ex, json.dumps(data))

def clear_cache(key: str):
    redis_client.delete(key)