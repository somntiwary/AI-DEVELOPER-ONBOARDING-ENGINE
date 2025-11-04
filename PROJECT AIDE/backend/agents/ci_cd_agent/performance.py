"""
Performance Optimization Module for CI/CD Agent
===============================================
Provides advanced caching, performance monitoring, and optimization utilities.
"""

import time
import hashlib
import json
import logging
from typing import Any, Dict, Optional, Callable, Union
from functools import wraps
from datetime import datetime, timedelta
import threading
from collections import defaultdict

logger = logging.getLogger(__name__)

class AdvancedCache:
    """Advanced caching system with TTL, LRU eviction, and statistics."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.hit_count = 0
        self.miss_count = 0
        self.lock = threading.RLock()
        
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate a cache key from function name and arguments."""
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else {}
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        with self.lock:
            if key not in self.cache:
                self.miss_count += 1
                return None
            
            entry = self.cache[key]
            if time.time() > entry['expires_at']:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
                self.miss_count += 1
                return None
            
            self.access_times[key] = time.time()
            self.hit_count += 1
            return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        with self.lock:
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            ttl = ttl or self.default_ttl
            self.cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl,
                'created_at': time.time()
            }
            self.access_times[key] = time.time()
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        if lru_key in self.cache:
            del self.cache[lru_key]
        del self.access_times[lru_key]
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_requests = self.hit_count + self.miss_count
            hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hit_count': self.hit_count,
                'miss_count': self.miss_count,
                'hit_rate': round(hit_rate, 2),
                'total_requests': total_requests
            }

class PerformanceMonitor:
    """Performance monitoring and metrics collection."""
    
    def __init__(self):
        self.metrics: Dict[str, list] = defaultdict(list)
        self.lock = threading.RLock()
    
    def record_execution_time(self, function_name: str, execution_time: float, 
                            success: bool = True, error_message: Optional[str] = None):
        """Record execution time for a function."""
        with self.lock:
            self.metrics[function_name].append({
                'timestamp': datetime.now().isoformat(),
                'execution_time': execution_time,
                'success': success,
                'error_message': error_message
            })
    
    def get_metrics(self, function_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics for a function or all functions."""
        with self.lock:
            if function_name:
                if function_name not in self.metrics:
                    return {}
                
                times = [m['execution_time'] for m in self.metrics[function_name]]
                successes = [m['success'] for m in self.metrics[function_name]]
                
                return {
                    'function': function_name,
                    'total_calls': len(times),
                    'success_rate': sum(successes) / len(successes) * 100 if successes else 0,
                    'avg_execution_time': sum(times) / len(times) if times else 0,
                    'min_execution_time': min(times) if times else 0,
                    'max_execution_time': max(times) if times else 0,
                    'recent_calls': self.metrics[function_name][-10:]  # Last 10 calls
                }
            else:
                return {func: self.get_metrics(func) for func in self.metrics.keys()}

# Global instances
_advanced_cache = AdvancedCache()
_performance_monitor = PerformanceMonitor()

def cached(ttl: int = 300, cache_instance: Optional[AdvancedCache] = None):
    """Advanced caching decorator with TTL and statistics."""
    cache = cache_instance or _advanced_cache
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = cache._generate_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}, executing function")
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
        
        return wrapper
    return decorator

def monitor_performance(func: Callable) -> Callable:
    """Performance monitoring decorator."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        success = True
        error_message = None
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            execution_time = time.time() - start_time
            _performance_monitor.record_execution_time(
                func.__name__, execution_time, success, error_message
            )
            logger.debug(f"{func.__name__} executed in {execution_time:.3f}s (success: {success})")
    
    return wrapper

def optimize_github_workflow_parsing(workflows_dir: str) -> Dict[str, Any]:
    """Optimized GitHub workflow parsing with caching and parallel processing."""
    import os
    import yaml
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    def parse_single_workflow(file_path: str) -> Optional[Dict[str, Any]]:
        """Parse a single workflow file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return None
    
    if not os.path.exists(workflows_dir):
        return {"workflows": [], "errors": []}
    
    workflow_files = [
        os.path.join(workflows_dir, f) 
        for f in os.listdir(workflows_dir) 
        if f.endswith(('.yml', '.yaml'))
    ]
    
    workflows = []
    errors = []
    
    # Parse workflows in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_file = {
            executor.submit(parse_single_workflow, file_path): file_path 
            for file_path in workflow_files
        }
        
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                result = future.result()
                if result:
                    workflows.append(result)
                else:
                    errors.append(f"Failed to parse {file_path}")
            except Exception as e:
                errors.append(f"Error processing {file_path}: {e}")
    
    return {
        "workflows": workflows,
        "errors": errors,
        "total_files": len(workflow_files),
        "successful_parses": len(workflows)
    }

def optimize_validation_checks(repo_path: str) -> Dict[str, Any]:
    """Optimized validation with parallel file checking."""
    import os
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    def check_file_exists(file_path: str) -> Dict[str, Any]:
        """Check if a file exists and return metadata."""
        exists = os.path.exists(file_path)
        return {
            "file": file_path,
            "exists": exists,
            "size": os.path.getsize(file_path) if exists else 0,
            "modified": os.path.getmtime(file_path) if exists else 0
        }
    
    # Files to check
    files_to_check = [
        os.path.join(repo_path, ".gitignore"),
        os.path.join(repo_path, "Dockerfile"),
        os.path.join(repo_path, "requirements.txt"),
        os.path.join(repo_path, "package.json"),
        os.path.join(repo_path, "Jenkinsfile"),
        os.path.join(repo_path, ".github", "workflows")
    ]
    
    results = []
    
    # Check files in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_file = {
            executor.submit(check_file_exists, file_path): file_path 
            for file_path in files_to_check
        }
        
        for future in as_completed(future_to_file):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({
                    "file": future_to_file[future],
                    "exists": False,
                    "error": str(e)
                })
    
    return {
        "file_checks": results,
        "total_checked": len(files_to_check),
        "found_files": sum(1 for r in results if r.get("exists", False))
    }

def get_performance_summary() -> Dict[str, Any]:
    """Get comprehensive performance summary."""
    cache_stats = _advanced_cache.get_stats()
    performance_metrics = _performance_monitor.get_metrics()
    
    return {
        "cache": cache_stats,
        "performance": performance_metrics,
        "timestamp": datetime.now().isoformat(),
        "system_info": {
            "python_version": "3.11+",
            "threading_enabled": True
        }
    }

def clear_all_caches():
    """Clear all caches and reset performance metrics."""
    _advanced_cache.clear()
    _performance_monitor.metrics.clear()
    logger.info("All caches and performance metrics cleared")

# Export commonly used functions
__all__ = [
    'cached',
    'monitor_performance',
    'optimize_github_workflow_parsing',
    'optimize_validation_checks',
    'get_performance_summary',
    'clear_all_caches',
    'AdvancedCache',
    'PerformanceMonitor'
]
