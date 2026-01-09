# IngestMetrics.py
"""
Prometheus metrics for PDF upload and ingestion endpoints.

Provides RED metrics (Rate, Errors, Duration) plus domain-specific metrics:
- File size distribution (histogram)
- Total bytes throughput (counter)
- Total files uploaded (counter)

Usage:
    from book_club.observability.IngestMetrics import ingest_metrics

    # In endpoint:
    ingest_metrics.observe_upload(size_bytes=size, status="ok", duration_s=elapsed)
"""
from __future__ import annotations

import time
import functools
import asyncio
from typing import Callable, Literal, Optional

from prometheus_client import (
    REGISTRY as DEFAULT_REGISTRY,
    Counter,
    Histogram,
)

REGISTRY = DEFAULT_REGISTRY

# Metric name prefix
_NS = "bookclub"
_SUBSYSTEM = "pdf_upload"

# --- Metric Definitions ---

# File size buckets: 100KB, 500KB, 1MB, 2MB, 5MB, 10MB, 20MB, 50MB
_SIZE_BUCKETS = (
    100 * 1024,       # 100 KB
    500 * 1024,       # 500 KB
    1 * 1024 * 1024,  # 1 MB
    2 * 1024 * 1024,  # 2 MB
    5 * 1024 * 1024,  # 5 MB
    10 * 1024 * 1024, # 10 MB
    20 * 1024 * 1024, # 20 MB
    50 * 1024 * 1024, # 50 MB
)

# Duration buckets: 10ms to 30s (upload can be slow for large files)
_DURATION_BUCKETS = (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30)


class _NoOpMetric:
    """Fallback for multiprocess mode when registration fails."""
    def labels(self, **kwargs):
        return self
    def inc(self, amount=1): pass
    def observe(self, value, exemplar=None): pass


def _safe_register(metric_cls, name: str, desc: str, labels: list, **kwargs):
    """Register metric, returning no-op if already registered (multiprocess)."""
    try:
        return metric_cls(name, desc, labels, registry=REGISTRY, **kwargs)
    except ValueError:
        return _NoOpMetric()


class IngestMetrics:
    """
    Container for PDF upload/ingest metrics.

    Metrics exposed:
    - bookclub_pdf_upload_requests_total{status} - Counter (RED: Rate + Errors)
    - bookclub_pdf_upload_duration_seconds{status} - Histogram (RED: Duration)
    - bookclub_pdf_upload_size_bytes{status} - Histogram (file size distribution)
    - bookclub_pdf_upload_bytes_total{status} - Counter (throughput)
    """

    def __init__(self):
        self._requests_total = _safe_register(
            Counter,
            f"{_NS}_{_SUBSYSTEM}_requests_total",
            "Total PDF upload requests",
            ["status"],
        )
        self._duration_seconds = _safe_register(
            Histogram,
            f"{_NS}_{_SUBSYSTEM}_duration_seconds",
            "PDF upload request duration in seconds",
            ["status"],
            buckets=_DURATION_BUCKETS,
        )
        self._size_bytes = _safe_register(
            Histogram,
            f"{_NS}_{_SUBSYSTEM}_size_bytes",
            "Uploaded PDF file size in bytes",
            ["status"],
            buckets=_SIZE_BUCKETS,
        )
        self._bytes_total = _safe_register(
            Counter,
            f"{_NS}_{_SUBSYSTEM}_bytes_total",
            "Total bytes uploaded via PDF upload endpoint",
            ["status"],
        )

    def observe_upload(
        self,
        size_bytes: int,
        status: Literal["ok", "error"],
        duration_s: float,
        exemplar: Optional[dict] = None,
    ) -> None:
        """
        Record metrics for a PDF upload request.

        Args:
            size_bytes: Size of the uploaded file in bytes.
            status: "ok" for success, "error" for failure.
            duration_s: Request duration in seconds.
            exemplar: Optional dict for trace correlation (e.g., {"trace_id": "..."}).
        """
        self._requests_total.labels(status=status).inc()
        self._bytes_total.labels(status=status).inc(size_bytes)

        # Observe histograms (with optional exemplar for trace correlation)
        try:
            if exemplar:
                self._duration_seconds.labels(status=status).observe(duration_s, exemplar=exemplar)
                self._size_bytes.labels(status=status).observe(size_bytes, exemplar=exemplar)
            else:
                self._duration_seconds.labels(status=status).observe(duration_s)
                self._size_bytes.labels(status=status).observe(size_bytes)
        except TypeError:
            # Older prometheus_client without exemplar support
            self._duration_seconds.labels(status=status).observe(duration_s)
            self._size_bytes.labels(status=status).observe(size_bytes)

    def track_upload(self):
        """
        Decorator for upload endpoints. Automatically tracks duration and status.

        The decorated function MUST return a response object with a `size_bytes` attribute,
        or the function must set `_upload_size_bytes` in kwargs.

        Usage:
            @ingest_metrics.track_upload()
            async def upload_pdf(file: UploadFile) -> PDFUploadResponse:
                ...
        """
        def decorator(fn: Callable):
            if asyncio.iscoroutinefunction(fn):
                @functools.wraps(fn)
                async def async_wrapper(*args, **kwargs):
                    start = time.perf_counter()
                    status = "ok"
                    size_bytes = 0
                    try:
                        result = await fn(*args, **kwargs)
                        # Extract size from response or kwargs
                        size_bytes = getattr(result, "size_bytes", 0) or kwargs.get("_upload_size_bytes", 0)
                        return result
                    except Exception:
                        status = "error"
                        # Attempt to get size from kwargs if set before error
                        size_bytes = kwargs.get("_upload_size_bytes", 0)
                        raise
                    finally:
                        duration_s = time.perf_counter() - start
                        self.observe_upload(size_bytes, status, duration_s)
                return async_wrapper
            else:
                @functools.wraps(fn)
                def sync_wrapper(*args, **kwargs):
                    start = time.perf_counter()
                    status = "ok"
                    size_bytes = 0
                    try:
                        result = fn(*args, **kwargs)
                        size_bytes = getattr(result, "size_bytes", 0) or kwargs.get("_upload_size_bytes", 0)
                        return result
                    except Exception:
                        status = "error"
                        size_bytes = kwargs.get("_upload_size_bytes", 0)
                        raise
                    finally:
                        duration_s = time.perf_counter() - start
                        self.observe_upload(size_bytes, status, duration_s)
                return sync_wrapper
        return decorator


# Module-level singleton
ingest_metrics = IngestMetrics()
