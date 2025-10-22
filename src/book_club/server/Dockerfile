# syntax=docker/dockerfile:1
# Use Microsoft Container Registry to avoid Docker Hub TLS issues behind corporate proxies
FROM mcr.microsoft.com/devcontainers/python:3.11

WORKDIR /server
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

EXPOSE ${PORT}
CMD ["sh", "-lc", "mkdir -p \"${PROMETHEUS_MULTIPROC_DIR}\"; rm -rf \"${PROMETHEUS_MULTIPROC_DIR}\"/* 2>/dev/null || true; exec gunicorn -k uvicorn.workers.UvicornWorker -w ${GUNICORN_WORKERS} -b ${HOST}:${PORT} ${START_POINT}"]