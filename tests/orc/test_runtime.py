from __future__ import annotations

import io
import logging

import pytest
from rich.console import Console

from book_club.orc.runtime import OrcRuntime, make_console


def _runtime() -> tuple[OrcRuntime, io.StringIO]:
    output = io.StringIO()
    console = Console(file=output, force_terminal=True, width=120)
    logger = logging.getLogger("test.orc.runtime")
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    return (
        OrcRuntime(
            console=console,
            trace_enabled=False,
            verbose=False,
            quiet=False,
            logger=logger,
        ),
        output,
    )


def test_action_emits_start_and_success_signals() -> None:
    runtime, output = _runtime()

    with runtime.action("test.action", "Doing useful work"):
        pass

    rendered = output.getvalue()
    assert "Doing useful work" in rendered
    assert "→" in rendered
    assert "✓" in rendered


def test_action_emits_failure_signal_and_reraises() -> None:
    runtime, output = _runtime()

    with pytest.raises(RuntimeError, match="boom"):
        with runtime.action("test.failure", "Doing risky work"):
            raise RuntimeError("boom")

    rendered = output.getvalue()
    assert "Doing risky work failed: boom" in rendered
    assert "✗" in rendered


def test_quiet_runtime_still_prints_warnings() -> None:
    runtime, output = _runtime()
    quiet_runtime = OrcRuntime(
        console=runtime.console,
        trace_enabled=False,
        verbose=False,
        quiet=True,
        logger=runtime.logger,
    )

    quiet_runtime.emit("info", "test.info", "hidden")
    quiet_runtime.emit("warning", "test.warning", "visible")

    rendered = output.getvalue()
    assert "hidden" not in rendered
    assert "visible" in rendered


def test_no_color_console_disables_colour_system() -> None:
    console = make_console(False)
    assert console.color_system is None
