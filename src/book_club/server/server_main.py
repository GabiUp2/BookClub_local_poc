import os
import time
import atexit
import datetime
import logging
import fastapi
from fastapi import Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry, REGISTRY
from prometheus_client import multiprocess
from prometheus_client import platform_collector

from book_club.observability.ExecutionTimings import track_timing

logger = logging.getLogger(__name__)

# CORS configuration
ALLOWED_ORIGINS = [
    os.getenv("FRONTEND_ORIGIN", "http://localhost:8000"),
    "http://bookclub-app:8000",
]

# ---- Prometheus helpers ----
PROM_MULTIPROC_DIR = os.getenv("PROMETHEUS_MULTIPROC_DIR")  # e.g., /tmp/prom_multiproc

def _build_singleprocess_registry():
    registry = CollectorRegistry()
    platform_collector.PlatformCollector(registry=registry)
    return registry

def _build_multiprocess_registry():
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    platform_collector.PlatformCollector(registry=registry)
    return registry

def _prom_registry():
    return _build_multiprocess_registry() if PROM_MULTIPROC_DIR else _build_singleprocess_registry()

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
                logger.error(f"Error clearing multiproc dir {PROM_MULTIPROC_DIR}: {e}. File: {file}")

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
        log_format = os.getenv("LOGS_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(lineno)d - %(funcName)s - %(process)d - %(thread)d - %(threadName)s - %(message)s")
        file_handler = logging.FileHandler(f"{log_dir}/server_main.log")
        formatter = logging.Formatter(log_format)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

# Lifespan of a server 
async def lifespan(app: fastapi.FastAPI):
    # startup
    app.state.started_at = time.time()
    app.state.started_at_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    app.state.app_env = os.getenv("APP_ENV", "local")
    
    _clear_multiproc_dir()
    _register_mark_dead() # Behaviour i want is for every worker to mark itself as dead when the server is shutting down.

    try:
        yield

    finally:   
        logger.info(f"Server shutdown at {datetime.datetime.now(datetime.timezone.utc).isoformat()}")

server = fastapi.FastAPI(title="Book Club Server", version="0.0.1", lifespan=lifespan)

server.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000", # it's the page that allows only requests from localhost:8000 and bookclub-app:8000 to avoid CORS issues.
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
