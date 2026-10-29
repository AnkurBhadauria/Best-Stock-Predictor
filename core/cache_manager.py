"""
Intelligent In-Memory and Disk Cache Manager.
Prevents API rate limiting and provides instant sub-second responses.
"""

import time
import json
import os
from typing import Any, Optional

class CacheManager:
    def __init__(self, cache_dir: str = ".cache"):
        self._memory_cache = {}
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def get(self, key: str) -> Optional[Any]:
        current_time = time.time()
        
        # Check memory cache first
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if current_time < entry["expires_at"]:
                return entry["data"]
            else:
                del self._memory_cache[key]
                
        # Check disk cache
        safe_filename = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in key) + ".json"
        disk_path = os.path.join(self.cache_dir, safe_filename)
        if os.path.exists(disk_path):
            try:
                with open(disk_path, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                    if current_time < entry.get("expires_at", 0):
                        # Populate back to memory
                        self._memory_cache[key] = entry
                        return entry.get("data")
                    else:
                        os.remove(disk_path)
            except Exception:
                pass
                
        return None

    def set(self, key: str, data: Any, ttl_seconds: int = 900):
        current_time = time.time()
        entry = {
            "expires_at": current_time + ttl_seconds,
            "created_at": current_time,
            "data": data
        }
        self._memory_cache[key] = entry
        
        # Save to disk cache (only if data is JSON serializable)
        safe_filename = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in key) + ".json"
        disk_path = os.path.join(self.cache_dir, safe_filename)
        try:
            with open(disk_path, "w", encoding="utf-8") as f:
                json.dump(entry, f, default=str)
        except Exception:
            pass

    def clear(self):
        self._memory_cache.clear()

# Global cache instance
cache = CacheManager()

