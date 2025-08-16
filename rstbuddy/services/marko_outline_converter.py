"""
Marko-based outline converter service.

Converts parsed Marko markdown outlines into RST file structure with proper
folder organization and toctree entries.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .rst_utils import (
    backup_and_write_file,
    convert_content_to_rst,
    filter_chapter_heading_marko,
    filter_section_heading,
    get_clean_chapter_title_marko,
    get_clean_section_title,
)
from ..models.marko_outline import MarkoHeadingType

if TYPE_CHECKING:
    from ..models.marko_outline import (
        MarkoBookOutline,
        MarkoChapter,
        MarkoSection,
        MarkoHeadingType,
    )


class MarkoOutlineConverter:
    """
    Convert parsed Marko outline to RST file structure.

    This class handles the conversion of parsed Marko markdown outlines into
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
        Initialize the Marko outline converter.

        Args:
            force: If True, overwrite existing files with timestamped backups
            dry_run: If True, show what would be created without creating files

        """
        self.force = force
        self.dry_run = dry_run
        self._content_cache: dict[str, str] = {}  # Cache for pandoc conversions

    def convert_outline(self, outline: MarkoBookOutline) -> None:
        """
        Convert the outline to RST file structure.

        This is the main entry point for converting a parsed Marko outline
        into a complete RST documentation structure. It orchestrates
        the creation of all necessary files and directories.

        Args:
            outline: Parsed Marko book outline structure

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

    def _generate_top_level_index(self, outline: MarkoBookOutline) -> None:
        """
        Generate the top-level index.rst file.

        Creates the main index.rst file that serves as the entry point
        for the documentation. Includes the book title, introduction content,
        and a table of contents linking to all chapters.

        Args:
            outline: The complete Marko book outline structure

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
            filtered_content = filter_chapter_heading_marko(
                outline.introduction_content.content, outline.title
            )
            rst_content = convert_content_to_rst(filtered_content, self._content_cache)
            content.append(rst_content)
            content.append("")

        # Table of contents for front matter (Introduction and Prologue)
        front_matter = [
            c
            for c in outline.chapters
            if c.heading_type
            in [MarkoHeadingType.INTRODUCTION, MarkoHeadingType.PROLOGUE]
        ]
        if front_matter:
            content.append(".. toctree::")
            content.append("   :caption: Front Matter")
            content.append("   :hidden:")
            content.append("")
            content.extend(
                [f"   {chapter.folder_name}/index" for chapter in front_matter]
            )
            content.append("")

        # Table of contents for regular chapters
        chapters = [
            c
            for c in outline.chapters
            if c.heading_type
            not in [
                MarkoHeadingType.APPENDIX,
                MarkoHeadingType.INTRODUCTION,
                MarkoHeadingType.PROLOGUE,
            ]
        ]
        if chapters:
            content.append(".. toctree::")
            content.append("   :caption: Chapters")
            content.append("   :hidden:")
            content.append("")
            content.extend([f"   {chapter.folder_name}/index" for chapter in chapters])
            content.append("")

        # Table of contents for appendices
        appendices = [
            c for c in outline.chapters if c.heading_type == MarkoHeadingType.APPENDIX
        ]
        if appendices:
            content.append(".. toctree::")
            content.append("   :caption: Appendices")
            content.append("   :hidden:")
            content.append("")
            content.extend(
                [f"   {appendix.folder_name}/index" for appendix in appendices]
            )
            content.append("")

        # Use smart backup and write
        final_content = "\n".join(content)
        backup_and_write_file(index_path, final_content, self.force, self.dry_run)

    def _generate_chapter_files(self, output_dir: Path, chapter: MarkoChapter) -> None:
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

    def _generate_chapter_index(self, chapter_dir: Path, chapter: MarkoChapter) -> None:
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
        clean_title = get_clean_chapter_title_marko(chapter.title)
        content.append(clean_title)
        content.append("=" * len(clean_title))
        content.append("")

        # Table of contents for sections (immediately after title)
        actual_sections = [s for s in chapter.sections if s.filename]
        if actual_sections:
            content.append(".. toctree::")
            content.append("   :hidden:")
            content.append("")
            content.extend([f"   {section.filename}" for section in actual_sections])
            content.append("")

        # Chapter content
        if chapter.content.content.strip():
            # Filter out the original chapter heading to avoid duplicate headings
            filtered_content = filter_chapter_heading_marko(
                chapter.content.content, chapter.title
            )
            rst_content = convert_content_to_rst(filtered_content, self._content_cache)
            content.append(rst_content)
            content.append("")

        # Write the file
        final_content = "\n".join(content)
        backup_and_write_file(index_path, final_content, self.force, self.dry_run)

    def _generate_section_file(self, chapter_dir: Path, section: MarkoSection) -> None:
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
        clean_title = get_clean_section_title(section.title)
        content.append(clean_title)
        content.append("-" * len(clean_title))
        content.append("")

        # Section content
        if section.content.content.strip():
            # Filter out the original section heading to avoid duplicate headings
            filtered_content = filter_section_heading(
                section.content.content, section.title
            )
            rst_content = convert_content_to_rst(filtered_content, self._content_cache)
            content.append(rst_content)

        # Write the file
        final_content = "\n".join(content)
        backup_and_write_file(section_path, final_content, self.force, self.dry_run)

    def _show_dry_run_plan(self, outline: MarkoBookOutline) -> None:
        """
        Show what would be created without actually creating files.

        Args:
            outline: The outline to show the plan for

        """
        print("=== DRY RUN - No files will be created ===")
        print(f"Book title: {outline.title}")
        print(f"Output directory: {outline.output_dir}")
        print(f"Chapters: {len(outline.chapters)}")
        print()

        for chapter in outline.chapters:
            print(f"Chapter: {chapter.title}")
            print(f"  Folder: {chapter.folder_name}")
            print(f"  Sections: {len([s for s in chapter.sections if s.filename])}")

            # Show sections
            actual_sections = [s for s in chapter.sections if s.filename]
            if actual_sections:
                for section in actual_sections:
                    print(f"    - {section.title} -> {section.filename}")
            print()

        # Show files that would be created
        print("Files that would be created:")
        self._list_files_to_create(outline)
        print("✓ Dry run completed - no files were created")

    def _list_files_to_create(self, outline: MarkoBookOutline) -> None:
        """
        List all files that would be created.

        Args:
            outline: The outline to list files for

        """
        files_to_create = []

        # Top-level index.rst
        files_to_create.append(f"  {outline.output_dir}/index.rst")

        # Chapter index files
        for chapter in outline.chapters:
            files_to_create.append(
                f"  {outline.output_dir}/{chapter.folder_name}/index.rst"
            )

        # Section files
        for chapter in outline.chapters:
            for section in chapter.sections:
                if section.filename:
                    files_to_create.append(
                        f"  {outline.output_dir}/{chapter.folder_name}/{section.filename}"
                    )

        # Print all files
        for file_path in files_to_create:
            print(file_path)

    def show_generated_structure(self, outline: MarkoBookOutline) -> None:
        """
        Display the generated file structure.

        Args:
            outline: The outline that was converted

        """
        print(f"└── {outline.output_dir.name}/")

        # Show chapters and their sections
        for chapter in outline.chapters:
            print(f"    ├── {chapter.folder_name}/")

            # Show sections
            actual_sections = [s for s in chapter.sections if s.filename]
            for i, section in enumerate(actual_sections):
                if i == len(actual_sections) - 1:
                    # Last section
                    print(f"    │   └── {section.filename}")
                else:
                    print(f"    │   ├── {section.filename}")

            # Show chapter index
            if actual_sections:
                print("    │   └── index.rst")
            else:
                print("    │   └── index.rst")

        # Show top-level index
        print("    └── index.rst")
