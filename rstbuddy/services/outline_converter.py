"""
Outline converter service.

Converts parsed markdown outlines into RST file structure with proper
folder organization and toctree entries.
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


class OutlineConverter:
    """
    Convert parsed outline to RST file structure.

    This class handles the conversion of parsed markdown outlines into
    a complete RST documentation structure. It creates directories,
    generates RST files with proper Sphinx formatting, and manages
    content conversion from Markdown to RST using Pandoc.

    Attributes:
        force: Whether to force overwrite existing files
        dry_run: Whether to show what would be created without creating files
        _content_cache: In-memory cache for Pandoc conversion results

    """

    def __init__(self, force: bool = False, dry_run: bool = False):
        """
        Initialize the outline converter.

        Args:
            force: If True, overwrite existing files with timestamped backups
            dry_run: If True, show what would be created without creating files

        """
        self.force = force
        self.dry_run = dry_run
        self._content_cache: dict[str, str] = {}  # Cache for pandoc conversions

    def _content_is_different(self, file_path: Path, new_content: str) -> bool:
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
            normalized_existing = self._normalize_content(existing_content)
            normalized_new = self._normalize_content(new_content)

        except (OSError, UnicodeDecodeError):
            # If we can't read the existing file, assume it's different
            return True
        else:
            return normalized_existing != normalized_new

    def _normalize_content(self, content: str) -> str:
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

    def _backup_file_if_exists(self, file_path: Path) -> None:
        """
        Backup a single file if it exists, using timestamped naming.

        Args:
            file_path: Path to the file to backup

        Note:
            Creates a backup with format: filename.timestamp.bak
            Only creates backup if force=True and file exists

        """
        if file_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # noqa: DTZ005
            backup_path = file_path.with_suffix(f".{timestamp}.bak")
            if self.dry_run:
                print(f"[DRY RUN] Would backup: {file_path} -> {backup_path}")
            else:
                shutil.copy2(file_path, backup_path)
                print(f"Backed up: {file_path} -> {backup_path}")

    def _backup_and_write_file(self, file_path: Path, new_content: str) -> None:
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

        Raises:
            OSError: If file operations fail (read, write, backup)
            UnicodeDecodeError: If existing file cannot be read with UTF-8 encoding

        """
        # Check if content is different
        if not self._content_is_different(file_path, new_content):
            print(f"Skipping {file_path} - content unchanged")
            return

        # Content is different, so backup and write
        if self.force and file_path.exists():
            if self.dry_run:
                print(f"[DRY RUN] Would backup: {file_path}")
            else:
                self._backup_file_if_exists(file_path)

        # Write the new content
        if self.dry_run:
            print(f"[DRY RUN] Would update: {file_path}")
        else:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with file_path.open("w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Updated: {file_path}")

    def convert_outline(self, outline: BookOutline) -> None:
        """
        Convert the outline to RST file structure.

        This is the main entry point for converting a parsed outline
        into a complete RST documentation structure. It orchestrates
        the creation of all necessary files and directories.

        Args:
            outline: Parsed book outline structure

        Note:
            If dry_run is True, only shows what would be created
            without actually creating any files.

        """
        if self.dry_run:
            self._show_dry_run_plan(outline)
            return

        # Create output directory
        self._create_output_directory(outline.output_dir)

        # Generate top-level index.rst
        self._generate_top_level_index(outline)

        # Generate chapter files
        for chapter in outline.chapters:
            self._generate_chapter_files(outline.output_dir, chapter)

    def _create_output_directory(self, output_dir: Path) -> None:
        """
        Create the output directory, handling existing content if force=True.

        Args:
            output_dir: Path to the output directory to create

        Raises:
            FileExistsError: If directory exists and force=False

        Note:
            When force=True, existing directories are handled at the file level
            rather than backing up the entire directory.

        """
        if output_dir.exists():
            if not self.force:
                msg = (
                    f"Output directory {output_dir} already exists. "
                    "Use --force to overwrite."
                )
                raise FileExistsError(msg)
            # If force=True, we'll handle backups at the file level instead of
            # directory level Just ensure the directory exists and is ready for
            # file operations

        output_dir.mkdir(parents=True, exist_ok=True)

    def _generate_top_level_index(self, outline: BookOutline) -> None:
        """
        Generate the top-level index.rst file.

        Creates the main index.rst file that serves as the entry point
        for the documentation. Includes the book title, introduction content,
        and a table of contents linking to all chapters.

        Args:
            outline: The complete book outline structure

        Raises:
            OSError: If file operations fail during writing

        """
        index_path = outline.output_dir / "index.rst"

        content = []

        # Book title
        content.append("#" * len(outline.title))
        content.append(outline.title)
        content.append("#" * len(outline.title))
        content.append("")

        # Introduction content
        if outline.introduction_content.content.strip():
            # Filter out the original chapter heading to avoid duplicate headings
            filtered_content = self._filter_chapter_heading(
                outline.introduction_content.content, outline.title
            )
            rst_content = self.convert_content_to_rst(filtered_content)
            content.append(rst_content)
            content.append("")

        # Table of contents
        content.append("Table of Contents")
        content.append("================")
        content.append("")
        content.append(".. toctree::")
        content.append("   :maxdepth: 2")
        content.append("   :numbered:")
        content.append("")

        # Add chapters in order
        content.extend(
            [f"   {chapter.folder_name}/index" for chapter in outline.chapters]
        )

        content.append("")

        # Use smart backup and write
        final_content = "\n".join(content)
        self._backup_and_write_file(index_path, final_content)

    def _generate_chapter_files(self, output_dir: Path, chapter: Chapter) -> None:
        """
        Generate files for a single chapter.

        Creates the chapter directory and generates both the chapter's
        index.rst file and individual section files.

        Args:
            output_dir: Base output directory
            chapter: Chapter to generate files for

        Raises:
            OSError: If file operations fail during directory creation or writing

        """
        chapter_dir = output_dir / chapter.folder_name
        chapter_dir.mkdir(exist_ok=True)

        # Generate chapter index.rst
        self._generate_chapter_index(chapter_dir, chapter)

        # Generate section files (only for actual sections, not content headings)
        for section in chapter.sections:
            if section.filename:  # Only create files for sections with filenames
                self._generate_section_file(chapter_dir, section)

    def _generate_chapter_index(self, chapter_dir: Path, chapter: Chapter) -> None:
        """
        Generate the index.rst file for a chapter.

        Creates a chapter's index.rst file containing the chapter title,
        chapter content, and a table of contents for its sections.

        Args:
            chapter_dir: Directory where the chapter files should be created
            chapter: Chapter to generate the index for

        Raises:
            OSError: If file operations fail during writing

        """
        index_path = chapter_dir / "index.rst"

        content = []

        # Chapter title (clean version without prefix)
        clean_title = self._get_clean_chapter_title(chapter)
        content.append(clean_title)
        content.append("=" * len(clean_title))
        content.append("")

        # Chapter content
        if chapter.content.content.strip():
            # Filter out the original chapter heading to avoid duplicate headings
            filtered_content = self._filter_chapter_heading(
                chapter.content.content, chapter.title
            )
            rst_content = self.convert_content_to_rst(filtered_content)
            content.append(rst_content)
            content.append("")

        # Table of contents for sections
        actual_sections = [s for s in chapter.sections if s.filename]
        if actual_sections:
            content.append(".. toctree::")
            content.append("   :maxdepth: 1")
            content.append("   :hidden:")
            content.append("")
            content.extend([f"   {section.filename}" for section in actual_sections])
            content.append("")

        # Write the file
        final_content = "\n".join(content)
        self._backup_and_write_file(index_path, final_content)

    def _generate_section_file(self, chapter_dir: Path, section: Section) -> None:
        """
        Generate a section file.

        Creates an individual RST file for a section containing the
        section title and content.

        Args:
            chapter_dir: Directory where the section file should be created
            section: Section to generate the file for

        Raises:
            OSError: If file operations fail during writing

        """
        section_path = chapter_dir / section.filename

        content = []

        # Section title (clean version without number prefix)
        clean_title = self._get_clean_section_title(section.title)
        content.append(clean_title)
        content.append("-" * len(clean_title))
        content.append("")

        # Section content
        if section.content.content.strip():
            # Filter out the original section heading to avoid duplicate headings
            filtered_content = self._filter_section_heading(
                section.content.content, section.title
            )
            rst_content = self.convert_content_to_rst(filtered_content)
            content.append(rst_content)

        # Write the file
        final_content = "\n".join(content)
        self._backup_and_write_file(section_path, final_content)

    def convert_content_to_rst(self, markdown_content: str) -> str:
        """
        Convert Markdown content to RST using Pandoc.

        This method converts Markdown content blocks to RST format using
        the Pandoc external tool. It includes caching to ensure deterministic
        output and fallback to original content if Pandoc fails.

        Args:
            markdown_content: Markdown content to convert

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

        # Check if content is already in cache
        if markdown_content in self._content_cache:
            return self._content_cache[markdown_content]

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
            msg = f"Failed to read temporary file: {e}"
            raise FileError(msg) from e

        # Cache the converted content
        self._content_cache[markdown_content] = rst_content
        return rst_content

    def _filter_chapter_heading(self, content: str, chapter_title: str) -> str:
        """
        Filter out the original chapter heading from content to avoid duplicates.

        Removes the original Markdown chapter heading from the content
        to prevent it from appearing as a duplicate heading in the
        generated RST file.

        Args:
            content: Content that may contain the original heading
            chapter_title: Title of the chapter to filter out

        Returns:
            Content with the original heading removed

        """
        # Remove the original chapter heading line if it exists
        lines = content.split("\n")
        filtered_lines = []

        for line in lines:
            # Skip lines that match the chapter heading (with or without
            # markdown syntax)
            stripped_line = line.strip()
            if stripped_line in (
                chapter_title,
                f"# {chapter_title}",
                f"## {chapter_title}",
            ):
                continue
            filtered_lines.append(line)

        return "\n".join(filtered_lines)

    def _filter_section_heading(self, content: str, section_title: str) -> str:
        """
        Filter out the original section heading from content to avoid duplicates.

        Removes the original Markdown section heading from the content
        to prevent it from appearing as a duplicate heading in the
        generated RST file. Handles various heading formats and partial matches.

        Args:
            content: Content that may contain the original heading
            section_title: Title of the section to filter out

        Returns:
            Content with the original heading removed

        """
        # Remove the original section heading line if it exists
        lines = content.split("\n")
        filtered_lines = []

        for line in lines:
            # Skip lines that match the section heading (with or without
            # markdown syntax)
            stripped_line = line.strip()

            # Check for exact matches
            if stripped_line in (
                section_title,
                f"# {section_title}",
                f"## {section_title}",
            ):
                continue

            # Check for partial matches (in case the original title contains the
            # cleaned title) This handles cases where the original title is
            # "2.1: Event-Driven Processing" and the cleaned title is
            # "Event-Driven Processing"
            if section_title and section_title in stripped_line:
                # Only skip if it looks like a heading (starts with # or is
                # followed by underline)
                if stripped_line.startswith("#") or any(
                    next_line.strip().startswith("~")
                    or next_line.strip().startswith("-")
                    for next_line in lines[
                        lines.index(line) + 1 : lines.index(line) + 2
                    ]
                ):
                    continue

            filtered_lines.append(line)

        return "\n".join(filtered_lines)

    def _get_clean_chapter_title(self, chapter: Chapter) -> str:  # noqa: PLR0911
        """
        Get clean chapter title without prefix.

        Removes formatting prefixes like "Chapter X:", "Appendix X:",
        etc. to create clean titles for RST headings.

        Args:
            chapter: Chapter object containing the title to clean

        Returns:
            Cleaned chapter title without formatting prefixes

        """
        if chapter.heading_type.value == "prologue":
            return "Prologue"
        if chapter.heading_type.value == "introduction":
            # Remove "Introduction:" prefix and extract the actual title
            if chapter.title.startswith("Introduction"):
                if ":" in chapter.title:
                    return chapter.title.split(":", 1)[1].strip()
                return "Introduction"
            return chapter.title
        if chapter.heading_type.value == "chapter":
            # Remove "Chapter X:" prefix
            if chapter.title.startswith("Chapter "):
                return chapter.title.split(":", 1)[1].strip()
            return chapter.title
        if chapter.heading_type.value == "appendix":
            # Remove "Appendix X:" prefix and any trailing text after colon
            if chapter.title.startswith("Appendix "):
                # Extract the part after "Appendix " and before any colon
                appendix_part = chapter.title[9:]  # Remove "Appendix " prefix
                if ":" in appendix_part:
                    return appendix_part.split(":", 1)[1].strip()
                return appendix_part.strip()
            return chapter.title
        return chapter.title

    def _get_clean_section_title(self, section_title: str) -> str:
        """
        Get clean section title without number prefix.

        Removes number prefixes like "1.1 ", "2.3.1 ", "D.1.2 ", etc.
        to create clean titles for RST headings. Handles both regular
        numbered sections and appendix sections.

        Args:
            section_title: Section title that may contain number prefixes

        Returns:
            Cleaned section title without number prefixes

        Note:
            This method handles various prefix formats:
            - "1.1 Title" -> "Title"
            - "2.1: Title" -> "Title"
            - "D.1.2 Title" -> "Title"
            - ": Title" -> "Title"

        """
        # Remove number prefixes like "1. ", "2.3. ", "D.1. ", etc.  This
        # handles both regular numbered sections and appendix sections Also
        # handle cases with colons like "2.1: Title" - the colon is part of the
        # prefix And handle cases where the title starts with a colon like ":
        # Title" But be careful not to remove the first letter of the actual
        # title
        clean_title = re.sub(
            r"^(?:\d+(?:\.\d+)*\s*:?\s*|[A-Z]\.\d+(?:\.\d+)*\s*:?\s*|:\s*)",
            "",
            section_title,
        )
        return clean_title.strip()

    def _show_dry_run_plan(self, outline: BookOutline) -> None:
        """
        Show what would be created without actually creating files.

        Displays a comprehensive plan of what files and directories
        would be created during the conversion process.

        Args:
            outline: The book outline to show the plan for

        """
        print("=== DRY RUN - No files will be created ===")
        print(f"Book title: {outline.title}")
        print(f"Output directory: {outline.output_dir}")
        print(f"Chapters: {len(outline.chapters)}")

        for chapter in outline.chapters:
            print(f"\nChapter: {chapter.title}")
            print(f"  Folder: {chapter.folder_name}")
            print(f"  Sections: {len(chapter.sections)}")
            for section in chapter.sections:
                print(f"    - {section.title} -> {section.filename}")

        print("\nFiles that would be created:")
        print(f"  {outline.output_dir}/index.rst")
        for chapter in outline.chapters:
            print(f"  {outline.output_dir}/{chapter.folder_name}/index.rst")
            for section in chapter.sections:
                print(
                    f"  {outline.output_dir}/{chapter.folder_name}/{section.filename}"
                )
