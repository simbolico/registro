"""Test metrics collection functionality."""

import time
import pytest
from registro.utils.metrics import MetricsCollector, MetricPoint, metrics


class TestMetricPoint:
    """Test MetricPoint class."""
    
    def test_metric_point_creation(self):
        """Test creating a metric point."""
        point = MetricPoint(value=42.0)
        
        assert point.value == 42.0
        assert isinstance(point.timestamp, float)
        from datetime import datetime
        assert isinstance(point.datetime, datetime)
        assert point.tags == {}
    
    def test_metric_point_with_tags(self):
        """Test creating a metric point with tags."""
        tags = {"env": "test", "service": "users"}
        point = MetricPoint(value=100.0, tags=tags)
        
        assert point.value == 100.0
        assert point.tags == tags


class TestMetricsCollector:
    """Test MetricsCollector class."""
    
    def test_counter_increment(self):
        """Test counter increment."""
        collector = MetricsCollector()
        
        # Increment by default value
        collector.increment("test.counter")
        assert collector.get_counter("test.counter") == 1.0
        
        # Increment by custom value
        collector.increment("test.counter", 5.0)
        assert collector.get_counter("test.counter") == 6.0
    
    def test_counter_with_tags(self):
        """Test counter with tags."""
        collector = MetricsCollector()
        
        # Increment without tags
        collector.increment("requests", 1.0)
        
        # Increment with tags
        collector.increment("requests", 2.0, {"method": "GET"})
        collector.increment("requests", 3.0, {"method": "POST"})
        
        assert collector.get_counter("requests") == 1.0
        assert collector.get_counter("requests", {"method": "GET"}) == 2.0
        assert collector.get_counter("requests", {"method": "POST"}) == 3.0
    
    def test_gauge_set(self):
        """Test gauge setting."""
        collector = MetricsCollector()
        
        # Set gauge value
        collector.set_gauge("memory.usage", 75.5)
        assert collector.get_gauge("memory.usage") == 75.5
        
        # Update gauge value
        collector.set_gauge("memory.usage", 80.0)
        assert collector.get_gauge("memory.usage") == 80.0
    
    def test_gauge_with_tags(self):
        """Test gauge with tags."""
        collector = MetricsCollector()
        
        collector.set_gauge("cpu.usage", 50.0, {"host": "web1"})
        collector.set_gauge("cpu.usage", 75.0, {"host": "web2"})
        
        assert collector.get_gauge("cpu.usage", {"host": "web1"}) == 50.0
        assert collector.get_gauge("cpu.usage", {"host": "web2"}) == 75.0
        assert collector.get_gauge("cpu.usage") is None
    
    def test_histogram_record(self):
        """Test histogram recording."""
        collector = MetricsCollector()
        
        # Record some values
        collector.record_histogram("response.time", 100.0)
        collector.record_histogram("response.time", 200.0)
        collector.record_histogram("response.time", 300.0)
        
        stats = collector.get_histogram_stats("response.time")
        assert stats["count"] == 3
        assert stats["sum"] == 600.0
        assert stats["min"] == 100.0
        assert stats["max"] == 300.0
        assert stats["avg"] == 200.0
    
    def test_histogram_with_tags(self):
        """Test histogram with tags."""
        collector = MetricsCollector()
        
        collector.record_histogram("response.time", 100.0, {"endpoint": "/api/users"})
        collector.record_histogram("response.time", 50.0, {"endpoint": "/api/posts"})
        
        user_stats = collector.get_histogram_stats("response.time", {"endpoint": "/api/users"})
        post_stats = collector.get_histogram_stats("response.time", {"endpoint": "/api/posts"})
        
        assert user_stats["count"] == 1
        assert user_stats["sum"] == 100.0
        assert post_stats["count"] == 1
        assert post_stats["sum"] == 50.0
    
    def test_timer_record(self):
        """Test timer recording."""
        collector = MetricsCollector()
        
        # Record some durations
        collector.record_timer("operation.duration", 0.1)
        collector.record_timer("operation.duration", 0.2)
        collector.record_timer("operation.duration", 0.3)
        
        stats = collector.get_timer_stats("operation.duration")
        assert stats["count"] == 3
        assert stats["sum"] == 0.6
        assert stats["min"] == 0.1
        assert stats["max"] == 0.3
        assert abs(stats["avg"] - 0.2) < 1e-10
    
    def test_timer_context_manager(self):
        """Test timer context manager."""
        collector = MetricsCollector()
        
        # Use context manager
        with collector.timer("operation.duration"):
            time.sleep(0.01)  # Small delay
        
        stats = collector.get_timer_stats("operation.duration")
        assert stats["count"] == 1
        assert stats["min"] > 0.0  # Should be greater than 0
        assert stats["max"] > 0.0
        assert stats["avg"] > 0.0
    
    def test_timer_context_manager_with_tags(self):
        """Test timer context manager with tags."""
        collector = MetricsCollector()
        
        with collector.timer("operation.duration", {"operation": "test"}):
            time.sleep(0.01)
        
        stats = collector.get_timer_stats("operation.duration", {"operation": "test"})
        assert stats["count"] == 1
        assert stats["min"] > 0.0
    
    def test_get_all_metrics(self):
        """Test getting all metrics."""
        collector = MetricsCollector()
        
        # Add various metrics
        collector.increment("counter1", 5.0)
        collector.set_gauge("gauge1", 42.0)
        collector.record_histogram("hist1", 100.0)
        collector.record_timer("timer1", 0.1)
        
        all_metrics = collector.get_all_metrics()
        
        assert "counters" in all_metrics
        assert "gauges" in all_metrics
        assert "histograms" in all_metrics
        assert "timers" in all_metrics
        
        assert all_metrics["counters"]["counter1"] == 5.0
        assert all_metrics["gauges"]["gauge1"] == 42.0
        assert all_metrics["histograms"]["hist1"]["count"] == 1
        assert all_metrics["timers"]["timer1"]["count"] == 1
    
    def test_reset(self):
        """Test resetting metrics."""
        collector = MetricsCollector()
        
        # Add some metrics
        collector.increment("counter1", 5.0)
        collector.set_gauge("gauge1", 42.0)
        
        # Verify metrics exist
        assert collector.get_counter("counter1") == 5.0
        assert collector.get_gauge("gauge1") == 42.0
        
        # Reset metrics
        collector.reset()
        
        # Verify metrics are gone
        assert collector.get_counter("counter1") == 0.0
        assert collector.get_gauge("gauge1") is None
    
    def test_max_history_limit(self):
        """Test that history is limited to max_history."""
        collector = MetricsCollector(max_history=3)
        
        # Add more than max_history values
        collector.record_histogram("test", 1.0)
        collector.record_histogram("test", 2.0)
        collector.record_histogram("test", 3.0)
        collector.record_histogram("test", 4.0)
        
        stats = collector.get_histogram_stats("test")
        
        # Should only have 3 values (the most recent ones)
        assert stats["count"] == 3
        assert stats["sum"] == 9.0  # 2.0 + 3.0 + 4.0
    
    def test_empty_stats(self):
        """Test getting stats for empty metrics."""
        collector = MetricsCollector()
        
        assert collector.get_histogram_stats("nonexistent") == {}
        assert collector.get_timer_stats("nonexistent") == {}
        assert collector.get_gauge("nonexistent") is None
        assert collector.get_counter("nonexistent") == 0.0
    
    def test_thread_safety(self):
        """Test that metrics collector is thread-safe."""
        import threading
        
        collector = MetricsCollector()
        errors = []
        
        def increment_counter():
            try:
                for _ in range(100):
                    collector.increment("thread.test")
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = [threading.Thread(target=increment_counter) for _ in range(5)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check for errors
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        
        # Check final counter value
        assert collector.get_counter("thread.test") == 500.0


class TestGlobalMetrics:
    """Test global metrics instance."""
    
    def test_global_metrics_instance(self):
        """Test that global metrics instance exists and works."""
        global metrics
        
        # Should be an instance of MetricsCollector
        assert isinstance(metrics, MetricsCollector)
        
        # Should be able to use it
        metrics.increment("global.test", 1.0)
        assert metrics.get_counter("global.test") == 1.0
        
        # Reset for other tests
        metrics.reset()
