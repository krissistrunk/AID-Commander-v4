#!/usr/bin/env python3
"""
Performance monitoring and optimization utilities for AID Commander v4.0
"""

import time
import asyncio
import functools
import logging
from typing import Dict, Any, Callable, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Performance monitoring with metrics collection"""
    
    def __init__(self):
        self.metrics = {}
        self.cache = {}
    
    def record_metric(self, name: str, value: float, timestamp: datetime = None):
        """Record a performance metric"""
        if timestamp is None:
            timestamp = datetime.now()
        
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append({
            'value': value,
            'timestamp': timestamp.isoformat()
        })
        
        # Keep only last 1000 entries per metric
        if len(self.metrics[name]) > 1000:
            self.metrics[name] = self.metrics[name][-1000:]
    
    def get_metric_stats(self, name: str, window_minutes: int = 60) -> Dict[str, float]:
        """Get statistics for a metric within time window"""
        if name not in self.metrics:
            return {}
        
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        recent_values = [
            entry['value'] for entry in self.metrics[name]
            if datetime.fromisoformat(entry['timestamp']) > cutoff
        ]
        
        if not recent_values:
            return {}
        
        return {
            'count': len(recent_values),
            'avg': sum(recent_values) / len(recent_values),
            'min': min(recent_values),
            'max': max(recent_values),
            'latest': recent_values[-1]
        }

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def measure_performance(func: Callable) -> Callable:
    """Decorator to measure function performance"""
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            success = True
        except Exception as e:
            success = False
            raise
        finally:
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # Convert to milliseconds
            
            metric_name = f"{func.__module__}.{func.__name__}"
            performance_monitor.record_metric(f"{metric_name}.duration_ms", duration)
            performance_monitor.record_metric(f"{metric_name}.success_rate", 1.0 if success else 0.0)
            
            logger.debug(f"Performance: {metric_name} took {duration:.2f}ms")
        
        return result
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            success = False
            raise
        finally:
            end_time = time.time()
            duration = (end_time - start_time) * 1000
            
            metric_name = f"{func.__module__}.{func.__name__}"
            performance_monitor.record_metric(f"{metric_name}.duration_ms", duration)
            performance_monitor.record_metric(f"{metric_name}.success_rate", 1.0 if success else 0.0)
            
            logger.debug(f"Performance: {metric_name} took {duration:.2f}ms")
        
        return result
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

def cache_result(ttl: int = 300, key_func: Optional[Callable] = None):
    """Decorator to cache function results with TTL"""
    
    def decorator(func: Callable) -> Callable:
        cache_dict = {}
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Check cache
            if cache_key in cache_dict:
                entry = cache_dict[cache_key]
                if datetime.now() - entry['timestamp'] < timedelta(seconds=ttl):
                    logger.debug(f"Cache hit for {cache_key}")
                    return entry['value']
                else:
                    # Expired entry
                    del cache_dict[cache_key]
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache_dict[cache_key] = {
                'value': result,
                'timestamp': datetime.now()
            }
            
            logger.debug(f"Cache miss for {cache_key}, result cached")
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Check cache
            if cache_key in cache_dict:
                entry = cache_dict[cache_key]
                if datetime.now() - entry['timestamp'] < timedelta(seconds=ttl):
                    logger.debug(f"Cache hit for {cache_key}")
                    return entry['value']
                else:
                    del cache_dict[cache_key]
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_dict[cache_key] = {
                'value': result,
                'timestamp': datetime.now()
            }
            
            logger.debug(f"Cache miss for {cache_key}, result cached")
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

async def optimize_memory_usage():
    """Optimize memory usage by cleaning up caches"""
    import gc
    
    # Clear expired cache entries
    for cache_dict in [performance_monitor.cache]:
        expired_keys = [
            key for key, entry in cache_dict.items()
            if datetime.now() - entry['timestamp'] > timedelta(hours=1)
        ]
        for key in expired_keys:
            del cache_dict[key]
    
    # Force garbage collection
    gc.collect()
    
    logger.info("Memory optimization completed")