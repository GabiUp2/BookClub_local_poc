import os
import time
import atexit
import datetime
import logging
import uuid
from pathlib import Path

import fastapi
from fastapi import Response, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry
from prometheus_client import multiprocess
from prometheus_client import platform_collector

# Observability imports - handle both local dev and Docker paths
try:
    from book_club.observability.IngestMetrics import ingest_metrics
except ImportError:
    try:
        from observability.IngestMetrics import ingest_metrics
    except ImportError:
        # Final fallback - create no-op stub
        class _NoOpIngestMetrics:
            def observe_upload(self, *args, **kwargs): pass
            def track_upload(self):
                def decorator(fn):
                    return fn
                return decorator
        ingest_metrics = _NoOpIngestMetrics()

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
        log_format = os.getenv(
            "LOGS_FORMAT",
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(lineno)d - %(funcName)s - %(process)d - %(thread)d - %(threadName)s - %(message)s",
        )
        file_handler = logging.FileHandler(f"{log_dir}/server_main.log")
        formatter = logging.Formatter(log_format)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def _init_otel(app_name: str = "bookclub-server", app_version: str = "0.0.1"):
    pass


async def lifespan(app: fastapi.FastAPI):
    # startup
    app.state.started_at = time.time()
    app.state.started_at_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    app.state.app_env = os.getenv("APP_ENV", "local")

    _clear_multiproc_dir()
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
    start_time = _time.perf_counter()
    size_bytes = 0

    try:
        # Validate content type
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Only PDF files are allowed.",
            )

        # Validate filename extension
        original_filename = file.filename or "unknown.pdf"
        if not original_filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="File must have a .pdf extension.",
            )

        # Read file content
        content = await file.read()
        size_bytes = len(content)

        # Validate file size
        max_size_bytes = MAX_PDF_SIZE_MB * 1024 * 1024
        if size_bytes > max_size_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File too large: {size_bytes / (1024 * 1024):.1f}MB exceeds limit of {MAX_PDF_SIZE_MB}MB.",
            )

        # Ensure storage directory exists
        PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

        # Generate unique filename to avoid collisions
        unique_id = uuid.uuid4().hex[:8]
        safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in original_filename)
        unique_filename = f"{unique_id}_{safe_name}"
        file_path = PDF_STORAGE_DIR / unique_filename

        # Write file to storage
        try:
            file_path.write_bytes(content)
            logger.info(f"PDF uploaded: {unique_filename} ({size_bytes} bytes)")
        except OSError as e:
            logger.error(f"Failed to save PDF {unique_filename}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to save file to storage.",
            )

        # Record success metrics
        duration_s = _time.perf_counter() - start_time
        ingest_metrics.observe_upload(size_bytes=size_bytes, status="ok", duration_s=duration_s)

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
        ingest_metrics.observe_upload(size_bytes=size_bytes, status="error", duration_s=duration_s)
        raise

    except Exception as e:
        # Record error metrics for unexpected exceptions
        duration_s = _time.perf_counter() - start_time
        ingest_metrics.observe_upload(size_bytes=size_bytes, status="error", duration_s=duration_s)
        logger.exception(f"Unexpected error during PDF upload: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during upload.")
