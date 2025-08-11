from __future__ import annotations

from typing import TYPE_CHECKING

from click.testing import CliRunner

from rstbuddy.cli.cli import cli

if TYPE_CHECKING:
    from pathlib import Path


def test_cli_fix_dry_run(tmp_path: Path):
    # prepare a small file with a markdown heading
    p = tmp_path / "sample.rst"
    p.write_text("# Title\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["fix", str(p), "--dry-run"])
    assert result.exit_code == 0
    # ensure file not changed
    assert p.read_text(encoding="utf-8") == "# Title\n"


def test_cli_fix_writes_backup(tmp_path: Path):
    p = tmp_path / "sample.rst"
    p.write_text("# Title\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["fix", str(p)])
    assert result.exit_code == 0
    # file changed
    assert "Title\n=====" in p.read_text(encoding="utf-8")
    # backup created
    backups = list(tmp_path.glob("sample.rst.*.bak"))
    assert len(backups) == 1
