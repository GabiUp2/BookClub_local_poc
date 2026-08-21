from __future__ import annotations

import io
import logging
import subprocess

import pytest
from rich.console import Console

from book_club.orc.runner import CommandFailed, run
from book_club.orc.runtime import OrcRuntime


def _runtime() -> OrcRuntime:
    logger = logging.getLogger("test.orc.runner")
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    return OrcRuntime(
        console=Console(file=io.StringIO(), force_terminal=False),
        trace_enabled=False,
        verbose=False,
        quiet=False,
        logger=logger,
    )


def test_run_passes_argument_vector_without_shell(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(args, **kwargs):  # type: ignore[no-untyped-def]
        captured["args"] = args
        captured.update(kwargs)
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = run(
        _runtime(),
        "test.command",
        "Running command",
        ["printf", "%s", "hello world"],
        capture=True,
    )

    assert captured["args"] == ("printf", "%s", "hello world")
    assert captured["capture_output"] is True
    assert captured["check"] is False
    assert result.stdout == "ok"


def test_run_maps_nonzero_exit_to_command_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(args, **kwargs):  # type: ignore[no-untyped-def]
        return subprocess.CompletedProcess(args=args, returncode=7, stdout="", stderr="bad thing")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(CommandFailed, match="bad thing"):
        run(_runtime(), "test.command", "Running command", ["false"])
