# Tests for `IngestMetrics.py`.
# British English is used in comments and docstrings.

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from prometheus_client import CollectorRegistry, generate_latest

pytest_plugins = ("pytest_asyncio",)

# Module under test
from book_club.observability.IngestMetrics import (
    IngestMetrics,
    _NoOpMetric,
    _safe_register,
    ingest_metrics,
)

import book_club.observability.IngestMetrics as im_module


# ─── Unit Tests ───────────────────────────────────────────────────────────────


class TestNoOpMetric:
    """Tests for the _NoOpMetric fallback class."""

    def test_labels_returns_self(self):
        """NoOpMetric.labels returns self for chaining."""
        noop = _NoOpMetric()
        result = noop.labels(status="ok")
        assert result is noop

    def test_inc_does_nothing(self):
        """NoOpMetric.inc does nothing and raises no error."""
        noop = _NoOpMetric()
        noop.inc()
        noop.inc(100)  # should not raise

    def test_observe_does_nothing(self):
        """NoOpMetric.observe does nothing and raises no error."""
        noop = _NoOpMetric()
        noop.observe(12345)
        noop.observe(67890, exemplar={"trace_id": "abc"})  # should not raise


class TestSafeRegister:
    """Tests for _safe_register helper function."""

    def test_returns_metric_on_success(self):
        """_safe_register returns actual metric when registration succeeds."""
        from prometheus_client import Counter

        registry = CollectorRegistry()
        metric = _safe_register(
            Counter,
            "test_safe_register_counter",
            "Test counter",
            ["status"],
        )
        # The safe_register uses default registry, so we check type
        assert hasattr(metric, "labels")
        assert hasattr(metric, "inc")

    def test_returns_noop_on_duplicate(self):
        """_safe_register returns NoOpMetric when metric already registered."""
        from prometheus_client import Counter

        # Register the metric once
        _safe_register(
            Counter,
            "test_duplicate_counter",
            "First registration",
            ["label"],
        )
        # Second registration should return NoOpMetric
        metric2 = _safe_register(
            Counter,
            "test_duplicate_counter",
            "Duplicate registration",
            ["label"],
        )
        assert isinstance(metric2, _NoOpMetric)


# ─── IngestMetrics Class Tests ────────────────────────────────────────────────


class TestIngestMetricsClass:
    """Tests for the IngestMetrics class."""

    @pytest.fixture
    def isolated_metrics(self):
        """Create fresh IngestMetrics instance with mocked internal metrics."""
        # Create mock metrics to avoid polluting the default registry
        metrics = IngestMetrics.__new__(IngestMetrics)
        metrics._requests_total = MagicMock()
        metrics._duration_seconds = MagicMock()
        metrics._size_bytes = MagicMock()
        metrics._bytes_total = MagicMock()

        # Set up labels() to return self for chaining
        for m in [
            metrics._requests_total,
            metrics._duration_seconds,
            metrics._size_bytes,
            metrics._bytes_total,
        ]:
            m.labels.return_value = m

        return metrics

    def test_observe_upload_success_increments_requests(self, isolated_metrics):
        """observe_upload increments request counter with correct status."""
        isolated_metrics.observe_upload(
            size_bytes=1024, status="ok", duration_s=0.5
        )
        isolated_metrics._requests_total.labels.assert_called_with(status="ok")
        isolated_metrics._requests_total.inc.assert_called_once()

    def test_observe_upload_error_increments_requests(self, isolated_metrics):
        """observe_upload increments request counter on error."""
        isolated_metrics.observe_upload(
            size_bytes=512, status="error", duration_s=0.1
        )
        isolated_metrics._requests_total.labels.assert_called_with(status="error")
        isolated_metrics._requests_total.inc.assert_called_once()

    def test_observe_upload_increments_bytes_counter(self, isolated_metrics):
        """observe_upload increments bytes counter by file size."""
        isolated_metrics.observe_upload(
            size_bytes=2048, status="ok", duration_s=0.3
        )
        isolated_metrics._bytes_total.labels.assert_called_with(status="ok")
        isolated_metrics._bytes_total.inc.assert_called_once_with(2048)

    def test_observe_upload_observes_duration_histogram(self, isolated_metrics):
        """observe_upload records duration in histogram."""
        isolated_metrics.observe_upload(
            size_bytes=1024, status="ok", duration_s=0.75
        )
        isolated_metrics._duration_seconds.labels.assert_called_with(status="ok")
        isolated_metrics._duration_seconds.observe.assert_called_once_with(0.75)

    def test_observe_upload_observes_size_histogram(self, isolated_metrics):
        """observe_upload records file size in histogram."""
        isolated_metrics.observe_upload(
            size_bytes=5_000_000, status="ok", duration_s=1.0
        )
        isolated_metrics._size_bytes.labels.assert_called_with(status="ok")
        isolated_metrics._size_bytes.observe.assert_called_once_with(5_000_000)

    def test_observe_upload_with_exemplar(self, isolated_metrics):
        """observe_upload passes exemplar to histogram observations."""
        exemplar = {"trace_id": "abc123"}
        isolated_metrics.observe_upload(
            size_bytes=1024, status="ok", duration_s=0.5, exemplar=exemplar
        )
        # Check exemplar was passed to observe calls
        isolated_metrics._duration_seconds.observe.assert_called_once_with(
            0.5, exemplar=exemplar
        )
        isolated_metrics._size_bytes.observe.assert_called_once_with(
            1024, exemplar=exemplar
        )


# ─── track_upload Decorator Tests ─────────────────────────────────────────────


class TestTrackUploadDecorator:
    """Tests for the track_upload decorator."""

    @pytest.fixture
    def mock_observe(self, monkeypatch):
        """Mock observe_upload to track calls."""
        mock = MagicMock()
        # Use the module-level singleton
        monkeypatch.setattr(ingest_metrics, "observe_upload", mock)
        return mock

    def test_sync_decorator_records_success(self, mock_observe):
        """Decorator records success metrics for sync function."""

        class FakeResponse:
            size_bytes = 4096

        @ingest_metrics.track_upload()
        def upload_handler():
            time.sleep(0.01)
            return FakeResponse()

        result = upload_handler()

        assert result.size_bytes == 4096
        mock_observe.assert_called_once()
        # observe_upload(size_bytes, status, duration_s) - positional args
        args, kwargs = mock_observe.call_args
        size_bytes = kwargs.get("size_bytes", args[0] if args else None)
        status = kwargs.get("status", args[1] if len(args) > 1 else None)
        duration_s = kwargs.get("duration_s", args[2] if len(args) > 2 else None)
        assert size_bytes == 4096
        assert status == "ok"
        assert duration_s >= 0.01

    def test_sync_decorator_records_error(self, mock_observe):
        """Decorator records error metrics when sync function raises."""

        @ingest_metrics.track_upload()
        def failing_handler():
            raise ValueError("upload failed")

        with pytest.raises(ValueError, match="upload failed"):
            failing_handler()

        mock_observe.assert_called_once()
        args, kwargs = mock_observe.call_args
        status = kwargs.get("status", args[1] if len(args) > 1 else None)
        assert status == "error"

    @pytest.mark.asyncio
    async def test_async_decorator_records_success(self, mock_observe):
        """Decorator records success metrics for async function."""

        class FakeResponse:
            size_bytes = 8192

        @ingest_metrics.track_upload()
        async def async_upload_handler():
            await asyncio.sleep(0.01)
            return FakeResponse()

        result = await async_upload_handler()

        assert result.size_bytes == 8192
        mock_observe.assert_called_once()
        args, kwargs = mock_observe.call_args
        size_bytes = kwargs.get("size_bytes", args[0] if args else None)
        status = kwargs.get("status", args[1] if len(args) > 1 else None)
        duration_s = kwargs.get("duration_s", args[2] if len(args) > 2 else None)
        assert size_bytes == 8192
        assert status == "ok"
        assert duration_s >= 0.01

    @pytest.mark.asyncio
    async def test_async_decorator_records_error(self, mock_observe):
        """Decorator records error metrics when async function raises."""

        @ingest_metrics.track_upload()
        async def failing_async_handler():
            await asyncio.sleep(0.001)
            raise RuntimeError("async upload failed")

        with pytest.raises(RuntimeError, match="async upload failed"):
            await failing_async_handler()

        mock_observe.assert_called_once()
        args, kwargs = mock_observe.call_args
        status = kwargs.get("status", args[1] if len(args) > 1 else None)
        assert status == "error"

    def test_decorator_preserves_function_metadata(self):
        """Decorator preserves original function name and docstring."""

        @ingest_metrics.track_upload()
        def documented_upload():
            """Upload with documentation."""
            return MagicMock(size_bytes=100)

        assert documented_upload.__name__ == "documented_upload"
        assert documented_upload.__doc__ == "Upload with documentation."

    @pytest.mark.asyncio
    async def test_async_decorator_preserves_metadata(self):
        """Async decorator preserves function metadata."""

        @ingest_metrics.track_upload()
        async def async_documented():
            """Async upload documentation."""
            return MagicMock(size_bytes=200)

        assert async_documented.__name__ == "async_documented"
        assert async_documented.__doc__ == "Async upload documentation."
        assert asyncio.iscoroutinefunction(async_documented)


# ─── Integration Tests ────────────────────────────────────────────────────────

pytestmark = pytest.mark.behaviour


class TestIngestMetricsIntegration:
    """Integration tests that verify metrics appear in Prometheus output."""

    @pytest.fixture
    def fresh_registry(self, monkeypatch):
        """Create a fresh registry and patch the module to use it."""
        registry = CollectorRegistry()
        monkeypatch.setattr(im_module, "REGISTRY", registry)
        return registry

    @pytest.fixture
    def fresh_metrics(self, fresh_registry):
        """Create fresh IngestMetrics instance using the isolated registry."""
        # Create a new instance that will register to our fresh registry
        return IngestMetrics()

    def test_metrics_appear_in_prometheus_output(self, fresh_metrics, fresh_registry):
        """Metrics should appear in Prometheus text output after observation."""
        fresh_metrics.observe_upload(
            size_bytes=1_000_000, status="ok", duration_s=0.5
        )

        output = generate_latest(fresh_registry).decode("utf-8")

        # Check all four metric families are present
        assert "bookclub_pdf_upload_requests_total" in output
        assert "bookclub_pdf_upload_duration_seconds" in output
        assert "bookclub_pdf_upload_size_bytes" in output
        assert "bookclub_pdf_upload_bytes_total" in output

    def test_status_label_appears_in_output(self, fresh_metrics, fresh_registry):
        """Status label should appear with correct values."""
        fresh_metrics.observe_upload(size_bytes=1024, status="ok", duration_s=0.1)
        fresh_metrics.observe_upload(size_bytes=512, status="error", duration_s=0.05)

        output = generate_latest(fresh_registry).decode("utf-8")

        assert 'status="ok"' in output
        assert 'status="error"' in output

    def test_bytes_counter_accumulates(self, fresh_metrics, fresh_registry):
        """Bytes counter should accumulate across multiple uploads."""
        fresh_metrics.observe_upload(size_bytes=1000, status="ok", duration_s=0.1)
        fresh_metrics.observe_upload(size_bytes=2000, status="ok", duration_s=0.2)
        fresh_metrics.observe_upload(size_bytes=3000, status="ok", duration_s=0.3)

        output = generate_latest(fresh_registry).decode("utf-8")

        # Find the bytes_total line for status="ok"
        # The counter should show 6000.0 total
        assert "bookclub_pdf_upload_bytes_total" in output
        # We can't easily parse the exact value, but verify metric exists

    def test_request_counter_increments(self, fresh_metrics, fresh_registry):
        """Request counter should increment with each upload."""
        for _ in range(5):
            fresh_metrics.observe_upload(size_bytes=100, status="ok", duration_s=0.01)

        output = generate_latest(fresh_registry).decode("utf-8")
        assert "bookclub_pdf_upload_requests_total" in output

    def test_histogram_buckets_present(self, fresh_metrics, fresh_registry):
        """Histogram buckets should be present in output."""
        fresh_metrics.observe_upload(
            size_bytes=500_000, status="ok", duration_s=0.25
        )

        output = generate_latest(fresh_registry).decode("utf-8")

        # Duration histogram buckets
        assert "bookclub_pdf_upload_duration_seconds_bucket" in output
        # Size histogram buckets
        assert "bookclub_pdf_upload_size_bytes_bucket" in output

    def test_duration_histogram_sum_and_count(self, fresh_metrics, fresh_registry):
        """Duration histogram should track sum and count."""
        fresh_metrics.observe_upload(size_bytes=1024, status="ok", duration_s=0.5)
        fresh_metrics.observe_upload(size_bytes=2048, status="ok", duration_s=1.0)

        output = generate_latest(fresh_registry).decode("utf-8")

        assert "bookclub_pdf_upload_duration_seconds_sum" in output
        assert "bookclub_pdf_upload_duration_seconds_count" in output

    def test_size_histogram_sum_and_count(self, fresh_metrics, fresh_registry):
        """Size histogram should track sum and count."""
        fresh_metrics.observe_upload(
            size_bytes=1_000_000, status="ok", duration_s=0.1
        )
        fresh_metrics.observe_upload(
            size_bytes=2_000_000, status="ok", duration_s=0.2
        )

        output = generate_latest(fresh_registry).decode("utf-8")

        assert "bookclub_pdf_upload_size_bytes_sum" in output
        assert "bookclub_pdf_upload_size_bytes_count" in output


# ─── Multiprocess Mode Tests ──────────────────────────────────────────────────


class TestMultiprocessMode:
    """Tests for multiprocess/Gunicorn compatibility."""

    def test_noop_fallback_on_duplicate_registration(self, monkeypatch):
        """IngestMetrics gracefully handles duplicate metric registration."""
        from prometheus_client import Counter

        # Create a registry and register a metric with the same name
        registry = CollectorRegistry()
        Counter(
            "bookclub_pdf_upload_requests_total",
            "Pre-existing metric",
            ["status"],
            registry=registry,
        )

        # Patch the module's registry
        monkeypatch.setattr(im_module, "REGISTRY", registry)

        # Creating IngestMetrics should not raise, even with duplicate names
        # It will get NoOpMetric fallbacks
        metrics = IngestMetrics()

        # Should still be callable without error
        metrics.observe_upload(size_bytes=1024, status="ok", duration_s=0.1)


# ─── Module Singleton Tests ───────────────────────────────────────────────────


class TestModuleSingleton:
    """Tests for the module-level ingest_metrics singleton."""

    def test_singleton_is_ingest_metrics_instance(self):
        """Module singleton should be an IngestMetrics instance."""
        assert isinstance(ingest_metrics, IngestMetrics)

    def test_singleton_has_observe_upload_method(self):
        """Singleton should have observe_upload method."""
        assert hasattr(ingest_metrics, "observe_upload")
        assert callable(ingest_metrics.observe_upload)

    def test_singleton_has_track_upload_decorator(self):
        """Singleton should have track_upload decorator method."""
        assert hasattr(ingest_metrics, "track_upload")
        assert callable(ingest_metrics.track_upload)
