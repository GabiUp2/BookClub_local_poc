from __future__ import annotations

import atexit
import logging
import os
import sys
import time
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.status import Status, StatusCode
from prometheus_client import CollectorRegistry, Counter, Histogram, push_to_gateway
from rich.console import Console


ACTION_LOGGER_NAME = "book_club.orc.action"
_TRACING_CONFIGURED = False
_METRICS_PUSH_REGISTERED = False

_ACTION_REGISTRY = CollectorRegistry()
_ACTION_SIGNALS = Counter(
    "bookclub_orc_action_signals_total",
    "ORC action signals emitted by state.",
    ("action", "state"),
    registry=_ACTION_REGISTRY,
)
_ACTION_DURATION = Histogram(
    "bookclub_orc_action_duration_seconds",
    "Duration of completed ORC orchestration actions.",
    ("action", "outcome"),
    registry=_ACTION_REGISTRY,
)


def _push_action_metrics(logger: logging.Logger) -> None:
    """Best-effort push of short-lived CLI metrics to the local Pushgateway."""
    endpoint = os.environ.get("PUSHGATEWAY_URL", "http://localhost:9091")
    try:
        push_to_gateway(endpoint, job="bookclub_orc", registry=_ACTION_REGISTRY)
    except Exception as exc:  # telemetry must never break orchestration
        logger.debug(
            "Could not push ORC metrics to %s: %s",
            endpoint,
            exc,
            extra={"orc_action": "telemetry.metrics", "orc_state": "warning"},
        )


@dataclass(frozen=True)
class OrcRuntime:
    """CLI-only runtime state shared by ORC commands."""

    console: Console
    trace_enabled: bool
    verbose: bool
    quiet: bool
    logger: logging.Logger

    def emit(self, state: str, action: str, message: str) -> None:
        """Emit one action signal to terminal, logs, metrics and the active trace."""
        terminal_styles = {
            "start": ("→", "cyan"),
            "success": ("✓", "green"),
            "warning": ("!", "yellow"),
            "failure": ("✗", "red"),
            "info": ("•", "blue"),
        }
        symbol, style = terminal_styles.get(state, ("•", "white"))

        if not self.quiet or state in {"warning", "failure"}:
            self.console.print(f"[{style}]{symbol}[/{style}] {message}")

        log_level = {
            "warning": logging.WARNING,
            "failure": logging.ERROR,
        }.get(state, logging.INFO)
        self.logger.log(
            log_level,
            message,
            extra={"orc_action": action, "orc_state": state},
        )
        _ACTION_SIGNALS.labels(action=action, state=state).inc()

        span = trace.get_current_span()
        if span.is_recording():
            span.add_event(
                "orc.action.signal",
                attributes={
                    "orc.action": action,
                    "orc.state": state,
                    "orc.message": message,
                },
            )

    @contextmanager
    def action(self, name: str, description: str) -> Iterator[None]:
        """Wrap one orchestration action with consistent signals and tracing."""
        tracer = trace.get_tracer("book_club.orc")
        span_context = (
            tracer.start_as_current_span(
                f"orc.{name}",
                attributes={"orc.action": name, "orc.description": description},
            )
            if self.trace_enabled
            else nullcontext()
        )

        started = time.perf_counter()
        self.emit("start", name, description)
        with span_context as span:
            try:
                yield
            except Exception as exc:
                duration = time.perf_counter() - started
                _ACTION_DURATION.labels(action=name, outcome="failure").observe(duration)
                if self.trace_enabled and span is not None:
                    span.record_exception(exc)
                    span.set_attribute("orc.duration_seconds", duration)
                    span.set_status(Status(StatusCode.ERROR, str(exc)))
                self.emit("failure", name, f"{description} failed: {exc}")
                raise
            else:
                duration = time.perf_counter() - started
                _ACTION_DURATION.labels(action=name, outcome="success").observe(duration)
                if self.trace_enabled and span is not None:
                    span.set_attribute("orc.duration_seconds", duration)
                self.emit("success", name, f"{description} ({duration:.2f}s)")


def make_console(color: bool | None) -> Console:
    """Create Rich console with auto colour by default and explicit overrides."""
    if color is True:
        return Console(force_terminal=True, color_system="auto")
    if color is False:
        return Console(force_terminal=False, color_system=None, no_color=True)
    return Console(color_system="auto")


def configure_action_logger(verbose: bool) -> logging.Logger:
    global _METRICS_PUSH_REGISTERED

    logger = logging.getLogger(ACTION_LOGGER_NAME)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s action=%(orc_action)s state=%(orc_state)s %(message)s"
        )

        logs_dir = Path(os.environ.get("ORC_LOG_DIR", "logs"))
        try:
            logs_dir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(logs_dir / "orc.log")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError:
            # ORC must still be usable in read-only checkouts or constrained shells.
            pass

        if verbose:
            stream_handler = logging.StreamHandler(sys.stderr)
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

    if not _METRICS_PUSH_REGISTERED:
        atexit.register(_push_action_metrics, logger)
        _METRICS_PUSH_REGISTERED = True

    return logger


def configure_tracing(enabled: bool) -> None:
    """Configure a CLI-local OTLP tracer when --trace is requested."""
    global _TRACING_CONFIGURED
    if not enabled or _TRACING_CONFIGURED:
        return

    # Import lazily so normal ORC invocations do not initialise exporter code.
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": "bookclub-orc",
                "deployment.environment": os.environ.get("APP_ENV", "local"),
            }
        )
    )
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=endpoint.startswith("http://"))
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    _TRACING_CONFIGURED = True
