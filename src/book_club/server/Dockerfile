# syntax=docker/dockerfile:1
# Use Microsoft Container Registry to avoid Docker Hub TLS issues behind corporate proxies
FROM mcr.microsoft.com/devcontainers/python:3.11

WORKDIR /server
COPY server/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ .
COPY observability/ ./observability

EXPOSE ${PORT}
CMD ["sh", "-lc", "mkdir -p \"${PROMETHEUS_MULTIPROC_DIR}\"; rm -rf \"${PROMETHEUS_MULTIPROC_DIR}\"/* 2>/dev/null || true; exec gunicorn -k uvicorn.workers.UvicornWorker -w ${GUNICORN_WORKERS:-4} -b 0.0.0.0:${PORT:-8010} ${START_POINT:-server_main:server}"]