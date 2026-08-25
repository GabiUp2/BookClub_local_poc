from __future__ import annotations

import io

from book_club.orc.banner import ORC_BANNER
from book_club.orc.help import render_root_banner, wants_root_help


def test_bare_orc_wants_root_help() -> None:
    assert wants_root_help([])


def test_root_help_wants_banner() -> None:
    assert wants_root_help(["--help"])
    assert wants_root_help(["--no-color", "--help"])


def test_subcommand_help_does_not_want_banner() -> None:
    assert not wants_root_help(["dev", "--help"])
    assert not wants_root_help(["--no-color", "obs", "--help"])


def test_banner_uses_configured_orc_art_without_ansi_when_color_is_disabled() -> None:
    output = io.StringIO()

    render_root_banner(["--no-color", "--help"], file=output)

    rendered = output.getvalue()
    assert "⣿⣿⣿⣿" in rendered
    assert ORC_BANNER.splitlines()[6] in rendered
    assert "ORC-HESTRATOR" in rendered
    assert "\x1b[" not in rendered
