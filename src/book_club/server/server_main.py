import os
import time
import datetime
import logging
import fastapi
from fastapi import Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry
from prometheus_client import multiprocess

logger = logging.getLogger(__name__)

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
async def startup():
    server.state.started_at = time.time()
    server.state.app_env = os.getenv("APP_ENV", "local")

@server.on_event("shutdown")
async def shutdown():
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
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        data = generate_latest(registry)
    else:
        data = generate_latest()
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