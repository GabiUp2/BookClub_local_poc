from __future__ import annotations

import sys

from rich.console import Console
from rich.text import Text
from typer.core import TyperGroup

from book_club.orc.banner import ORC_BANNER, ORC_TAGLINE


class OrcGroup(TyperGroup):
    """Root Typer group that prepends ORC's terminal identity to help output."""

    def format_help(self, ctx, formatter) -> None:  # type: ignore[no-untyped-def]
        color = ctx.params.get("color")
        if color is True:
            console = Console(file=sys.stdout, force_terminal=True, color_system="auto")
        elif color is False:
            console = Console(
                file=sys.stdout,
                force_terminal=False,
                color_system=None,
                no_color=True,
            )
        else:
            console = Console(file=sys.stdout, color_system="auto")

        console.print()
        console.print(Text(ORC_BANNER, style="bold green"), soft_wrap=True)
        console.print(Text(ORC_TAGLINE, style="bold"), justify="center")
        console.print()

        super().format_help(ctx, formatter)
