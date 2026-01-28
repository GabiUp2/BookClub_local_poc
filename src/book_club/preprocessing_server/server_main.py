import os
import time
import atexit
import datetime
import logging
import uuid
import asyncio
import random
from pathlib import Path

import fastapi
from fastapi import Response, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry
from prometheus_client import multiprocess
from prometheus_client import platform_collector

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, DEPLOYMENT_ENVIRONMENT
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.trace import Status, StatusCode

# Observability imports - handle both local dev and Docker paths
try:
    from book_club.observability.IngestMetrics import ingest_metrics
    from book_club.observability.GitHandler import git_commit_and_branch
except ImportError:
    try:
        from observability.IngestMetrics import ingest_metrics
        from observability.GitHandler import git_commit_and_branch
    except ImportError:
        # Final fallback - create no-op stub
        class _NoOpIngestMetrics:
            def observe_upload(self, *args, **kwargs):
                pass

            def track_upload(self):
                def decorator(fn):
                    return fn

                return decorator

        ingest_metrics = _NoOpIngestMetrics()
        
        def git_commit_and_branch():
            return {"commit": "unknown", "short": "unknown", "ref": "unknown"}

logger = logging.getLogger(__name__)

# PDF storage configuration
PDF_STORAGE_DIR = Path(os.getenv("PDF_STORAGE_DIR", "/pdfs"))
MAX_PDF_SIZE_MB = int(os.getenv("MAX_PDF_SIZE_MB", "50"))
ALLOWED_CONTENT_TYPES = {"application/pdf"}


class PDFUploadResponse(BaseModel):
    """Response model for PDF upload endpoint."""

    filename: str
    original_filename: str
    size_bytes: int
    path: str
    message: str


# CORS configuration
ALLOWED_ORIGINS = [
    os.getenv("FRONTEND_ORIGIN", "http://localhost:8000"),
    "http://bookclub-app:8000",
]

# ---- Prometheus helpers ----
PROM_MULTIPROC_DIR = os.getenv("PROMETHEUS_MULTIPROC_DIR")  # e.g., /tmp/prom_multiproc


def _build_singleprocess_registry():
    """Return the default registry for singleprocess mode.

    This includes all metrics registered via prometheus_client's default registry,
    including IngestMetrics and any other application metrics.
    """
    from prometheus_client import REGISTRY

    return REGISTRY


def _build_multiprocess_registry():
    """Build a registry for multiprocess (Gunicorn) mode.

    In multiprocess mode, metrics are written to files in PROMETHEUS_MULTIPROC_DIR
    and the MultiProcessCollector aggregates them across workers.
    """
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    platform_collector.PlatformCollector(registry=registry)
    return registry


def _prom_registry():
    return (
        _build_multiprocess_registry()
        if PROM_MULTIPROC_DIR
        else _build_singleprocess_registry()
    )


def _register_mark_dead():
    if PROM_MULTIPROC_DIR:
        pid = os.getpid()
        logger.info(f"Registering mark_process_dead for pid {pid}")
        atexit.register(multiprocess.mark_process_dead, pid)


def _clear_multiproc_dir():
    if PROM_MULTIPROC_DIR and os.path.isdir(PROM_MULTIPROC_DIR):
        logger.info(f"Clearing multiproc dir {PROM_MULTIPROC_DIR}")
        for file in os.listdir(PROM_MULTIPROC_DIR):
            try:
                os.remove(os.path.join(PROM_MULTIPROC_DIR, file))
            except OSError as e:
                logger.error(
                    f"Error clearing multiproc dir {PROM_MULTIPROC_DIR}: {e}. File: {file}"
                )


def _configure_logging() -> None:
    log_dir = os.getenv("LOG_DIR", "/logs")
    try:
        os.makedirs(log_dir, exist_ok=True)
    except PermissionError:
        # fall back to current directory or re-raise with context
        log_dir = "."
        os.makedirs(log_dir, exist_ok=True)
    finally:
        log_level = os.getenv("LOGS_LEVEL", "INFO").upper()
        # Include OTEL trace/span IDs if available (LoggingInstrumentor adds these)
        log_format = os.getenv(
            "LOGS_FORMAT",
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(lineno)d - %(funcName)s - %(process)d - %(thread)d - %(threadName)s - %(otelTraceID)s - %(otelSpanID)s - %(message)s",
        )
        file_handler = logging.FileHandler(f"{log_dir}/server_main.log")
        formatter = logging.Formatter(log_format)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def _init_otel(
    app_name: str = "bookclub-preprocessing-server", app_version: str = "0.0.1"
):
    """Initialise OpenTelemetry tracing with resource attributes, exporter, and instrumentors."""
    # Check if OTEL is enabled (default: enabled in local/dev)
    enable_otel = os.getenv("ENABLE_OTEL_TRACING", "true").lower() in ("true", "1", "yes")
    if not enable_otel:
        logger.info("OpenTelemetry tracing disabled via ENABLE_OTEL_TRACING")
        return
    
    try:
        # Get git metadata (best-effort, safe fallbacks)
        git_info = git_commit_and_branch()
        git_commit = git_info.get("commit", "unknown")
        git_branch = git_info.get("ref", "unknown")
    except Exception as e:
        logger.warning(f"Failed to get git metadata for OTEL: {e}")
        git_commit = "unknown"
        git_branch = "unknown"
    
    # Build resource attributes
    service_name = os.getenv("OTEL_SERVICE_NAME", app_name)
    deployment_env = os.getenv("APP_ENV", os.getenv("DEPLOYMENT_ENVIRONMENT", "local"))
    
    resource = Resource.create({
        SERVICE_NAME: service_name,
        DEPLOYMENT_ENVIRONMENT: deployment_env,
        "service.version": app_version,
        "git.commit": git_commit,
        "git.branch": git_branch,
    })
    
    # Configure OTLP exporter
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://alloy:4318")
    # Ensure endpoint doesn't have trailing slash
    otlp_endpoint = otlp_endpoint.rstrip("/")
    
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    
    # Set up tracer provider with batch processor
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    
    # Enable auto-instrumentation
    FastAPIInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    
    # Enable logging instrumentation for trace_id/span_id injection
    enable_otel_logs = os.getenv("ENABLE_OTEL_LOGS", "true").lower() in ("true", "1", "yes")
    if enable_otel_logs:
        LoggingInstrumentor().instrument(set_logging_format=True)
        logger.info("OpenTelemetry logging instrumentation enabled")
    
    logger.info(
        f"OpenTelemetry tracing initialised: service={service_name}, "
        f"env={deployment_env}, endpoint={otlp_endpoint}"
    )


async def lifespan(app: fastapi.FastAPI):
    # startup
    app.state.started_at = time.time()
    app.state.started_at_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    app.state.app_env = os.getenv("APP_ENV", "local")

    _clear_multiproc_dir()
    _init_otel()  # Initialise OpenTelemetry tracing
    _register_mark_dead()  # Behaviour i want is for every worker to mark itself as dead when the server is shutting down.

    try:
        yield

    finally:
        logger.info(
            f"Server shutdown at {datetime.datetime.now(datetime.timezone.utc).isoformat()}"
        )


server = fastapi.FastAPI(title="Book Club Server", version="0.0.1", lifespan=lifespan)

server.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",  # it's the page that allows only requests from localhost:8000 and bookclub-app:8000 to avoid CORS issues.
        "http://bookclub-app:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo fault injection configuration (only enabled in local/dev)
_demo_config = {"backend_delay_ms": 0, "cpu_burn_ms": 0, "error_rate": 0.0}


@server.middleware("http")
async def demo_fault_injection_middleware(request: fastapi.Request, call_next):
    """Apply demo faults (delay, CPU burn, error rate) for demo scenarios."""
    app_env = os.getenv("APP_ENV", "local")
    if app_env != "local" or not any(_demo_config.values()):
        return await call_next(request)
    
    # Skip fault injection for demo endpoints themselves
    if request.url.path.startswith("/__demo/"):
        return await call_next(request)
    
    # Apply delay
    if _demo_config["backend_delay_ms"] > 0:
        await asyncio.sleep(_demo_config["backend_delay_ms"] / 1000.0)
    
    # Apply CPU burn (blocking, so use sync sleep in a thread)
    if _demo_config["cpu_burn_ms"] > 0:
        import threading
        burn_end = time.time() + (_demo_config["cpu_burn_ms"] / 1000.0)
        def burn_cpu():
            while time.time() < burn_end:
                pass
        burn_thread = threading.Thread(target=burn_cpu)
        burn_thread.start()
        burn_thread.join()
    
    # Apply error rate (probabilistic)
    if _demo_config["error_rate"] > 0 and random.random() < _demo_config["error_rate"]:
        # Mark span as error
        try:
            span = trace.get_current_span()
            if span:
                span.set_status(Status(StatusCode.ERROR, "Demo fault injection"))
        except Exception:
            pass
        raise HTTPException(status_code=500, detail="Demo fault injection: probabilistic error")
    
    return await call_next(request)

# ----- Metadata -----


@server.get("/health", tags=["health"])
async def health() -> dict:
    started = getattr(server.state, "started_at", None)
    uptime = round(time.time() - started, 3) if started else 0.0
    return {
        "status": "ok",
        "env": getattr(server.state, "app_env", "local"),
        "started_at": getattr(server.state, "started_at_iso", None),
        "uptime_s": uptime,
        "pid": os.getpid(),
        "multiprocess": bool(PROM_MULTIPROC_DIR),
    }


@server.get("/metrics", tags=["metrics"])
async def metrics():
    reg = _prom_registry()
    data = generate_latest(reg)
    return Response(
        data,
        media_type=CONTENT_TYPE_LATEST,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        },
    )


# ----- Endpoints -----


@server.get("/ingest", tags=["ingest"])
async def ingest() -> dict:
    return {"status": "not_implemented"}


@server.get("/generate_flashcards", tags=["generate_flashcards"])
async def generate_flashcards() -> dict:
    return {"status": "not_implemented"}


@server.get("/srs", tags=["srs"])
async def srs() -> dict:
    return {"status": "not_implemented"}


@server.get("/anki_export", tags=["anki_export"])
async def anki_export() -> dict:
    return {"status": "not_implemented"}


# Demo fault injection endpoints (only in local/dev)
@server.post("/__demo/faults", tags=["demo"], include_in_schema=False)
async def set_demo_faults(config: dict):
    """Set demo fault injection configuration.
    
    Only available when APP_ENV=local.
    Config keys: backend_delay_ms, cpu_burn_ms, error_rate (0.0-1.0)
    """
    app_env = os.getenv("APP_ENV", "local")
    if app_env != "local":
        raise HTTPException(status_code=403, detail="Demo endpoints only available in local environment")
    
    _demo_config.update({
        "backend_delay_ms": config.get("backend_delay_ms", 0),
        "cpu_burn_ms": config.get("cpu_burn_ms", 0),
        "error_rate": config.get("error_rate", 0.0),
    })
    return {"status": "ok", "config": _demo_config}


@server.post("/__demo/reset", tags=["demo"], include_in_schema=False)
async def reset_demo_faults():
    """Reset demo fault injection to baseline (no faults)."""
    app_env = os.getenv("APP_ENV", "local")
    if app_env != "local":
        raise HTTPException(status_code=403, detail="Demo endpoints only available in local environment")
    
    _demo_config.update({"backend_delay_ms": 0, "cpu_burn_ms": 0, "error_rate": 0.0})
    return {"status": "ok", "config": _demo_config}


@server.post("/upload-pdf", tags=["ingest"], response_model=PDFUploadResponse)
async def upload_pdf(file: UploadFile = File(...)) -> PDFUploadResponse:
    """Upload a PDF file for processing.

    The file is saved to the configured PDF storage directory with a unique
    filename to avoid collisions.

    Metrics emitted:
    - bookclub_pdf_upload_requests_total{status}
    - bookclub_pdf_upload_duration_seconds{status}
    - bookclub_pdf_upload_size_bytes{status}
    - bookclub_pdf_upload_bytes_total{status}

    Args:
        file: The uploaded PDF file.

    Returns:
        PDFUploadResponse with file metadata and storage path.

    Raises:
        HTTPException: If the file is not a PDF or exceeds size limit.
    """
    import time as _time
    
    tracer = trace.get_tracer(__name__)
    start_time = _time.perf_counter()
    size_bytes = 0

    try:
        original_filename = file.filename or "unknown.pdf"
        
        # Validate content type and filename
        with tracer.start_as_current_span("pdf.validate") as span:
            span.set_attribute("file.filename", original_filename)
            span.set_attribute("file.content_type", file.content_type or "unknown")
            
            if file.content_type not in ALLOWED_CONTENT_TYPES:
                span.set_status(Status(StatusCode.ERROR, "Invalid content type"))
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type: {file.content_type}. Only PDF files are allowed.",
                )
            
            if not original_filename.lower().endswith(".pdf"):
                span.set_status(Status(StatusCode.ERROR, "Invalid file extension"))
                raise HTTPException(
                    status_code=400,
                    detail="File must have a .pdf extension.",
                )

        # Read file content
        with tracer.start_as_current_span("pdf.read") as span:
            content = await file.read()
            size_bytes = len(content)
            span.set_attribute("file.size_bytes", size_bytes)
            span.set_attribute("file.filename", original_filename)

        # Validate file size
        max_size_bytes = MAX_PDF_SIZE_MB * 1024 * 1024
        with tracer.start_as_current_span("pdf.validate_size") as span:
            if size_bytes > max_size_bytes:
                span.set_status(Status(StatusCode.ERROR, "File too large"))
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large: {size_bytes / (1024 * 1024):.1f}MB exceeds limit of {MAX_PDF_SIZE_MB}MB.",
                )

        # Parse PDF (placeholder for future implementation)
        with tracer.start_as_current_span("pdf.parse") as span:
            # TODO: Implement actual PDF parsing
            span.set_attribute("pdf.pages", 0)  # Placeholder
            pass

        # Chunk PDF (placeholder for future implementation)
        with tracer.start_as_current_span("pdf.chunk") as span:
            # TODO: Implement chunking logic
            span.set_attribute("chunks.count", 0)  # Placeholder
            pass

        # Embed chunks (placeholder for future implementation)
        with tracer.start_as_current_span("embed") as span:
            # TODO: Implement embedding logic
            span.set_attribute("embeddings.count", 0)  # Placeholder
            pass

        # Upsert to Qdrant (placeholder for future implementation)
        with tracer.start_as_current_span("qdrant.upsert") as span:
            try:
                # TODO: Implement Qdrant upsert
                span.set_attribute("qdrant.collection", "bookclub")  # Placeholder
                # When implemented, ensure errors are caught and span marked as ERROR
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                logger.error(f"Qdrant upsert failed: {e}")
                raise

        # Ensure storage directory exists
        PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

        # Generate unique filename to avoid collisions
        unique_id = uuid.uuid4().hex[:8]
        safe_name = "".join(
            c if c.isalnum() or c in "._-" else "_" for c in original_filename
        )
        unique_filename = f"{unique_id}_{safe_name}"
        file_path = PDF_STORAGE_DIR / unique_filename

        # Write file to storage
        with tracer.start_as_current_span("storage.write") as span:
            try:
                file_path.write_bytes(content)
                span.set_attribute("storage.path", str(file_path))
                logger.info(f"PDF uploaded: {unique_filename} ({size_bytes} bytes)")
            except OSError as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                logger.error(f"Failed to save PDF {unique_filename}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to save file to storage.",
                )

        # Record success metrics with trace correlation
        duration_s = _time.perf_counter() - start_time
        # Extract trace_id from OTEL context for exemplar
        exemplar = None
        try:
            from opentelemetry import trace as otel_trace
            span = otel_trace.get_current_span()
            if span:
                ctx = span.get_span_context()
                if ctx.is_valid:
                    exemplar = {"trace_id": format(ctx.trace_id, '032x')}
        except Exception:
            pass
        ingest_metrics.observe_upload(
            size_bytes=size_bytes, status="ok", duration_s=duration_s, exemplar=exemplar
        )

        return PDFUploadResponse(
            filename=unique_filename,
            original_filename=original_filename,
            size_bytes=size_bytes,
            path=str(file_path),
            message="PDF uploaded successfully.",
        )

    except HTTPException:
        # Record error metrics for HTTP exceptions (client errors)
        duration_s = _time.perf_counter() - start_time
        # Extract trace_id from OTEL context for exemplar
        exemplar = None
        try:
            from opentelemetry import trace as otel_trace
            span = otel_trace.get_current_span()
            if span:
                ctx = span.get_span_context()
                if ctx.is_valid:
                    exemplar = {"trace_id": format(ctx.trace_id, '032x')}
        except Exception:
            pass
        ingest_metrics.observe_upload(
            size_bytes=size_bytes, status="error", duration_s=duration_s, exemplar=exemplar
        )
        raise

    except Exception as e:
        # Record error metrics for unexpected exceptions
        duration_s = _time.perf_counter() - start_time
        # Extract trace_id from OTEL context for exemplar
        exemplar = None
        try:
            from opentelemetry import trace as otel_trace
            span = otel_trace.get_current_span()
            if span:
                ctx = span.get_span_context()
                if ctx.is_valid:
                    exemplar = {"trace_id": format(ctx.trace_id, '032x')}
        except Exception:
            pass
        ingest_metrics.observe_upload(
            size_bytes=size_bytes, status="error", duration_s=duration_s, exemplar=exemplar
        )
        logger.exception(f"Unexpected error during PDF upload: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error during upload."
        )
