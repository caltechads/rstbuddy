"""
Make-MDC command for rstbuddy.

Implements the main RST to MDC conversion functionality.
"""

import sys
from pathlib import Path

import click

from ..exc import ConfigurationError, ConversionError, NoPandocError
from ..services.pandoc_converter import (
    PandocConverter,
    get_pandoc_installation_instructions,
)
from ..services.summary_generation import SummaryGenerationService
from .cli import cli


@cli.command("summarize")
@click.argument("rst_file", type=click.Path(exists=True, path_type=Path))
@click.pass_context
def summarize_rst(ctx: click.Context, rst_file: Path) -> None:
    """
    Summarize an RST file by asking an AI assistant.
    """
    context = ctx.obj

    if not context.settings or not context.utils:
        click.echo("Context not properly initialized", err=True)
        sys.exit(1)

    # Initialize pandoc converter
    try:
        converter = PandocConverter()
        context.utils.print_info("Using enhanced pandoc converter")
    except NoPandocError as e:
        context.utils.print_error(f"Pandoc converter initialization failed: {e}")
        instructions = get_pandoc_installation_instructions()
        context.utils.print_error(instructions)
        sys.exit(1)

    # Read the RST file
    context.utils.print_header("Step 1: Reading RST file")
    with rst_file.open(encoding="utf-8") as f:
        rst_content = f.read()

    context.utils.print_success(f"Successfully read {len(rst_content)} characters")

    context.utils.print_header("Step 4: Converting RST to Markdown")
    with context.utils.show_progress("Converting content...") as progress:
        task = progress.add_task("Converting content...", total=None)
        try:
            md_content = converter.convert_rst_to_md(rst_content)
        except ConversionError as e:
            context.utils.print_error(f"Conversion failed: {e}")
            sys.exit(1)
        progress.update(task, completed=True)

    context.utils.print_success("Successfully converted content to Markdown")

    context.utils.print_header("Step 3: Generating summary")
    summary_service = SummaryGenerationService(context.settings, context.console)
    try:
        # Generate summary for the RST content
        summary = summary_service.generate_summary(md_content)
    except ConfigurationError as e:
        context.utils.print_warning(f"Summary generation failed: {e}")

    # Extract metadata for documentation generation
    context.utils.print_header("Step 4: Displaying summary")
    context.console.print()
    context.console.print(summary)
