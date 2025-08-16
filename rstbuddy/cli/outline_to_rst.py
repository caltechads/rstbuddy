"""
CLI command for converting markdown outlines to RST structure using Marko.

This module provides the `outline-to-rst` command for the rstbuddy CLI.
It uses the Marko-based parser for more reliable markdown parsing.
"""

from __future__ import annotations

from pathlib import Path

import click

from ..exc import FileError
from ..services.marko_outline_parser import MarkoOutlineParser
from ..services.marko_outline_converter import MarkoOutlineConverter
from ..services.outline_validator import OutlineValidator
from .cli import cli


@cli.command("outline-to-rst")
@click.argument(
    "markdown_file",
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Force overwrite existing output directory (creates timestamped backup)",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    help="Custom output directory (default: uses RSTBUDDY_DOCUMENTATION_DIR setting)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be created without actually creating files",
)
@click.pass_context
def outline_to_rst(
    ctx: click.Context,
    markdown_file: Path,
    force: bool,
    output_dir: Path | None,
    dry_run: bool,
) -> None:
    """
    Convert a markdown outline to RST file structure using Marko parser.

    This command processes markdown files with a clear heading hierarchy
    and converts them into a complete RST documentation structure using
    Marko's AST-based parsing for improved reliability.

    The markdown file must have a clear heading hierarchy:
    - H1: Book title
    - H2: Chapters (Prologue, Introduction, Chapter X:, Appendix X:)
    - H3: Sections (1.1, 2.3, etc.) or content headings

    Creates a folder structure with proper RST files and toctree entries.

    Args:
        ctx: Click context object containing utilities and settings
        markdown_file: Path to the markdown file to convert
        force: If True, overwrite existing output directory with backups
        output_dir: Custom output directory (default: uses RSTBUDDY_DOCUMENTATION_DIR)
        dry_run: If True, show what would be created without creating files

    Raises:
        click.ClickException: If validation, parsing, or conversion fails

    Note:
        This command uses Marko's AST-based parsing for improved reliability
        compared to the regex-based approach. It provides the same output
        structure but with more robust content boundary detection.

        The conversion process:
        1. Validates markdown structure and heading hierarchy
        2. Parses the outline using Marko's AST
        3. Converts to RST files with proper Sphinx formatting
        4. Creates timestamped backups when force=True

        When dry_run is True, no files are actually created or modified.
    """
    utils = ctx.obj.get("utils")
    print_info = utils.print_info
    print_error = utils.print_error

    try:
        print_info(f"Converting outline: {markdown_file}")
        print_info("Using Marko-based parser for improved reliability")

        # Step 1: Validate the markdown structure
        print_info("Validating markdown structure...")
        validator = OutlineValidator()
        validation_result = validator.validate_file(markdown_file)

        if not validation_result.is_valid:
            print_error("Validation failed:")
            for error in validation_result.errors:
                print_error(f"  - {error}")
            raise click.ClickException("Markdown validation failed")

        print_info("✓ Markdown structure is valid")

        # Step 2: Parse the outline using Marko
        print_info("Parsing markdown outline with Marko...")
        parser = MarkoOutlineParser()
        outline = parser.parse_file(markdown_file, output_dir)

        print_info(f"✓ Parsed {len(outline.chapters)} chapters")
        total_sections = sum(len(chapter.sections) for chapter in outline.chapters)
        print_info(f"✓ Found {total_sections} total sections")

        # Step 3: Convert to RST structure
        print_info("Converting to RST structure...")

        # Use the new MarkoOutlineConverter directly
        converter = MarkoOutlineConverter(force=force, dry_run=dry_run)
        converter.convert_outline(outline)

        if dry_run:
            print_info("✓ Dry run completed - no files were created")
        else:
            print_info("✓ RST structure created successfully")

        # Step 4: Display the generated structure
        if not dry_run:
            print_info("\nGenerated structure:")
            # Show the generated structure using the converter's method
            converter.show_generated_structure(outline)

    except FileError as e:
        print_error(f"File operation failed: {e}")
        raise click.ClickException(f"File operation failed: {e}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        raise click.ClickException(f"Unexpected error: {e}")
