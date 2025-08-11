"""
CLI command to clean a single RST file using the RSTCleaner service.

The command converts Markdown constructs to valid reStructuredText, normalizes
headings, fixes list spacing, converts fenced code blocks, adjusts inline code
spans, removes stray backtick fences, and optionally validates external links.
"""

from __future__ import annotations

from pathlib import Path

import click
from rich.table import Table

from ..services.rst_cleaner import RSTCleaner
from .cli import cli
from .utils import console


@cli.command("fix")
@click.argument(
    "rst_file", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--dry-run", is_flag=True, help="Show changes without writing the file")
def fix_rst(rst_file: Path, dry_run: bool) -> None:
    """
    Clean a single RST file in place (with a timestamped backup unless --dry-run).

    Args:
        rst_file: Path to the .rst file to clean
        dry_run: If True, show a summary without modifying the file

    """
    cleaner = RSTCleaner()
    original_path: Path = rst_file

    cleaned_report = cleaner.clean_file(original_path, dry_run=dry_run)

    # Output summary using rich table
    table = Table(title="RST Clean Summary")
    table.add_column("File")
    table.add_column("Headings")
    table.add_column("MD Headings")
    table.add_column("Lists")
    table.add_column("Code Blocks")
    table.add_column("Inline Code")
    table.add_column("Stray Fences")

    table.add_row(
        str(original_path),
        str(cleaned_report.headings_fixed),
        str(cleaned_report.md_headings_converted),
        str(cleaned_report.lists_spaced),
        str(cleaned_report.code_blocks_converted),
        str(cleaned_report.inline_code_fixed),
        str(cleaned_report.stray_fences_removed),
    )

    console.print(table)
