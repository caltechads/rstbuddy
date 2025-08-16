"""
RST utility functions for outline conversion.

This module contains utility functions extracted from the old OutlineConverter
that are still useful for the new Marko-based outline-to-rst approach.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from rstbuddy.exc import FileError
from rstbuddy.services.pandoc_converter import get_pandoc_installation_instructions

if TYPE_CHECKING:
    from ..models.outline import BookOutline, Chapter, Section


def content_is_different(file_path: Path, new_content: str) -> bool:
    """
    Check if new content differs from existing file content.

    Args:
        file_path: Path to the file to compare
        new_content: New content to compare against existing file

    Returns:
        True if content is different, False if identical

    Note:
        This method normalizes content by removing trailing whitespace
        and normalizing line endings before comparison.
    """
    if not file_path.exists():
        return True  # File doesn't exist, so it's "different"

    try:
        with file_path.open(encoding="utf-8") as f:
            existing_content = f.read()

        # Normalize both contents for comparison
        # Remove trailing whitespace and normalize line endings
        normalized_existing = normalize_content(existing_content)
        normalized_new = normalize_content(new_content)

    except (OSError, UnicodeDecodeError):
        # If we can't read the existing file, assume it's different
        return True
    else:
        return normalized_existing != normalized_new


def normalize_content(content: str) -> str:
    """
    Normalize content for comparison by removing trailing whitespace and
    normalizing line endings.

    Args:
        content: Content to normalize

    Returns:
        Normalized content with consistent formatting
    """
    # Split into lines, strip trailing whitespace, and rejoin
    lines = content.splitlines()
    normalized_lines = [line.rstrip() for line in lines]
    return "\n".join(normalized_lines)


def backup_file_if_exists(file_path: Path, dry_run: bool = False) -> None:
    """
    Backup a single file if it exists, using timestamped naming.

    Args:
        file_path: Path to the file to backup
        dry_run: If True, only show what would be done

    Note:
        Creates a backup with format: filename.timestamp.bak
    """
    if file_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # noqa: DTZ005
        backup_path = file_path.with_suffix(f".{timestamp}.bak")
        if dry_run:
            print(f"[DRY RUN] Would backup: {file_path} -> {backup_path}")
        else:
            shutil.copy2(file_path, backup_path)
            print(f"Backed up: {file_path} -> {backup_path}")


def backup_and_write_file(
    file_path: Path, new_content: str, force: bool = False, dry_run: bool = False
) -> None:
    """
    Backup existing file and write new content only if different.

    This method implements smart file writing that:
    1. Compares new content with existing content
    2. Only writes if content has actually changed
    3. Creates timestamped backups when force=True
    4. Handles dry-run mode appropriately

    Args:
        file_path: Path where the file should be written
        new_content: New content to write to the file
        force: If True, create backups of existing files
        dry_run: If True, only show what would be done

    Raises:
        OSError: If file operations fail (read, write, backup)
        UnicodeDecodeError: If existing file cannot be read with UTF-8 encoding
    """
    # Check if content is different
    if not content_is_different(file_path, new_content):
        print(f"Skipping {file_path} - content unchanged")
        return

    # Content is different, so backup and write
    if force and file_path.exists():
        if dry_run:
            print(f"[DRY RUN] Would backup: {file_path}")
        else:
            backup_file_if_exists(file_path, dry_run)

    # Write the new content
    if dry_run:
        print(f"[DRY RUN] Would update: {file_path}")
    else:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated: {file_path}")


def convert_content_to_rst(
    markdown_content: str, content_cache: dict[str, str] | None = None
) -> str:
    """
    Convert Markdown content to RST using Pandoc.

    This method converts Markdown content blocks to RST format using
    the Pandoc external tool. It includes caching to ensure deterministic
    output and fallback to original content if Pandoc fails.

    Args:
        markdown_content: Markdown content to convert
        content_cache: Optional cache for pandoc conversions

    Returns:
        RST-formatted content

    Raises:
        subprocess.CalledProcessError: If pandoc command fails
        FileError: If any of the file operations fail
        FileNotFoundError: If pandoc executable is not found

    Note:
        - Uses temporary files for Pandoc conversion
        - Caches results to ensure consistent output
        - Raises FileError if Pandoc conversion fails
        - Provides helpful installation instructions if Pandoc is not available
        - Handles file operation errors gracefully
    """
    if not markdown_content.strip():
        return ""

    # Initialize cache if not provided
    if content_cache is None:
        content_cache = {}

    # Check if content is already in cache
    if markdown_content in content_cache:
        return content_cache[markdown_content]

    try:
        # Create a temporary file with the markdown content
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as temp_md:
            temp_md.write(markdown_content)
            temp_md_path = Path(temp_md.name)
    except OSError as e:
        msg = f"Failed to create temporary file: {e}"
        raise FileError(msg) from e

    try:
        # Create a temporary file for the RST output
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".rst", delete=False, encoding="utf-8"
        ) as temp_rst:
            temp_rst_path = Path(temp_rst.name)
    except OSError as e:
        with suppress(OSError):
            temp_md_path.unlink()
            temp_rst_path.unlink()
        msg = f"Failed to create temporary file: {e}"
        raise FileError(msg) from e

    try:
        # Run pandoc to convert markdown to RST
        subprocess.run(
            [
                "pandoc",
                "-f",
                "markdown",
                "-t",
                "rst",
                str(temp_md_path),
                "-o",
                str(temp_rst_path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        with suppress(OSError):
            temp_md_path.unlink()
            temp_rst_path.unlink()
        msg = f"Pandoc conversion failed: {e}"
        raise FileError(msg) from e
    except FileNotFoundError as e:
        with suppress(OSError):
            temp_md_path.unlink()
            temp_rst_path.unlink()
        instructions = get_pandoc_installation_instructions()
        msg = f"Pandoc is not installed or not found in PATH.\n\n{instructions}"
        raise FileError(msg) from e

    try:
        # Read the converted RST content
        with temp_rst_path.open(encoding="utf-8") as f:
            rst_content = f.read()
    except OSError as e:
        with suppress(OSError):
            temp_md_path.unlink()
            temp_rst_path.unlink()
        msg = f"Failed to read converted RST content: {e}"
        raise FileError(msg) from e
    finally:
        # Clean up temporary files
        with suppress(OSError):
            temp_md_path.unlink()
            temp_rst_path.unlink()

    # Post-process RST content to remove auto-generated Pandoc anchors
    rst_content = remove_pandoc_anchors(rst_content)

    # Cache the result
    content_cache[markdown_content] = rst_content
    return rst_content


def remove_pandoc_anchors(rst_content: str) -> str:
    """
    Remove auto-generated Pandoc anchors from RST content.

    Pandoc automatically generates `.. _target:` anchors above headings,
    which can cause duplicate anchor names across chapters (e.g., multiple
    "Summary" sections). This function removes them to let authors add
    their own anchors when needed.

    Args:
        rst_content: RST content that may contain Pandoc anchors

    Returns:
        RST content with Pandoc anchors removed
    """
    if not rst_content.strip():
        return rst_content

    lines = rst_content.splitlines()
    filtered_lines = []
    skip_next_line = False

    for line in lines:
        # Skip lines that are Pandoc auto-generated anchors
        if line.strip().startswith(".. _") and line.strip().endswith(":"):
            skip_next_line = False
            continue

        # Skip empty lines that follow anchors (common Pandoc output)
        if skip_next_line and line.strip() == "":
            skip_next_line = False
            continue

        filtered_lines.append(line)

    return "\n".join(filtered_lines)


def get_clean_chapter_title(chapter: Chapter) -> str:
    """
    Get a clean chapter title without the prefix.

    Args:
        chapter: Chapter object

    Returns:
        Clean chapter title without prefix
    """
    title = chapter.title

    # Remove common prefixes
    if title.startswith("Chapter "):
        # Extract everything after "Chapter X: "
        if ":" in title:
            return title.split(":", 1)[1].strip()
        else:
            return title[8:].strip()  # Remove "Chapter " prefix

    elif title.startswith("Appendix "):
        # Extract everything after "Appendix X: "
        if ":" in title:
            return title.split(":", 1)[1].strip()
        else:
            return title[9:].strip()  # Remove "Appendix " prefix

    elif title.startswith("Introduction: "):
        return title[13:].strip()  # Remove "Introduction: " prefix

    elif title.startswith("Prologue: "):
        return title[10:].strip()  # Remove "Prologue: " prefix

    return title


def get_clean_section_title(title: str) -> str:
    """
    Get a clean section title without the number prefix.

    Args:
        title: Section title (e.g., "1.1 Installation Guide")

    Returns:
        Clean section title without number prefix
    """
    # Remove section numbering patterns
    # Match patterns like "1.1", "2.3", "A.1", "B.2"
    section_pattern = re.compile(r"^(\d+\.\d+|[A-Z]\.\d+)\s+(.*)")
    match = section_pattern.match(title)

    if match:
        return match.group(2).strip()

    return title


def filter_chapter_heading(content: str, chapter_title: str) -> str:
    """
    Filter out the original chapter heading from content to avoid duplication.

    Args:
        content: Content that may contain the chapter heading
        chapter_title: Original chapter title to filter out

    Returns:
        Content with chapter heading filtered out
    """
    # Split content into lines
    lines = content.splitlines()

    # Find and remove the chapter heading line
    filtered_lines = []
    heading_found = False

    for line in lines:
        # Skip the exact chapter title line
        if line.strip() == chapter_title.strip():
            heading_found = True
            continue

        # Skip the underline line (equals signs or dashes)
        if heading_found and re.match(r"^[=\-]+$", line.strip()):
            heading_found = False
            continue

        filtered_lines.append(line)

    return "\n".join(filtered_lines)


def filter_section_heading(content: str, section_title: str) -> str:
    """
    Filter out the original section heading from content to avoid duplication.

    Args:
        content: Content that may contain the section heading
        section_title: Original section title to filter out (may include markdown syntax)

    Returns:
        Content with section heading filtered out
    """
    # Split content into lines
    lines = content.splitlines()

    # Find and remove the section heading line
    filtered_lines = []
    heading_found = False

    for line in lines:
        # Skip the exact section title line (with or without markdown syntax)
        stripped_line = line.strip()

        # Check for exact match first
        if stripped_line == section_title.strip():
            heading_found = True
            continue

        # Check for markdown format matches (### Title, ## Title, # Title)
        # Extract the clean title from the markdown heading
        clean_title = section_title.strip()
        if clean_title.startswith("#"):
            # Remove markdown prefix and get clean title
            clean_title = clean_title.lstrip("#").strip()

        # Check for exact matches and various markdown formats
        if (
            stripped_line == clean_title
            or stripped_line == f"### {clean_title}"
            or stripped_line == f"## {clean_title}"
            or stripped_line == f"# {clean_title}"
        ):
            heading_found = True
            continue

        # Check for numbered section headings like "### 2.1 Introduction"
        # This handles cases where the content contains the full numbered heading
        # but we only have the clean title
        if stripped_line.startswith("### ") and stripped_line.endswith(
            f" {clean_title}"
        ):
            heading_found = True
            continue
        if stripped_line.startswith("## ") and stripped_line.endswith(
            f" {clean_title}"
        ):
            heading_found = True
            continue
        if stripped_line.startswith("# ") and stripped_line.endswith(f" {clean_title}"):
            heading_found = True
            continue

        # Skip the underline line (dashes)
        if heading_found and re.match(r"^[\-]+$", stripped_line):
            heading_found = False
            continue

        filtered_lines.append(line)

    return "\n".join(filtered_lines)


def get_clean_chapter_title_marko(chapter_title: str) -> str:
    """
    Get a clean chapter title without the prefix for Marko models.

    Args:
        chapter_title: Chapter title string

    Returns:
        Clean chapter title without prefix
    """
    # Remove common prefixes
    if chapter_title.startswith("Chapter "):
        # Extract everything after "Chapter X: "
        if ":" in chapter_title:
            return chapter_title.split(":", 1)[1].strip()
        else:
            return chapter_title[8:].strip()  # Remove "Chapter " prefix

    elif chapter_title.startswith("Appendix "):
        # Extract everything after "Appendix X: "
        if ":" in chapter_title:
            return chapter_title.split(":", 1)[1].strip()
        else:
            return chapter_title[9:].strip()  # Remove "Appendix " prefix

    elif chapter_title.startswith("Introduction: "):
        return chapter_title  # Keep "Introduction: " prefix

    elif chapter_title.startswith("Prologue: "):
        return chapter_title  # Keep "Prologue: " prefix

    return chapter_title


def filter_chapter_heading_marko(content: str, chapter_title: str) -> str:
    """
    Filter out the original chapter heading from content to avoid duplication for Marko models.

    Args:
        content: Content that may contain the chapter heading
        chapter_title: Original chapter title to filter out

    Returns:
        Content with chapter heading filtered out
    """
    # Split content into lines
    lines = content.splitlines()

    # Find and remove the chapter heading line
    filtered_lines = []
    heading_found = False

    for line in lines:
        # Skip the exact chapter title line (with or without markdown syntax)
        stripped_line = line.strip()
        if (
            stripped_line == chapter_title.strip()
            or stripped_line == f"## {chapter_title.strip()}"
            or stripped_line == f"# {chapter_title.strip()}"
        ):
            heading_found = True
            continue

        # Skip the underline line (equals signs or dashes)
        if heading_found and re.match(r"^[=\-]+$", stripped_line):
            heading_found = False
            continue

        filtered_lines.append(line)

    return "\n".join(filtered_lines)
