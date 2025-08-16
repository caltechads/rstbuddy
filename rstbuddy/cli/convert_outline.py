"""
CLI command for converting markdown outlines to RST structure.

This module provides the `convert-outline` command for the rstbuddy CLI.
It orchestrates the complete process of converting markdown outlines
to RST documentation structure through validation, parsing, and conversion.
"""

from __future__ import annotations

from pathlib import Path

import click

from ..exc import FileError
from ..services.outline_converter import OutlineConverter
from ..services.outline_parser import OutlineParser
from ..services.outline_validator import OutlineValidator
from .cli import cli


@cli.command("convert-outline")
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
def convert_outline(
    ctx: click.Context,
    markdown_file: Path,
    force: bool,
    output_dir: Path | None,
    dry_run: bool,
) -> None:
    """
    Convert a markdown outline to RST file structure.

    This command processes markdown files with a clear heading hierarchy
    and converts them into a complete RST documentation structure. The
    process involves three main steps: validation, parsing, and conversion.

    The markdown file must have a clear heading hierarchy:
    - H1: Book title
    - H2: Chapters (Prologue, Introduction, Chapter X:, Appendix X:)
    - H3: Sections (1.1, 2.3.1, etc.)

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
        The conversion process:
        1. Validates markdown structure and heading hierarchy
        2. Parses the outline into a structured representation
        3. Converts to RST files with proper Sphinx formatting
        4. Creates timestamped backups when force=True

        When dry_run is True, no files are actually created or modified.

    """
    utils = ctx.obj.get("utils")
    print_info = utils.print_info
    print_error = utils.print_error
    print_success = utils.print_success
    print_header_func = utils.print_header

    print_header_func("Converting Markdown Outline to RST Structure")
    print_info(f"Input file: {markdown_file}")

    # Step 1: Validate markdown
    print_info("Step 1: Validating markdown structure...")

    try:
        validator = OutlineValidator()
        validation_result = validator.validate_file(markdown_file)
    except FileError as e:
        print_error(f"Failed to validate markdown: {e!s}")
        raise click.ClickException(str(e)) from e

    if not validation_result.is_valid:
        print_error("Markdown validation failed:")
        for error in validation_result.errors:
            print_error(f"  Line {error.line_number}: {error.message}")
        msg = "Markdown validation failed. Please fix the errors above."
        raise click.ClickException(msg)

    if validation_result.warnings:
        print_info("Warnings found (non-blocking):")
        for warning in validation_result.warnings:
            print_info(f"  Line {warning.line_number}: {warning.message}")

    print_success("Markdown validation passed!")

    # Step 2: Parse outline structure
    print_info("Step 2: Parsing outline structure...")

    try:
        parser = OutlineParser()
        outline = parser.parse_file(markdown_file, output_dir)
    except Exception as e:
        print_error(f"Failed to parse outline: {e!s}")
        raise click.ClickException(str(e)) from e

    print_info(f"  Chapters: {len(outline.chapters)}")
    total_sections = sum(len(chapter.sections) for chapter in outline.chapters)
    print_info(f"  Sections: {total_sections}")
    print_info(f"  Output directory: {outline.output_dir}")

    # Step 3: Convert to RST structure
    print_info("Step 3: Converting to RST structure...")
    try:
        converter = OutlineConverter(force=force, dry_run=dry_run)
        converter.convert_outline(outline)
    except Exception as e:
        print_error(f"Failed to convert to RST structure: {e!s}")
        raise click.ClickException(str(e)) from e

    if dry_run:
        print_success("Dry run completed!")
    else:
        print_success("Conversion completed successfully!")
        print_info(f"RST files generated in: {outline.output_dir}")

        # Show generated structure
        print_info("Generated structure:")
        _show_generated_structure(outline.output_dir, print_info)


def _show_generated_structure(output_dir: Path, print_info_func) -> None:
    """
    Display the generated file structure.

    Recursively traverses the output directory and displays a tree-like
    representation of all generated files and directories. This provides
    users with a clear overview of what was created.

    Args:
        output_dir: Root directory to display structure for
        print_info_func: Function to use for printing information

    Raises:
        OSError: If directory traversal fails

    Note:
        The tree display uses ASCII characters to create a visual
        hierarchy showing the relationship between files and directories.

    """

    def _print_tree(path: Path, prefix: str = "", is_last: bool = True) -> str:
        """
        Recursively build directory tree string.

        Args:
            path: Current path to print
            prefix: Prefix string for indentation
            is_last: Whether this is the last item in its parent

        Returns:
            String representation of the directory tree

        Raises:
            OSError: If directory listing or file operations fail

        """
        result = ""
        if path.is_file():
            result += f"{prefix}{'└── ' if is_last else '├── '}{path.name}\n"
        elif path.is_dir():
            result += f"{prefix}{'└── ' if is_last else '├── '}{path.name}/\n"
            items = sorted(path.iterdir(), key=lambda item: (item.is_file(), item.name))
            for i, item in enumerate(items):
                result += _print_tree(
                    item, prefix + ("    " if is_last else "│   "), i == len(items) - 1
                )
        return result

    # Build the complete tree structure
    tree_structure = _print_tree(output_dir)

    # Display the entire tree in a single call
    print_info_func(tree_structure.rstrip())
