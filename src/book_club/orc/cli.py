from __future__ import annotations

import sys

from book_club.orc.help import render_root_banner, wants_root_help
from book_club.orc.main import entrypoint as typer_entrypoint


def entrypoint() -> None:
    """Console-script entrypoint with ORC-branded root help."""
    argv = sys.argv[1:]
    if wants_root_help(argv):
        render_root_banner(argv)
    typer_entrypoint()
