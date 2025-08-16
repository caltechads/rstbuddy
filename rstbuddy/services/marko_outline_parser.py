"""
Marko-based outline parser service.

This module provides an alternative implementation of the outline parser
using Marko's AST approach instead of regex-based line parsing.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Any

import marko
from marko.md_renderer import MarkdownRenderer
from marko.block import Document, Heading

from ..models.marko_outline import (
    MarkoBookOutline,
    MarkoChapter,
    MarkoContentBlock,
    MarkoHeadingType,
    MarkoSection,
)
from ..settings import Settings


class MarkoOutlineParser:
    """
    Parses markdown outlines using Marko's AST approach.

    This parser leverages Marko's robust markdown parsing to extract
    document structure, chapters, sections, and content blocks. It
    provides a more reliable alternative to regex-based parsing.
    """

    def __init__(self) -> None:
        """
        Initialize the Marko outline parser.

        Sets up regex patterns for identifying different types of headings
        and section numbering patterns.
        """
        #: Regex pattern for matching chapter headings
        self._chapter_pattern = re.compile(r"^Chapter\s+(\d+):\s*(.*)")
        #: Regex pattern for matching appendix headings
        self._appendix_pattern = re.compile(r"^Appendix\s+([A-Z]):\s*(.*)")
        #: Canonical regex pattern for section headings (two levels maximum)
        self._section_pattern = re.compile(r"^(\d+\.\d+|[A-Z]\.\d+)(?!\.\d)\s+(.*)")

    def parse_file(
        self, file_path: Path, output_dir: Path | None = None
    ) -> MarkoBookOutline:
        """
        Parse a markdown file to extract book outline structure.

        This is the main entry point for parsing markdown files. It reads
        the file, parses the structure using Marko, and returns a complete
        MarkoBookOutline object with all chapters, sections, and content
        properly organized.

        Args:
            file_path: Path to the markdown file to parse
            output_dir: Custom output directory (default: uses settings)

        Returns:
            MarkoBookOutline with complete structure

        Raises:
            OSError: If the file cannot be opened or read
            UnicodeDecodeError: If the file cannot be decoded with UTF-8 encoding
        """
        with file_path.open(encoding="utf-8") as f:
            content = f.read()

        # Parse with Marko
        doc = marko.parse(content)

        # Parse the structure
        title, introduction_content, chapters = self._parse_structure(doc)

        # Determine output directory
        if output_dir is None:
            # Use settings documentation directory
            settings = Settings()
            output_dir = Path(settings.documentation_dir)
        else:
            output_dir = Path(output_dir)

        return MarkoBookOutline(
            title=title,
            introduction_content=introduction_content,
            chapters=chapters,
            output_dir=output_dir,
        )

    def _parse_structure(
        self, doc: Document
    ) -> tuple[str, MarkoContentBlock, List[MarkoChapter]]:
        """
        Parse the document structure from Marko's AST.

        Analyzes the parsed document to extract the title, introduction
        content, and all chapters with their sections and content.

        Args:
            doc: Marko parsed document object

        Returns:
            Tuple of (title, introduction_content, chapters)
        """
        children = list(doc.children)

        # Extract title (first H1)
        title = ""
        title_end_idx = 0

        for i, child in enumerate(children):
            if isinstance(child, Heading) and child.level == 1:
                title = self._extract_heading_text(child)
                title_end_idx = i
                break

        if not title:
            raise ValueError("Document must have a title (H1 heading)")

        # Extract introduction content (between title and first H2)
        introduction_start = title_end_idx + 1
        introduction_end = len(children)

        for i in range(introduction_start, len(children)):
            if isinstance(children[i], Heading) and children[i].level == 2:
                introduction_end = i
                break

        introduction_content = self._extract_content_block(
            children, introduction_start, introduction_end
        )

        # Extract chapters
        chapters = []
        current_chapter = None

        for i, child in enumerate(children):
            if isinstance(child, Heading) and child.level == 2:
                # Finalize previous chapter if it exists
                if current_chapter:
                    self._finalize_chapter(children, current_chapter, i)
                    chapters.append(current_chapter)

                # Start new chapter
                current_chapter = self._parse_chapter_heading(child, i)
            elif isinstance(child, Heading) and child.level == 3 and current_chapter:
                # Process section heading - ONLY H3 headings are sections
                self._process_section_heading(child, i, children, current_chapter)
            # Note: H4 and deeper headings are ignored - they're not sections

        # Finalize the last chapter
        if current_chapter:
            self._finalize_chapter(children, current_chapter, len(children))
            chapters.append(current_chapter)

        return title, introduction_content, chapters

    def _extract_heading_text(self, heading_element: Heading) -> str:
        """
        Extract text content from a heading element.

        Args:
            heading_element: Marko heading element

        Returns:
            The heading text as a string
        """
        text_parts = []
        for child in heading_element.children:
            if hasattr(child, "children"):
                # Recursively extract text from nested children
                if isinstance(child.children, str):
                    text_parts.append(child.children)
                elif isinstance(child.children, list):
                    # Handle list of children recursively
                    for grandchild in child.children:
                        if hasattr(grandchild, "children"):
                            if isinstance(grandchild.children, str):
                                text_parts.append(grandchild.children)
                            else:
                                # For complex nested structures, try to get string representation
                                text_parts.append(str(grandchild))
                        else:
                            text_parts.append(str(grandchild))
                else:
                    text_parts.append(str(child.children))
            else:
                # Direct text content
                text_parts.append(str(child))

        return "".join(text_parts)

    def _extract_content_block(
        self, children: List[Any], start_idx: int, end_idx: int
    ) -> MarkoContentBlock:
        """
        Extract content between two indices and convert to markdown.

        Args:
            children: List of document children
            start_idx: Starting index (inclusive)
            end_idx: Ending index (exclusive)

        Returns:
            MarkoContentBlock containing the extracted content
        """
        if start_idx >= end_idx:
            return MarkoContentBlock("", start_idx + 1, end_idx)

        # Extract elements and create a document
        content_elements = children[start_idx:end_idx]
        content_doc = Document()
        content_doc.children = content_elements

        # Render to markdown
        renderer = MarkdownRenderer()
        content = renderer.render(content_doc)

        return MarkoContentBlock(
            content=content, start_line=start_idx + 1, end_line=end_idx
        )

    def _parse_chapter_heading(
        self, heading_element: Heading, line_idx: int
    ) -> MarkoChapter:
        """
        Parse a chapter heading to create a MarkoChapter object.

        Args:
            heading_element: Marko heading element
            line_idx: Index of the heading in the document

        Returns:
            MarkoChapter object
        """
        heading_text = self._extract_heading_text(heading_element)

        # Determine heading type and folder name
        if heading_text.startswith("Prologue"):
            heading_type = MarkoHeadingType.PROLOGUE
            folder_name = "prologue"
        elif heading_text.startswith("Introduction"):
            heading_type = MarkoHeadingType.INTRODUCTION
            folder_name = "introduction"
        elif match := self._chapter_pattern.match(heading_text):
            heading_type = MarkoHeadingType.CHAPTER
            chapter_num = int(match.group(1))
            folder_name = f"chapter{chapter_num}"
        elif heading_text.startswith("Appendix "):
            heading_type = MarkoHeadingType.APPENDIX
            appendix_part = heading_text[9:]  # Remove "Appendix " prefix

            # Extract just the letter part
            if ":" in appendix_part:
                base_letter = appendix_part.split(":")[0].strip()
            elif "." in appendix_part:
                base_letter = appendix_part.split(".")[0].strip()
            else:
                base_letter = appendix_part.strip()

            if len(base_letter) == 1 and base_letter.isalpha():
                folder_name = f"appendix{base_letter}"
            else:
                folder_name = "appendix_unknown"
        else:
            # Default to chapter
            heading_type = MarkoHeadingType.CHAPTER
            folder_name = "chapter_unknown"

        return MarkoChapter(
            title=heading_text,
            heading_type=heading_type,
            folder_name=folder_name,
            content=MarkoContentBlock("", line_idx + 1, line_idx + 1),
            sections=[],
            chapter_number=None,  # Will be set later if needed
            appendix_letter=None,  # Will be set later if needed
        )

    def _process_section_heading(
        self,
        heading_element: Heading,
        line_idx: int,
        children: List[Any],
        chapter: MarkoChapter,
    ) -> None:
        """
        Process a section heading within a chapter.

        Args:
            heading_element: Marko heading element
            line_idx: Index of the heading in the document
            children: List of all document children
            chapter: Current chapter being processed
        """
        heading_text = self._extract_heading_text(heading_element)

        # Check if it's a numbered section
        match = self._section_pattern.match(heading_text)

        if match:
            # This is a numbered section - it gets its own file
            section_num = match.group(1)
            section_title = match.group(2).strip()

            # Create section
            section = MarkoSection(
                title=section_title,
                number=section_num,
                content=MarkoContentBlock("", line_idx + 1, line_idx + 1),
                filename=self._sanitize_filename(section_title),
                section_type="numbered",
            )

            # If this is the first numbered section, extract chapter content
            if not any(s.section_type == "numbered" for s in chapter.sections):
                self._extract_chapter_content_before_section(
                    children, chapter, line_idx
                )

            chapter.sections.append(section)
        else:
            # This is a content heading - it goes in the chapter's index.rst
            # We don't add it to sections list, just track it for content extraction
            pass

    def _extract_chapter_content_before_section(
        self, children: List[Any], chapter: MarkoChapter, section_line_idx: int
    ) -> None:
        """
        Extract chapter content that appears before the first section.

        Args:
            children: List of all document children
            chapter: Chapter to extract content for
            section_line_idx: Line number where the section appears
        """
        # Extract content from chapter heading to section heading
        content = self._extract_content_block(
            children, chapter.content.start_line - 1, section_line_idx
        )
        chapter.content = content

    def _finalize_chapter(
        self, children: List[Any], chapter: MarkoChapter, end_idx: int
    ) -> None:
        """
        Finalize a chapter by extracting any remaining content.

        Args:
            children: List of all document children
            chapter: Chapter to finalize
            end_idx: Index where chapter content ends
        """
        # If chapter has no sections, extract all content to the end
        if not chapter.sections:
            content = self._extract_content_block(
                children, chapter.content.start_line - 1, end_idx
            )
            chapter.content = content
        else:
            # Finalize all sections that haven't been finalized yet
            for section in chapter.sections:
                if section.content.start_line == section.content.end_line:
                    # Section content hasn't been extracted yet
                    # Find the next chapter or section heading (H2 or H3), or end of chapter
                    section_end = end_idx
                    for i in range(section.content.start_line, end_idx):
                        if i < len(children) and isinstance(children[i], Heading):
                            # Only stop at H2 (chapter) or H3 (section) headings
                            # H4+ headings should be included in the section content
                            if children[i].level <= 3:
                                section_end = i
                                break

                    section_content = self._extract_content_block(
                        children, section.content.start_line - 1, section_end
                    )
                    section.content = section_content

    def _sanitize_filename(self, title: str) -> str:
        """
        Convert section title to a safe filename.

        Args:
            title: Section title to convert

        Returns:
            Safe filename with .rst extension
        """
        # Remove or replace problematic characters
        filename = re.sub(r"[^\w\s-]", "", title)
        filename = re.sub(r"[-\s]+", "-", filename)
        filename = filename.strip("-").lower()

        # Ensure it's not empty
        if not filename:
            filename = "section"

        # Add .rst extension
        return f"{filename}.rst"
