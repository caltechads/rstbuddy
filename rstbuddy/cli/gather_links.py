from __future__ import annotations

from pathlib import Path

import click

from ..services.gather_links import RSTLinkGatherer
from .cli import cli


@cli.command("gather-links")
@click.argument(
    "root",
    required=False,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be done without making changes",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Show detailed progress and operations",
)
@click.pass_context
def gather_links(
    ctx: click.Context,
    root: Path | None,
    dry_run: bool,
    verbose: bool,
) -> None:
    """
    Consolidate external hyperlinks from RST documentation into a centralized
    ``_links.rst`` file.

    This command:

    1. Recursively scans RST files for external hyperlinks
    2. Generates unique labels for each URL
    3. Creates/updates _links.rst with consolidated links
    4. Replaces inline links with label references
    5. Updates conf.py with rst_epilog configuration

    ROOT defaults to the documentation directory from settings.
    """
    # Get documentation directory from context or use default
    if root:
        documentation_dir = root
    else:
        settings = ctx.obj.get("settings")
        if not settings:
            click.echo("Error: No settings available")
            raise click.Abort
        documentation_dir = Path(settings.documentation_dir)

    if verbose:
        click.echo(f"Using documentation directory: {documentation_dir}")

    # Validate documentation directory
    if not documentation_dir.exists():
        click.echo(
            f"Error: Documentation directory '{documentation_dir}' does not exist"
        )
        raise click.Abort

    if not documentation_dir.is_dir():
        click.echo(f"Error: '{documentation_dir}' is not a directory")
        raise click.Abort

    # Create and run the link gatherer
    gatherer = RSTLinkGatherer(documentation_dir)

    if dry_run:
        click.echo("=== DRY RUN MODE ===")
        click.echo("No files will be modified")
        click.echo()

    # Run the gathering process
    success = gatherer.run(dry_run=dry_run)

    if success:
        if dry_run:
            click.echo("Dry run completed successfully")
        else:
            click.echo("Link gathering completed successfully")
    else:
        click.echo("Link gathering failed")
        raise click.Abort
