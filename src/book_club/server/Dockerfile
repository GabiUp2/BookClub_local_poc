# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./
ENV PORT=8000
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
ENV GUNICORN_WORKERS=1
EXPOSE 8000
CMD ["sh", "-lc", "rm -rf \"$PROMETHEUS_MULTIPROC_DIR\"/* 2>/dev/null || true; exec gunicorn -k uvicorn.workers.UvicornWorker -w ${GUNICORN_WORKERS} -b 0.0.0.0:${PORT} server_main:app"]