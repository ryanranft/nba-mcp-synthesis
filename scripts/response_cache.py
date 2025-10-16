"""
Response caching for LLM calls to save costs during development
"""

import hashlib
import json
import os
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

class ResponseCache:
    """Cache LLM responses to save costs during development"""

    def __init__(self, cache_dir: str = "cache/llm_responses", ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.ttl_hours = ttl_hours
        os.makedirs(cache_dir, exist_ok=True)

    def get_cache_key(self, model: str, prompt: str, **kwargs) -> str:
        """Generate cache key from model, prompt, and parameters"""
        # Include relevant parameters in cache key
        params = {
            'model': model,
            'prompt': prompt,
            'temperature': kwargs.get('temperature', 0.7),
            'max_tokens': kwargs.get('max_tokens', 1000)
        }

        content = json.dumps(params, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, model: str, prompt: str, **kwargs) -> Optional[Dict]:
        """Get cached response"""
        key = self.get_cache_key(model, prompt, **kwargs)
        cache_file = os.path.join(self.cache_dir, f"{key}.json")

        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)

                # Check if cache is still valid
                cache_time = datetime.fromisoformat(data['timestamp'])
                if datetime.now() - cache_time < timedelta(hours=self.ttl_hours):
                    return data['response']
                else:
                    # Remove expired cache
                    os.remove(cache_file)
            except Exception as e:
                print(f"Warning: Could not read cache file {cache_file}: {e}")

        return None

    def set(self, model: str, prompt: str, response: Dict, **kwargs):
        """Cache response"""
        key = self.get_cache_key(model, prompt, **kwargs)
        cache_file = os.path.join(self.cache_dir, f"{key}.json")

        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'model': model,
            'response': response,
            'params': kwargs
        }

        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not write cache file {cache_file}: {e}")

    def clear_expired(self):
        """Clear expired cache files"""
        if not os.path.exists(self.cache_dir):
            return

        cutoff_time = datetime.now() - timedelta(hours=self.ttl_hours)
        removed_count = 0

        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.cache_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)

                    cache_time = datetime.fromisoformat(data['timestamp'])
                    if cache_time < cutoff_time:
                        os.remove(filepath)
                        removed_count += 1
                except Exception:
                    # Remove corrupted files
                    os.remove(filepath)
                    removed_count += 1

        if removed_count > 0:
            print(f"Cleared {removed_count} expired cache files")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not os.path.exists(self.cache_dir):
            return {'total_files': 0, 'total_size_mb': 0}

        total_files = 0
        total_size = 0

        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.cache_dir, filename)
                total_files += 1
                total_size += os.path.getsize(filepath)

        return {
            'total_files': total_files,
            'total_size_mb': total_size / (1024 * 1024),
            'cache_dir': self.cache_dir
        }




