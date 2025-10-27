# Tests for `ExecutionTimings.py`.
# British English is used in comments and docstrings.

from __future__ import annotations

import asyncio
import time
from typing import Callable
from unittest.mock import MagicMock, patch

import pytest
from prometheus_client import REGISTRY, CollectorRegistry

pytest_plugins = ('pytest_asyncio',)

# Module under test
from book_club.observability.ExecutionTimings import (
    _NoOpMetric,
    _get_or_create,
    _metric_names,
    metrics_content_type,
    metrics_text,
    track_timing,
)

# Import the module for patching
import book_club.observability.ExecutionTimings as et_module


# ─── Unit Tests ───────────────────────────────────────────────────────────────


def test_noop_metric_labels_returns_self():
    """NoOpMetric.labels returns self for chaining."""
    noop = _NoOpMetric()
    result = noop.labels(status="ok")
    assert result is noop


def test_noop_metric_set_does_nothing():
    """NoOpMetric.set does nothing and raises no error."""
    noop = _NoOpMetric()
    noop.set(1.234)  # should not raise


def test_noop_metric_inc_does_nothing():
    """NoOpMetric.inc does nothing and raises no error."""
    noop = _NoOpMetric()
    noop.inc()
    noop.inc(5)  # should not raise


def test_noop_metric_observe_does_nothing():
    """NoOpMetric.observe does nothing and raises no error."""
    noop = _NoOpMetric()
    noop.observe(0.123)
    noop.observe(0.456, exemplar={"trace_id": "abc"})  # should not raise


def test_metric_names_generates_correct_names():
    """_metric_names generates the expected metric name components."""

    def example_fn():
        pass

    example_fn.__module__ = "book_club.server.routes"
    example_fn.__name__ = "get_health"

    names = _metric_names(example_fn, namespace="server")

    assert names["gauge"] == "server_book_club_server_routes_get_health_seconds"
    assert names["counter"] == "server_book_club_server_routes_get_health_calls_total"
    assert (
        names["histogram"]
        == "server_book_club_server_routes_get_health_seconds_bucket"
    )


def test_metric_names_custom_namespace():
    """_metric_names respects custom namespace."""

    def task_fn():
        pass

    task_fn.__module__ = "app.tasks"
    task_fn.__name__ = "process"

    names = _metric_names(task_fn, namespace="worker")

    assert names["gauge"].startswith("worker_")
    assert names["counter"].startswith("worker_")
    assert names["histogram"].startswith("worker_")


def test_metrics_text_returns_bytes():
    """metrics_text returns bytes containing Prometheus metrics."""
    result = metrics_text()
    assert isinstance(result, bytes)
    assert b"python_info" in result  # standard metric present


def test_metrics_content_type_returns_string():
    """metrics_content_type returns the Prometheus content type."""
    result = metrics_content_type()
    assert isinstance(result, str)
    assert "text/plain" in result


# ─── Behaviour Tests ──────────────────────────────────────────────────────────

pytestmark = pytest.mark.behaviour


@pytest.fixture
def isolated_registry():
    """Create an isolated metrics registry for each test."""
    registry = CollectorRegistry()
    return registry


@pytest.fixture
def clear_caches(monkeypatch):
    """Clear module-level metric caches before each test."""
    # Reset the global caches
    monkeypatch.setattr(et_module, "_GAUGES", {})
    monkeypatch.setattr(et_module, "_COUNTERS", {})
    monkeypatch.setattr(et_module, "_HISTOS", {})


def test_track_timing_sync_function_success(isolated_registry, clear_caches, monkeypatch):
    """Decorator tracks timing for successful sync function execution."""
    monkeypatch.setattr(et_module, "REGISTRY", isolated_registry)

    @track_timing(namespace="test")
    def add(a: int, b: int) -> int:
        time.sleep(0.01)  # simulate work
        return a + b

    result = add(2, 3)

    assert result == 5

    # Check metrics were created and recorded
    metric_data = metrics_text()
    assert b"test_" in metric_data
    assert b'status="ok"' in metric_data


def test_track_timing_sync_function_error(isolated_registry, clear_caches, monkeypatch):
    """Decorator tracks timing when sync function raises exception."""
    monkeypatch.setattr(et_module, "REGISTRY", isolated_registry)

    @track_timing(namespace="test")
    def failing_fn():
        time.sleep(0.01)
        raise ValueError("intentional error")

    with pytest.raises(ValueError, match="intentional error"):
        failing_fn()

    # Check metrics recorded with status="error"
    metric_data = metrics_text()
    assert b"test_" in metric_data
    assert b'status="error"' in metric_data


@pytest.mark.asyncio
async def test_track_timing_async_function_success(
    isolated_registry, clear_caches, monkeypatch
):
    """Decorator tracks timing for successful async function execution."""
    monkeypatch.setattr(et_module, "REGISTRY", isolated_registry)

    @track_timing(namespace="test")
    async def fetch_data(item_id: int) -> str:
        await asyncio.sleep(0.01)  # simulate async work
        return f"data_{item_id}"

    result = await fetch_data(42)

    assert result == "data_42"

    # Check metrics were created and recorded
    metric_data = metrics_text()
    assert b"test_" in metric_data
    assert b'status="ok"' in metric_data


@pytest.mark.asyncio
async def test_track_timing_async_function_error(
    isolated_registry, clear_caches, monkeypatch
):
    """Decorator tracks timing when async function raises exception."""
    monkeypatch.setattr(et_module, "REGISTRY", isolated_registry)

    @track_timing(namespace="test")
    async def failing_async_fn():
        await asyncio.sleep(0.01)
        raise RuntimeError("async error")

    with pytest.raises(RuntimeError, match="async error"):
        await failing_async_fn()

    # Check metrics recorded with status="error"
    metric_data = metrics_text()
    assert b"test_" in metric_data
    assert b'status="error"' in metric_data


def test_track_timing_records_duration(isolated_registry, clear_caches, monkeypatch):
    """Decorator records execution duration in gauge and histogram."""
    monkeypatch.setattr(et_module, "REGISTRY", isolated_registry)

    @track_timing(namespace="test")
    def timed_fn():
        time.sleep(0.05)
        return "done"

    start = time.perf_counter()
    result = timed_fn()
    elapsed = time.perf_counter() - start

    assert result == "done"
    assert elapsed >= 0.05  # sanity check

    # Verify histogram recorded the observation
    metric_data = metrics_text().decode("utf-8")
    assert "test_" in metric_data
    # Histogram metric should be present (named without _bucket suffix)
    assert "test_test_executiontimings_timed_fn_seconds" in metric_data


def test_track_timing_increments_counter(isolated_registry, clear_caches, monkeypatch):
    """Decorator increments call counter on each invocation."""
    monkeypatch.setattr(et_module, "REGISTRY", isolated_registry)

    @track_timing(namespace="test")
    def counted_fn():
        return "ok"

    counted_fn()
    counted_fn()
    counted_fn()

    metric_data = metrics_text().decode("utf-8")
    assert "test_" in metric_data
    assert "_calls_total" in metric_data


def test_track_timing_with_trace_id_exemplar(
    isolated_registry, clear_caches, monkeypatch
):
    """Decorator attaches exemplar when _trace_id kwarg is provided."""
    monkeypatch.setattr(et_module, "REGISTRY", isolated_registry)

    @track_timing(namespace="test")
    def traced_fn(_trace_id=None):
        return "traced"

    result = traced_fn(_trace_id="trace-abc-123")

    assert result == "traced"
    # Exemplars are attached but may not appear in text output without special config
    # This test verifies no error is raised when exemplar is provided
    metric_data = metrics_text()
    assert b"test_" in metric_data


def test_get_or_create_caches_metrics(isolated_registry, clear_caches, monkeypatch):
    """_get_or_create returns same metric instances on repeated calls."""
    monkeypatch.setattr(et_module, "REGISTRY", isolated_registry)

    def sample_fn():
        pass

    gauge1, counter1, hist1 = _get_or_create(sample_fn, namespace="test")
    gauge2, counter2, hist2 = _get_or_create(sample_fn, namespace="test")

    # Should return cached instances
    assert gauge1 is gauge2
    assert counter1 is counter2
    assert hist1 is hist2


def test_get_or_create_handles_duplicate_registration(
    isolated_registry, clear_caches, monkeypatch
):
    """_get_or_create falls back to NoOpMetric on duplicate registration."""
    monkeypatch.setattr(et_module, "REGISTRY", isolated_registry)

    def target_fn():
        pass

    # First call creates metrics
    gauge1, counter1, hist1 = _get_or_create(target_fn, namespace="test")

    # Clear caches to simulate multiprocess mode where caches are per-process
    monkeypatch.setattr(et_module, "_GAUGES", {})
    monkeypatch.setattr(et_module, "_COUNTERS", {})
    monkeypatch.setattr(et_module, "_HISTOS", {})

    # Second call should catch ValueError and return NoOpMetric
    gauge2, counter2, hist2 = _get_or_create(target_fn, namespace="test")

    # In multiprocess mode, we return NoOpMetric when registration fails
    assert isinstance(gauge2, _NoOpMetric)
    assert isinstance(counter2, _NoOpMetric)
    assert isinstance(hist2, _NoOpMetric)


def test_get_or_create_custom_histogram_buckets(
    isolated_registry, clear_caches, monkeypatch
):
    """_get_or_create accepts custom histogram buckets."""
    monkeypatch.setattr(et_module, "REGISTRY", isolated_registry)

    def custom_fn():
        pass

    custom_buckets = (0.1, 0.5, 1.0, 5.0)
    gauge, counter, hist = _get_or_create(
        custom_fn, namespace="test", histogram_buckets=custom_buckets
    )

    # Verify histogram was created (no exceptions raised)
    assert hist is not None


def test_track_timing_preserves_function_metadata(clear_caches):
    """Decorator preserves original function name and docstring."""

    @track_timing(namespace="test")
    def documented_fn():
        """This is a documented function."""
        return 42

    assert documented_fn.__name__ == "documented_fn"
    assert documented_fn.__doc__ == "This is a documented function."


@pytest.mark.asyncio
async def test_track_timing_async_preserves_metadata(clear_caches):
    """Decorator preserves async function metadata."""

    @track_timing(namespace="test")
    async def async_documented():
        """Async documented function."""
        return "async"

    assert async_documented.__name__ == "async_documented"
    assert async_documented.__doc__ == "Async documented function."
    assert asyncio.iscoroutinefunction(async_documented)


def test_track_timing_histogram_fallback_without_exemplar_support(
    isolated_registry, clear_caches, monkeypatch
):
    """Decorator gracefully handles histogram.observe without exemplar support."""
    monkeypatch.setattr(et_module, "REGISTRY", isolated_registry)

    # Create a mock histogram that raises TypeError when exemplar is passed
    mock_hist = MagicMock()
    mock_hist_labelled = MagicMock()
    mock_hist.labels.return_value = mock_hist_labelled

    def observe_without_exemplar(value, exemplar=None):
        if exemplar is not None:
            raise TypeError("exemplar not supported")
        # Normal observe

    mock_hist_labelled.observe = observe_without_exemplar

    @track_timing(namespace="test")
    def fn_with_trace(_trace_id=None):
        return "done"

    # Patch the _get_metrics to return our mock
    with patch.object(
        et_module, "_get_or_create", return_value=(MagicMock(), MagicMock(), mock_hist)
    ):
        # Should not raise even with old prometheus_client
        result = fn_with_trace(_trace_id="trace-123")
        assert result == "done"


def test_multiple_decorated_functions_independent_metrics(
    isolated_registry, clear_caches, monkeypatch
):
    """Multiple decorated functions have independent metrics."""
    monkeypatch.setattr(et_module, "REGISTRY", isolated_registry)

    @track_timing(namespace="test")
    def fn_a():
        return "a"

    @track_timing(namespace="test")
    def fn_b():
        return "b"

    fn_a()
    fn_b()

    metric_data = metrics_text().decode("utf-8")
    # Both functions should have their own metrics
    assert "fn_a" in metric_data
    assert "fn_b" in metric_data


def test_track_timing_with_args_and_kwargs(isolated_registry, clear_caches, monkeypatch):
    """Decorator works correctly with function arguments."""
    monkeypatch.setattr(et_module, "REGISTRY", isolated_registry)

    @track_timing(namespace="test")
    def complex_fn(a, b, c=10, d=20):
        return a + b + c + d

    result = complex_fn(1, 2, c=3, d=4)
    assert result == 10

    metric_data = metrics_text()
    assert b"test_" in metric_data


@pytest.mark.asyncio
async def test_track_timing_async_with_args(
    isolated_registry, clear_caches, monkeypatch
):
    """Async decorator works correctly with function arguments."""
    monkeypatch.setattr(et_module, "REGISTRY", isolated_registry)

    @track_timing(namespace="test")
    async def async_complex(x, y, multiplier=2):
        await asyncio.sleep(0.001)
        return (x + y) * multiplier

    result = await async_complex(5, 3, multiplier=3)
    assert result == 24

    metric_data = metrics_text()
    assert b"test_" in metric_data
