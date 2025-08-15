from __future__ import annotations

import json
from pathlib import Path

import click
from rich.table import Table

from ..services.rst_link_checker import RSTLinkChecker
from .cli import cli
from .utils import console


@cli.command("check-links")
@click.argument(
    "root",
    required=False,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--timeout",
    type=int,
    default=5,
    show_default=True,
    help="Per-link timeout (seconds)",
)
@click.option(
    "--max-workers",
    type=int,
    default=8,
    show_default=True,
    help="Max workers for link checks",
)
@click.option(
    "--no-check-robots",
    is_flag=True,
    default=False,
    help="Disable robots.txt checks for external links",
)
@click.option(
    "--user-agent",
    type=str,
    default="rstbuddy-linkcheck/1.0",
    show_default=True,
    help="User-Agent to use for HTTP validation and robots.txt",
)
@click.pass_context
def check_links(  # noqa: PLR0913
    ctx: click.Context,
    root: Path | None,
    timeout: int,
    max_workers: int,
    no_check_robots: bool,
    user_agent: str,
) -> None:
    """
    Recursively scan RST files under ROOT (default:
    :py:attr:`~rstbuddy.settings.Settings.documentation_dir`) and report broken
    links.

    Broken links include:

    - External http(s) links that fail validation (non-200 or transport error)
    - :ref: roles whose labels are not defined via explicit ``.. _label:``
    - :doc: roles whose target .rst file cannot be resolved
    - Custom label references in the format `Label`_ that don't have corresponding
      definitions in the format ``.. Label: URL``

    Output format is controlled by the top-level --output option: json, table, or text.

    """
    base = root or Path("doc")
    checker = RSTLinkChecker(base)
    broken = checker.check(
        timeout=timeout,
        max_workers=max_workers,
        check_robots=not no_check_robots,
        user_agent=user_agent,
    )

    # Determine output format from CLI context settings
    output_format = "table"
    context = ctx.obj
    if context and "output" in context:
        output_format = context["output"]

    if output_format == "json":
        data = checker.render_json(broken)
        click.echo(json.dumps(data, indent=2))
    else:
        # Pretty table with rich (for table and text formats)
        table = Table(title="Broken RST Links")
        table.add_column("File")
        table.add_column("Line")
        table.add_column("Link")
        for occ in broken:
            table.add_row(
                checker.relative_to_doc_source(occ.file_path),
                str(occ.line_number),
                occ.link_text,
            )
        console.print(table)

    # Non-zero exit if any broken links
    if broken:
        raise SystemExit(1)
