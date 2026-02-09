import time
import json
import hashlib
import asyncio
from typing import Any, Callable, Dict, Optional, Tuple
from functools import wraps

class AsyncTTLCRUCache:
    def __init__(self, maxsize: int = 100, ttl: int = 3600):
        """
        Async Least Recently Used (LRU) cache with Time To Live (TTL).
        
        Args:
            maxsize: Maximum number of items in the cache.
            ttl: Time to live in seconds.
        """
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.maxsize = maxsize
        self.ttl = ttl
        self.lock = asyncio.Lock()

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate a unique key based on args and kwargs."""
        key_parts = [str(arg) for arg in args]
        # Sort kwargs to ensure consistent key generation
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        
        key_str = "|".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    async def get(self, key: str) -> Optional[Any]:
        async with self.lock:
            if key not in self.cache:
                return None
            
            value, timestamp = self.cache[key]
            
            # Check TTL
            if time.time() - timestamp > self.ttl:
                del self.cache[key]
                return None
            
            # Move to end (most recently used)
            self.cache[key] = self.cache.pop(key)
            self.cache[key] = (value, timestamp)
            
            return value

    async def set(self, key: str, value: Any):
        async with self.lock:
            # Evict if full
            if len(self.cache) >= self.maxsize:
                # Remove first item (least recently used)
                self.cache.pop(next(iter(self.cache)))
            
            self.cache[key] = (value, time.time())

# Global cache instance
agent_cache = AsyncTTLCRUCache(maxsize=100, ttl=3600)

def cache_response(ttl: int = 3600):
    """
    Decorator to cache async function responses.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate key from Pydantic models or dicts
            # For AgentRequest, we want to hash the model_dump if present
            key_args = []
            for arg in args:
                if hasattr(arg, "model_dump_json"):
                    key_args.append(arg.model_dump_json())
                elif hasattr(arg, "model_dump"):
                    key_args.append(json.dumps(arg.model_dump(), sort_keys=True))
                else:
                    key_args.append(str(arg))
            
            key = agent_cache._generate_key(*key_args, **kwargs)
            
            # Check cache
            cached_result = await agent_cache.get(key)
            if cached_result:
                print(f"⚡ Cache hit for {func.__name__} (Key: {key[:8]}...)")
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await agent_cache.set(key, result)
            print(f"💾 Cached result for {func.__name__} (Key: {key[:8]}...)")
            
            return result
        return wrapper
    return decorator
