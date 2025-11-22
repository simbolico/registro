"""
Metrics utilities for the Registro library.

This module provides simple metrics collection functionality for monitoring
resource creation, validation, and operations.
"""

import time
import threading
from typing import Dict, Optional, Any, List
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class MetricPoint:
    """A single metric data point."""
    timestamp: float = field(default_factory=time.time)
    value: float = 0.0
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def datetime(self) -> datetime:
        """Get timestamp as datetime object."""
        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc)


class MetricsCollector:
    """
    Simple in-memory metrics collector for Registro.
    
    Tracks various metrics like operation counts, durations, and errors.
    Thread-safe for use in multi-threaded applications.
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize metrics collector.
        
        Args:
            max_history: Maximum number of data points to keep per metric
        """
        self._lock = threading.RLock()
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._timers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._max_history = max_history
    
    def increment(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """
        Increment a counter metric.
        
        Args:
            name: Metric name
            value: Value to increment by (default: 1.0)
            tags: Optional tags for the metric
        """
        with self._lock:
            key = self._make_key(name, tags)
            self._counters[key] += value
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Set a gauge metric value.
        
        Args:
            name: Metric name
            value: Value to set
            tags: Optional tags for the metric
        """
        with self._lock:
            key = self._make_key(name, tags)
            self._gauges[key] = value
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Record a value in a histogram.
        
        Args:
            name: Metric name
            value: Value to record
            tags: Optional tags for the metric
        """
        with self._lock:
            key = self._make_key(name, tags)
            self._histograms[key].append(MetricPoint(value=value, tags=tags or {}))
    
    def record_timer(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """
        Record a timing metric.
        
        Args:
            name: Metric name
            duration: Duration in seconds
            tags: Optional tags for the metric
        """
        with self._lock:
            key = self._make_key(name, tags)
            self._timers[key].append(MetricPoint(value=duration, tags=tags or {}))
    
    def timer(self, name: str, tags: Optional[Dict[str, str]] = None):
        """
        Context manager for timing operations.
        
        Args:
            name: Metric name
            tags: Optional tags for the metric
        
        Returns:
            Context manager that records the duration
        
        Example:
            >>> with metrics.timer("operation.duration"):
            ...     # do some work
            ...     pass
        """
        return _TimerContext(self, name, tags)
    
    def get_counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> float:
        """Get counter value."""
        with self._lock:
            key = self._make_key(name, tags)
            return self._counters[key]
    
    def get_gauge(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get gauge value."""
        with self._lock:
            key = self._make_key(name, tags)
            return self._gauges.get(key)
    
    def get_histogram_stats(self, name: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """
        Get histogram statistics.
        
        Returns:
            Dictionary with count, sum, min, max, avg statistics
        """
        with self._lock:
            key = self._make_key(name, tags)
            points = list(self._histograms[key])
            
            if not points:
                return {}
            
            values = [p.value for p in points]
            return {
                "count": len(values),
                "sum": sum(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values)
            }
    
    def get_timer_stats(self, name: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """
        Get timer statistics.
        
        Returns:
            Dictionary with count, sum, min, max, avg statistics
        """
        with self._lock:
            key = self._make_key(name, tags)
            points = list(self._timers[key])
            
            if not points:
                return {}
            
            values = [p.value for p in points]
            return {
                "count": len(values),
                "sum": sum(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values)
            }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all collected metrics as a dictionary.
        
        Returns:
            Dictionary containing all metrics
        """
        with self._lock:
            result = {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
            }
            
            # Add histogram stats
            result["histograms"] = {}
            for key in self._histograms:
                result["histograms"][key] = self.get_histogram_stats(key)
            
            # Add timer stats
            result["timers"] = {}
            for key in self._timers:
                result["timers"][key] = self.get_timer_stats(key)
            
            return result
    
    def reset(self):
        """Reset all collected metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timers.clear()
    
    def _make_key(self, name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Create a metric key from name and tags."""
        if not tags:
            return name
        
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"


class _TimerContext:
    """Context manager for timing operations."""
    
    def __init__(self, collector: MetricsCollector, name: str, tags: Optional[Dict[str, str]] = None):
        self.collector = collector
        self.name = name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time
            self.collector.record_timer(self.name, duration, self.tags)


# Global metrics instance
metrics = MetricsCollector()
