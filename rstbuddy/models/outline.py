"""
Models for outline conversion from Markdown to RST structure.

This module contains the core models needed for validation and
other outline-related functionality.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional


class HeadingType(Enum):
    """Types of headings in the outline."""

    BOOK_TITLE = "book_title"
    PROLOGUE = "prologue"
    INTRODUCTION = "introduction"
    CHAPTER = "chapter"
    APPENDIX = "appendix"


@dataclass
class ContentBlock:
    """A block of content between headings."""

    content: str
    line_start: int
    line_end: int


@dataclass
class Section:
    """A section within a chapter."""

    title: str
    number: str  # e.g., "1.1", "2.3.1"
    content: ContentBlock
    filename: str  # sanitized filename


@dataclass
class Chapter:
    """A chapter in the book."""

    title: str
    heading_type: HeadingType
    folder_name: str
    content: ContentBlock
    sections: List[Section]
    chapter_number: Optional[int] = None
    appendix_letter: Optional[str] = None


@dataclass
class BookOutline:
    """Complete book outline structure."""

    title: str
    introduction_content: ContentBlock
    chapters: List[Chapter]
    output_dir: Path


@dataclass
class ValidationError:
    """Validation error details."""

    line_number: int
    message: str
    severity: str = "error"


@dataclass
class ValidationResult:
    """Result of markdown validation."""

    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
