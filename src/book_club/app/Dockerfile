# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

CMD ["sh", "-lc", "rm -rf \"${PROMETHEUS_MULTIPROC_DIR}\"/* 2>/dev/null || true; exec gunicorn -k uvicorn.workers.UvicornWorker -w ${GUNICORN_WORKERS} -b ${HOST}:${PORT} ${START_POINT}"]