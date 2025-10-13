import httpx
import queue
import threading
import time
import sys
from copy import copy

from logging import Handler, LogRecord


class LokiHandler(Handler):
    def __init__(self, url: str,
                 batch_size: int = 10,
                 batch_interval: float = 0.01,
                 max_queue: int = 10000,
    ):
        super().__init__()
        self.url = url
        self.session = httpx.Client()
        self.batch_size = batch_size
        self.batch_interval = batch_interval
        self.max_queue = max_queue
    
        # Threading for que handling, needs to be first as close() implementation - which is called even when authentication fails - calls _stop and _thread
        self._q = queue.Queue(maxsize=max_queue)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._worker, name="LokiHandler", daemon=True)
        self._last_flush = time.monotonic()
        self._thread.start()
    
    def emit(self, record: LogRecord) -> None:
        try:
            self._q.put_nowait(self._serialize(record))
        except queue.Full:
            self.handleError(record)
    
    def close(self) -> None:
        print("[LokiHandler] Closing gracefully")
        self.flush()
        self._stop.set()
        self._thread.join(timeout=0.1)
        super().close()
    
    def _worker(self):
        batch: list[dict] = []
        while not self._stop.is_set():
            remaining = self.batch_interval - (time.monotonic() - self._last_flush)
            timeout = min(0.1, max(0, remaining))
            try:
                item = self._q.get(timeout=timeout)
                batch.append(item)
                if len(batch) >= self.batch_size:
                    print("[LokiHandler] Flushing batch", batch)
                    self._flush(batch)
                    batch.clear()
                    self._last_flush = time.monotonic()
            except queue.Empty:
                now = time.monotonic()
                if batch and (self._stop.is_set() or (now - self._last_flush) >= self.batch_interval):
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
            print("[LokiHandler] Queue is empty") 
            pass
        finally:
            if batch:
                self._flush(batch)
    
    def _serialize(self, record: LogRecord) -> dict:
        return {
            "streams": [
                {
                    "stream": {
                        "level": record.levelname,
                        "logger": record.name,
                    },
                    "values": [
                        [record.created, record.getMessage()]
                    ]
                }
            ]
        }
    
    def _flush(self, rows: list[dict]):
        try:
            self.session.post(self.url, json=copy(rows))
        except Exception:
            print(f"[LokiHandler ERROR] Failed to flush {len(rows)} rows; Exception: {sys.exc_info()}")
            pass
    
    def _debug_flush(self, rows):
        print(f"[LokiHandler DEBUG] would flush {len(rows)} rows; first row:\n{rows[0] if rows else None}")
    
    def flush(self):
        # Nothing synchronous to do; worker handles timed flush
        print("[LokiHandler] Synchronous flush called")
        return
        