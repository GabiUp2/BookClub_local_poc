# tests/server/test_preprocessing_server_main.py
from unittest.mock import MagicMock

import pytest

import book_club.preprocessing_server.server_main as server_main


def test_register_mark_dead_marks_process_when_multiprocess_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(server_main, "PROM_MULTIPROC_DIR", "/tmp/prom")
    mock_register = MagicMock()
    monkeypatch.setattr(server_main.atexit, "register", mock_register)
    mock_mark_dead = MagicMock()
    monkeypatch.setattr(server_main.multiprocess, "mark_process_dead", mock_mark_dead)
    monkeypatch.setattr(server_main.os, "getpid", lambda: 4242)

    server_main._register_mark_dead()

    mock_register.assert_called_once_with(mock_mark_dead, 4242)
    mock_mark_dead.assert_not_called()


def test_register_mark_dead_no_op_when_multiprocess_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(server_main, "PROM_MULTIPROC_DIR", None)
    mock_register = MagicMock()
    monkeypatch.setattr(server_main.atexit, "register", mock_register)
    mock_mark_dead = MagicMock()
    monkeypatch.setattr(server_main.multiprocess, "mark_process_dead", mock_mark_dead)

    server_main._register_mark_dead()

    mock_register.assert_not_called()
    mock_mark_dead.assert_not_called()
