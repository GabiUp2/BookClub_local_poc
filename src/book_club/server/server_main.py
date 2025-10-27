import os
import time
import datetime
import logging
import fastapi
from fastapi import Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry, REGISTRY
from prometheus_client import multiprocess
from prometheus_client import platform_collector

from observability.ExecutionTimings import track_timing

TOP_ENV_FILE=os.getenv("TOP_ENV_FILE")

log_level = os.getenv("LOGS_LEVEL", "INFO")
log_format = os.getenv("LOGS_FORMAT")
log_dir = os.getenv("LOG_DIR", "/logs")

os.makedirs(log_dir, exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(log_level)
file_handler = logging.FileHandler(f"{log_dir}/server_main.log")
formatter = logging.Formatter(log_format)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

server = fastapi.FastAPI(title="Book Club Server", version="0.0.1")


# CORS configuration for frontend on port 8000
server.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://bookclub-app:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@server.on_event("startup")
@track_timing(namespace="startup")
async def startup():
    server.state.started_at = time.time()
    server.state.app_env = os.getenv("APP_ENV", "local")
    logger.info("Server started")

@server.on_event("shutdown")
@track_timing(namespace="shutdown")
#TODO: The metrics of the end are not being collected. I think its becouse the server is dying before the metrics are collected.
async def shutdown():
    logger.info("Server shutdown")
    pass

# ----- Metadata -----

@server.get("/health", tags=["health"])
async def health() -> dict:
    started = getattr(server.state, "started_at", None)
    uptime = round(time.time() - started, 3) if started else 0.0
    return {"status": "ok", "uptime_s": uptime}

@server.get("/metrics", tags=["metrics"])
async def metrics():
    if os.getenv("PROMETHEUS_MULTIPROC_DIR"):
        # Multiprocess mode: aggregate metrics from all workers
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        platform_collector.PlatformCollector(registry=registry)
        data = generate_latest(registry)
    else:
        # Single-process mode: use the default registry where track_timing registers metrics
        data = generate_latest(REGISTRY)
    return Response(data, media_type=CONTENT_TYPE_LATEST)

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
