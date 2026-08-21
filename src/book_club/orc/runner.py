from __future__ import annotations

import os
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from book_club.orc.runtime import OrcRuntime


@dataclass(frozen=True)
class CommandResult:
    args: tuple[str, ...]
    returncode: int
    stdout: str = ""
    stderr: str = ""


class CommandFailed(RuntimeError):
    def __init__(self, result: CommandResult) -> None:
        rendered = " ".join(result.args)
        detail = result.stderr.strip() or result.stdout.strip()
        suffix = f": {detail}" if detail else ""
        super().__init__(f"Command failed ({result.returncode}): {rendered}{suffix}")
        self.result = result


def run(
    runtime: OrcRuntime,
    action: str,
    description: str,
    args: Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
    cwd: str | Path | None = None,
    capture: bool = False,
    check: bool = True,
) -> CommandResult:
    """Run an external command behind an ORC action boundary."""
    command = tuple(str(part) for part in args)
    effective_env = os.environ.copy()
    if env:
        effective_env.update(env)

    if runtime.verbose:
        runtime.emit("info", action, f"$ {' '.join(command)}")

    with runtime.action(action, description):
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=effective_env,
            text=True,
            capture_output=capture,
            check=False,
        )

        result = CommandResult(
            args=command,
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )
        if check and result.returncode != 0:
            raise CommandFailed(result)
        return result
