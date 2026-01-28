# metrics.py
from __future__ import annotations
import time
import functools
import asyncio
from typing import Callable, Dict, Optional
from prometheus_client import REGISTRY as DEFAULT_REGISTRY, Counter, Gauge, Histogram, CONTENT_TYPE_LATEST, generate_latest

# OpenTelemetry imports for trace correlation
try:
    from opentelemetry import trace
except ImportError:
    trace = None

#TODO: I want it to use the same registry as the main else i would have to exposed another endpoint, which might be a good idea for metrics that are not related to the app workings but development
REGISTRY = DEFAULT_REGISTRY

# Caches so we only register once per function
_GAUGES: Dict[str, Gauge] = {}
_COUNTERS: Dict[str, Counter] = {}
_HISTOS: Dict[str, Histogram] = {}   # for exemplars + latency percentiles

# Dummy no-op metric for when registration fails in multiprocess mode
class _NoOpMetric:
    def labels(self, **kwargs):
        return self
    def set(self, value): pass
    def inc(self, amount=1): pass
    def observe(self, value, exemplar=None): pass

def _get_trace_id() -> Optional[str]:
    """Extract trace_id from current OTEL span context.
    
    Returns:
        Trace ID as 32-character hex string, or None if no valid span context.
    """
    if trace is None:
        return None
    try:
        span = trace.get_current_span()
        if span is None:
            return None
        ctx = span.get_span_context()
        if ctx.is_valid:
            return format(ctx.trace_id, '032x')
    except Exception:
        pass
    return None


def _metric_names(fn: Callable, namespace: str = "server") -> Dict[str, str]:
    mod = fn.__module__.replace(".", "_")
    name = f"{fn.__name__}"
    base = f"{namespace}_{mod}_{name}"
    return {
        "gauge": f"{base}_seconds",
        "counter": f"{base}_calls_total",
        "histogram": f"{base}_seconds_bucket",
    }

def _get_or_create(fn: Callable, namespace="server",
                   histogram_buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5)):

    names = _metric_names(fn, namespace)

    # In multiprocess mode (Gunicorn), metrics are registered by master process.
    # Workers inherit the registry but not the module-level caches, causing registration to fail.
    # We catch ValueError and look up existing collectors from the registry.

    # In multiprocess mode, metrics may already be registered by master process
    # Just use no-op objects if registration fails - metrics still work via file writes
    if names["gauge"] not in _GAUGES:
        try:
            _GAUGES[names["gauge"]] = Gauge(
                names["gauge"], "Execution time of the function in seconds (last run).",
                ["status"], registry=REGISTRY
            )
        except ValueError:
            # Already registered - use no-op (multiprocess mode writes to files anyway)
            _GAUGES[names["gauge"]] = _NoOpMetric()

    if names["counter"] not in _COUNTERS:
        try:
            _COUNTERS[names["counter"]] = Counter(
                names["counter"], "Number of calls to the function.",
                ["status"], registry=REGISTRY
            )
        except ValueError:
            _COUNTERS[names["counter"]] = _NoOpMetric()

    if names["histogram"] not in _HISTOS:
        metric_name = names["histogram"].replace("_bucket", "")
        try:
            _HISTOS[names["histogram"]] = Histogram(
                metric_name,  # real metric name without "_bucket"
                "Execution time distribution of the function in seconds.",
                ["status"], registry=REGISTRY, buckets=histogram_buckets
            )
        except ValueError:
            _HISTOS[names["histogram"]] = _NoOpMetric()

    return _GAUGES[names["gauge"]], _COUNTERS[names["counter"]], _HISTOS[names["histogram"]]

def track_timing(namespace: str = "server", registry=DEFAULT_REGISTRY):
    """
    Decorator that:
      - measures execution time
      - sets a Gauge (last duration)
      - increments a Counter (calls)
      - observes a Histogram (for p95 etc. + exemplars)
    Note: I should not add correlation IDs as labels, as label is a key and it will clutter the labels selections with low-cardinality values.
    Solution would be to use exemplars on the histogram if I have a trace_id.
    #TODO: Extend for Tempo once The section of Prometheus is done.
    """
    def decorator(fn: Callable):
        # Lazy initialization: create metrics at runtime, not decoration time
        # This avoids Gunicorn multiprocess issues where decorators run in master before fork
        _metrics_cache = {}

        def _get_metrics():
            if 'gauge' not in _metrics_cache:
                gauge, counter, hist = _get_or_create(fn, namespace=namespace)
                _metrics_cache['gauge'] = gauge
                _metrics_cache['counter'] = counter
                _metrics_cache['hist'] = hist
            return _metrics_cache['gauge'], _metrics_cache['counter'], _metrics_cache['hist']

        # Check if the function is async
        if asyncio.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args, **kwargs):
                gauge, counter, hist = _get_metrics()
                start = time.perf_counter()
                status = "ok"
                try:
                    result = await fn(*args, **kwargs)
                    return result
                except Exception:
                    status = "error"
                    raise
                finally:
                    dur = time.perf_counter() - start
                    gauge.labels(status=status).set(dur)
                    counter.labels(status=status).inc()

                    # Optional exemplar hook for a low-cardinality context (e.g., trace_id) if available
                    exemplar = None
                    trace_id = _get_trace_id()  # Pull from OTEL context
                    if trace_id:
                        exemplar = {"trace_id": trace_id}

                    # Observe with or without exemplar (exemplars only on Histogram/Counter)
                    try:
                        if exemplar:
                            hist.labels(status=status).observe(dur, exemplar=exemplar)
                        else:
                            hist.labels(status=status).observe(dur)
                    except TypeError:
                        # If prometheus_client is old and lacks exemplars, fall back gracefully.
                        hist.labels(status=status).observe(dur)
            return async_wrapper
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args, **kwargs):
                gauge, counter, hist = _get_metrics()
                start = time.perf_counter()
                status = "ok"
                try:
                    result = fn(*args, **kwargs)
                    return result
                except Exception:
                    status = "error"
                    raise
                finally:
                    dur = time.perf_counter() - start
                    gauge.labels(status=status).set(dur)
                    counter.labels(status=status).inc()

                    # Optional exemplar hook for a low-cardinality context (e.g., trace_id) if available
                    exemplar = None
                    trace_id = _get_trace_id()  # Pull from OTEL context
                    if trace_id:
                        exemplar = {"trace_id": trace_id}

                    # Observe with or without exemplar (exemplars only on Histogram/Counter)
                    try:
                        if exemplar:
                            hist.labels(status=status).observe(dur, exemplar=exemplar)
                        else:
                            hist.labels(status=status).observe(dur)
                    except TypeError:
                        # If prometheus_client is old and lacks exemplars, fall back gracefully.
                        hist.labels(status=status).observe(dur)
            return sync_wrapper
    return decorator

def metrics_text() -> bytes:
    """Use in /metrics endpoint for debug or development when default global registry is unavailable."""
    return generate_latest(REGISTRY)

def metrics_content_type() -> str:
    return CONTENT_TYPE_LATEST
