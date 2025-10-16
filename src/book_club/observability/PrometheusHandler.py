import httpx
import queue
import threading
import time
import sys
from typing import Literal

from logging import Handler, LogRecord


MetricType = Literal["counter", "gauge", "histogram", "summary"]


class PrometheusHandler(Handler):
    """
    Handler that batches log records as Prometheus metrics and pushes them
    to a Prometheus Pushgateway endpoint.

    Expected LogRecord extra fields:
    - metric_name: str (required)
    - metric_value: float (required)
    - metric_type: MetricType (default: "counter")
    - metric_labels: Dict[str, str] (optional)
    """

    def __init__(
        self,
        url: str,
        job: str = "python_app",
        batch_size: int = 10,
        batch_interval: float = 0.01,
        max_queue: int = 10000,
    ):
        super().__init__()
        self.url = url
        self.job = job
        self.session = httpx.Client()
        self.batch_size = batch_size
        self.batch_interval = batch_interval
        self.max_queue = max_queue

        # Threading for queue handling, needs to be first as close() implementation calls _stop and _thread
        self._q = queue.Queue(maxsize=max_queue)
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._worker, name="PrometheusHandler", daemon=True
        )
        self._last_flush = time.monotonic()
        self._thread.start()

    def emit(self, record: LogRecord) -> None:
        try:
            self._q.put_nowait(self._serialize(record))
        except queue.Full:
            self.handleError(record)

    def close(self) -> None:
        print("[PrometheusHandler] Closing gracefully")
        self.flush()
        self._stop.set()
        self._thread.join(timeout=0.1)
        super().close()

    def _worker(self):
        batch: list[str] = []
        while not self._stop.is_set():
            remaining = self.batch_interval - (time.monotonic() - self._last_flush)
            timeout = min(0.1, max(0, remaining))
            try:
                item = self._q.get(timeout=timeout)
                batch.append(item)
                if len(batch) >= self.batch_size:
                    print("[PrometheusHandler] Flushing batch", len(batch), "metrics")
                    self._flush(batch)
                    batch.clear()
                    self._last_flush = time.monotonic()
            except queue.Empty:
                now = time.monotonic()
                if batch and (
                    self._stop.is_set()
                    or (now - self._last_flush) >= self.batch_interval
                ):
                    self._flush(batch)
                    batch.clear()
                    self._last_flush = now
                # otherwise, continue waiting without flushing or resetting last_flush
        # Final drain
        try:
            while True:
                batch.append(self._q.get_nowait())
                if len(batch) >= self.batch_size:
                    self._flush(batch)
                    batch.clear()
        except queue.Empty:
            print("[PrometheusHandler] Queue is empty")
            pass
        finally:
            if batch:
                self._flush(batch)

    def _serialize(self, record: LogRecord) -> str:
        """
        Serialize LogRecord to Prometheus text exposition format.
        Expects extra fields: metric_name, metric_value, metric_type, metric_labels
        """
        metric_name = getattr(record, "metric_name", None)
        metric_value = getattr(record, "metric_value", None)
        metric_type = getattr(record, "metric_type", "counter")
        metric_labels = getattr(record, "metric_labels", {})

        if not metric_name or metric_value is None:
            # Fallback: create a metric from log level
            metric_name = f"log_{record.levelname.lower()}_total"
            metric_value = 1
            metric_type = "counter"
            metric_labels = {
                "logger": record.name,
                "level": record.levelname,
            }

        # Build label string
        label_str = ""
        if metric_labels:
            labels = ",".join(f'{k}="{v}"' for k, v in metric_labels.items())
            label_str = f"{{{labels}}}"

        # Prometheus exposition format
        lines = []
        lines.append(f"# TYPE {metric_name} {metric_type}")
        lines.append(f"{metric_name}{label_str} {metric_value}")
        return "\n".join(lines)

    def _flush(self, rows: list[str]):
        """
        Push metrics to Prometheus Pushgateway using text exposition format.
        """
        try:
            # Combine all metrics into single payload
            payload = "\n".join(rows)

            # Push to Pushgateway: POST /metrics/job/<job_name>
            endpoint = f"{self.url}/metrics/job/{self.job}"
            response = self.session.post(
                endpoint,
                content=payload,
                headers={"Content-Type": "text/plain; version=0.0.4"},
            )
            response.raise_for_status()
        except Exception:
            print(
                f"[PrometheusHandler ERROR] Failed to flush {len(rows)} metrics; Exception: {sys.exc_info()}"
            )
            pass

    def _debug_flush(self, rows: list[str]):
        print(
            f"[PrometheusHandler DEBUG] would flush {len(rows)} metrics; first metric:\n{rows[0] if rows else None}"
        )

    def flush(self):
        # Nothing synchronous to do; worker handles timed flush
        print("[PrometheusHandler] Synchronous flush called")
        return
