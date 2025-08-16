"""
Marko-based outline models.

This module contains data models for representing document outlines
parsed using Marko's AST approach. These models are designed to be
independent of the existing regex-based parser models.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List


class MarkoHeadingType(Enum):
    """Types of headings in the document outline."""

    TITLE = "title"
    CHAPTER = "chapter"
    APPENDIX = "appendix"
    INTRODUCTION = "introduction"
    PROLOGUE = "prologue"


@dataclass
class MarkoContentBlock:
    """
    Represents a block of content in the document.

    This class stores content along with its position information
    for accurate reconstruction and debugging.
    """

    content: str
    start_line: int
    end_line: int

    def __post_init__(self) -> None:
        """Validate content block data."""
        if self.start_line > self.end_line:
            raise ValueError("start_line cannot be greater than end_line")
        if self.start_line < 1:
            raise ValueError("start_line must be 1 or greater")


@dataclass
class MarkoSection:
    """
    Represents a section within a chapter or appendix.

    Sections can be either numbered (like "1.1 Introduction") or
    content headings (like "Summary", "Learning Goals").
    """

    title: str
    number: str  # Empty string for content headings
    content: MarkoContentBlock
    filename: str  # Empty string for content headings
    section_type: str  # "numbered" or "content"

    def __post_init__(self) -> None:
        """Validate section data."""
        if not self.title:
            raise ValueError("Section title cannot be empty")
        if self.section_type not in ["numbered", "content"]:
            raise ValueError("section_type must be 'numbered' or 'content'")


@dataclass
class MarkoChapter:
    """
    Represents a chapter or appendix in the document.

    Chapters contain sections and content, and are the main
    organizational units of the document.
    """

    title: str
    heading_type: MarkoHeadingType
    folder_name: str
    content: MarkoContentBlock
    sections: List[MarkoSection]
    chapter_number: int | None = None  # For numbered chapters
    appendix_letter: str | None = None  # For appendices

    def __post_init__(self) -> None:
        """Validate chapter data."""
        if not self.title:
            raise ValueError("Chapter title cannot be empty")
        if not self.folder_name:
            raise ValueError("Chapter folder_name cannot be empty")


@dataclass
class MarkoBookOutline:
    """
    Represents the complete structure of a book document.

    This is the root model that contains the document title,
    introduction content, and all chapters.
    """

    title: str
    introduction_content: MarkoContentBlock
    chapters: List[MarkoChapter]
    output_dir: Path

    def __post_init__(self) -> None:
        """Validate book outline data."""
        if not self.title:
            raise ValueError("Book title cannot be empty")
        if not self.output_dir:
            raise ValueError("Output directory cannot be empty")
