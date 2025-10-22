from __future__ import annotations

import time
from typing import Any, Dict, Tuple, Optional


class TTLCache:
    def __init__(self, default_ttl: int = 300):
        self._store: Dict[str, Tuple[float, Any, int]] = {}
        self._default_ttl = default_ttl

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl_val = ttl if ttl is not None else self._default_ttl
        self._store[key] = (time.time(), value, ttl_val)

    def get(self, key: str) -> Optional[Any]:
        item = self._store.get(key)
        if not item:
            return None
        ts, value, ttl = item
        if time.time() - ts > ttl:
            self._store.pop(key, None)
            return None
        return value

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()
