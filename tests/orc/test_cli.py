from __future__ import annotations

from typer.testing import CliRunner

from book_club.orc.main import app


runner = CliRunner()


def test_root_help_exposes_orchestration_categories() -> None:
    result = runner.invoke(app, ["--no-color", "--help"])

    assert result.exit_code == 0
    for command in (
        "env",
        "dev",
        "build",
        "test-metrics",
        "compose",
        "obs",
        "maintenance",
        "acr",
    ):
        assert command in result.stdout


def test_dev_help_exposes_session_setup() -> None:
    result = runner.invoke(app, ["--no-color", "dev", "--help"])

    assert result.exit_code == 0
    assert "session" in result.stdout


def test_acr_list_exposes_orchestration_decision() -> None:
    result = runner.invoke(app, ["--no-color", "acr", "list"])

    assert result.exit_code == 0
    assert "ACR-0001" in result.stdout
    assert "Python ORC" in result.stdout
