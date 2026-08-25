from __future__ import annotations

import sys
from collections.abc import Sequence

from rich.console import Console
from rich.text import Text

from book_club.orc.banner import ORC_BANNER, ORC_TAGLINE


ROOT_COMMANDS = {
    "env",
    "dev",
    "build",
    "test-metrics",
    "compose",
    "obs",
    "maintenance",
    "acr",
}


def wants_root_help(argv: Sequence[str]) -> bool:
    """Return whether this invocation will render the root help screen."""
    if not argv:
        return True

    help_requested = "--help" in argv or "-h" in argv
    subcommand_selected = any(argument in ROOT_COMMANDS for argument in argv)
    return help_requested and not subcommand_selected


def render_root_banner(argv: Sequence[str], *, file=None) -> None:  # type: ignore[no-untyped-def]
    """Render ORC's banner using the same colour intent as the root CLI flags."""
    output = file or sys.stdout
    if "--color" in argv:
        console = Console(file=output, force_terminal=True, color_system="auto")
    elif "--no-color" in argv:
        console = Console(
            file=output,
            force_terminal=False,
            color_system=None,
            no_color=True,
        )
    else:
        console = Console(file=output, color_system="auto")

    console.print()
    console.print(Text(ORC_BANNER, style="bold green"), soft_wrap=True)
    console.print(Text(ORC_TAGLINE, style="bold"), justify="center")
    console.print()
