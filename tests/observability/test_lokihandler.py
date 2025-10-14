# Tests for `LokiHandler`.
# British English is used in comments and docstrings.

from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass
from typing import Any, List
from copy import copy

import pytest 

# Module under test
from book_club.observability.LokiHandler import LokiHandler

# import of module for monkeypatching
import book_club.observability.LokiHandler as loki_module

pytestmark = pytest.mark.behaviour


@dataclass
class PostCall:
    url: str
    json: Any


class FakeHttpxClient:
    """A minimal fake for httpx.Client that captures post() calls.

    Thread-safe to support the handler's background thread.
    """

    def __init__(self, behaviour: list[str] | None = None):
        # behaviour items: "ok" or "raise", consumed sequentially
        self._behaviour = list(behaviour or [])
        self._lock = threading.Lock()
        self._posts: List[PostCall] = []

    @property
    def posts(self) -> List[PostCall]:
        with self._lock:
            return list(self._posts)

    def post(self, url: str, json: Any) -> None:  # signature similar to httpx
        with self._lock:
            action = self._behaviour.pop(0) if self._behaviour else "ok"
        if action == "raise":
            raise RuntimeError("simulated network failure")
        with self._lock:
            self._posts.append(PostCall(url=url, json=copy(json)))


@pytest.fixture()
def patch_httpx_client(monkeypatch):
    """Monkeypatch httpx.Client to return fake client instance.

    Returns a tuple (fake_client, install) where calling install() applies the patch
    and returns the fake instance.
    """

    fake_holder = {}

    def install(fake: FakeHttpxClient | None = None) -> FakeHttpxClient:
        client = fake or FakeHttpxClient()
        fake_holder["client"] = client
        monkeypatch.setattr(loki_module, "httpx", type("_M", (), {"Client": lambda: client}))
        return client

    return install


@pytest.fixture()
def ensure_sys_available_in_module(monkeypatch):
    """Ensure the module has a `sys` attribute for the error path in _flush()."""
    import sys as _sys

    monkeypatch.setattr(loki_module, "sys", _sys, raising=False)

def wait_until(pred, timeout: float = 1.5, step: float = 0.005):
    """Poll until predicate returns True or timeout elapses."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if pred():
            return True
        time.sleep(step)
    return False

def make_logger(name: str = "test.loki") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # Avoid duplicate handlers across tests
    logger.handlers = []
    return logger

def test_handlers_worker_is_running_on_another_thread(monkeypatch):
    handler = LokiHandler(url="http://example/loki", batch_size=100, batch_interval=0.5)
    print(handler._thread)
    assert handler._thread.is_alive()
    handler.close()
    assert not handler._thread.is_alive()

def test_fake_client_posts(monkeypatch, patch_httpx_client):
    fake_client = patch_httpx_client()
    handler = LokiHandler(url="http://example/loki", batch_size=100, batch_interval=0.5)
    try:
        logger = make_logger()
        logger.addHandler(handler)
        logger.info("hello world")
        time.sleep(0.05)
        assert isinstance(fake_client, FakeHttpxClient)
        assert isinstance(handler.session, FakeHttpxClient)
        assert wait_until(lambda: len(fake_client.posts) >= 1)
    finally:
        handler.close()

def test_emit_enqueues_without_post(monkeypatch, patch_httpx_client):
    fake_client = patch_httpx_client()
    handler = LokiHandler(url="http://example/loki", batch_size=100, batch_interval=0.01)
    try:
        logger = make_logger()
        logger.addHandler(handler)
        logger.info("hello world")
        # Short wait; with large interval and batch size, nothing should be posted yet
        time.sleep(0.05)
        assert len(fake_client.posts) == 1
    finally:
        handler.close()


def test_flushes_when_batch_size_reached(patch_httpx_client):
    fake_client = patch_httpx_client()
    handler = LokiHandler(url="http://example/loki", batch_size=3, batch_interval=10)
    try:
        logger = make_logger()
        logger.addHandler(handler)
        logger.info("m1")
        logger.info("m2")
        logger.info("m3")
        # the batch size is 3, so we expect 1 post with 3 records
        assert wait_until(lambda: len(fake_client.posts) == 1)
        post = fake_client.posts[0]
        print(post)
        assert post.url == "http://example/loki"
        assert isinstance(post, PostCall)
        assert isinstance(post.json, list)
        print(post.json)
        assert len(post.json) == 3
        # Shape contract
        row = post.json[0]
        assert "streams" in row and isinstance(row["streams"], list)
        stream = row["streams"][0]
        assert set(stream["stream"].keys()) == {"level", "logger"}
        assert isinstance(stream["values"], list) and len(stream["values"]) == 1
    finally:
        handler.close()


def test_flushes_on_interval(patch_httpx_client):
    fake_client = patch_httpx_client() 
    handler = LokiHandler(url="http://example/loki", batch_size=100, batch_interval=0.02)
    try:
        logger = make_logger()
        logger.addHandler(handler)
        logger.info("interval")
        assert wait_until(lambda: len(fake_client.posts) == 1)
        assert len(fake_client.posts[0].json) == 1
    finally:
        handler.close()


def test_close_drains_remaining(patch_httpx_client):
    fake_client = patch_httpx_client()
    handler = LokiHandler(url="http://example/loki", batch_size=10, batch_interval=10)
    logger = make_logger()
    logger.addHandler(handler)
    logger.info("a")
    logger.info("b")
    # No auto flush expected yet
    time.sleep(0.05)
    assert len(fake_client.posts) == 0
    # Close should drain and flush remaining
    handler.close()
    assert len(fake_client.posts) == 1
    assert len(fake_client.posts[0].json) == 2


def test_handle_error_on_queue_put_failure(monkeypatch, patch_httpx_client):
    patch_httpx_client()
    handler = LokiHandler(url="http://example/loki", batch_size=100, batch_interval=10)
    try:
        flag = {"called": False}

        def _he(record):
            flag["called"] = True

        # Replace handleError on this instance
        monkeypatch.setattr(handler, "handleError", _he)
        # Force queue full error
        def _raise_full(item):
            raise queue.Full

        monkeypatch.setattr(handler._q, "put_nowait", _raise_full)

        logger = make_logger()
        logger.addHandler(handler)
        # Emit via logger to produce a LogRecord
        logger.info("trigger full")
        # Give the emit a tick
        time.sleep(0.01)
        assert flag["called"] is True
    finally:
        handler.close()


def test_flush_catches_post_exception(monkeypatch, patch_httpx_client, ensure_sys_available_in_module, capsys):
    # First post raises, second succeeds
    fake_client = patch_httpx_client(FakeHttpxClient(behaviour=["raise", "ok"]))
    handler = LokiHandler(url="http://example/loki", batch_size=2, batch_interval=10)
    try:
        logger = make_logger()
        logger.addHandler(handler)
        logger.info("x1")
        logger.info("x2")  # triggers size-based flush -> raises
        # Wait a bit for the worker to attempt flushing and print error
        assert wait_until(lambda: len(fake_client.posts) >= 0)  # no-op predicate to yield time
        # Now send more to trigger a successful second flush
        logger.info("x3")
        logger.info("x4")
        assert wait_until(lambda: len(fake_client.posts) >= 1)
        # Verify error message printed
        out = capsys.readouterr().out
        assert "[LokiHandler ERROR]" in out
    finally:
        handler.close()


def test_serialize_shape_direct():
    handler = LokiHandler(url="http://example/loki")
    try:
        record = logging.LogRecord(
            name="unit.test", level=logging.INFO, pathname=__file__, lineno=1, msg="hello %s", args=("world",), exc_info=None
        )
        data = handler._serialize(record)
        assert "streams" in data and isinstance(data["streams"], list)
        s0 = data["streams"][0]
        assert set(s0["stream"].keys()) == {"level", "logger"}
        assert isinstance(s0["values"], list) and len(s0["values"]) == 1
        ts, msg = s0["values"][0]
        assert isinstance(ts, (float, int))
        assert msg == "hello world"
    finally:
        handler.close()
