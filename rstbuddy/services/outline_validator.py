"""
Markdown outline validation service using Marko.

Validates markdown files for proper structure and heading hierarchy
required for outline conversion.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import marko
from marko.block import Heading

from ..exc import FileError
from ..models.outline import ValidationError, ValidationResult
from ..services.outline_parser import SECTION_HEADING_PATTERN

if TYPE_CHECKING:
    from pathlib import Path

    from marko.element import Element


class OutlineValidator:
    """
    Validates markdown outlines for proper structure and heading hierarchy.

    This class uses the Marko parser to analyze markdown files and validate
    their structure according to the requirements for outline conversion.
    It checks heading hierarchy, validates chapter and section patterns,
    and ensures the document follows the expected format.

    """

    def __init__(self) -> None:
        """
        Initialize the outline validator.

        Sets up regex patterns for validating different types of headings
        in markdown files.
        """
        #: Regex pattern for validating chapter headings
        self._chapter_pattern = re.compile(
            r"^(Prologue|Introduction|Chapter\s+\d+:|Appendix\s+[A-Z](?:\.[0-9]+)?)"
        )

    def validate_file(self, file_path: Path) -> ValidationResult:
        """
        Validate a markdown file for outline structure.

        This is the main entry point for validation. It reads the markdown
        file, parses it using Marko, and performs various validation checks
        to ensure the document meets the requirements for outline conversion.

        Args:
            file_path: Path to the markdown file to validate

        Returns:
            ValidationResult with validation status and any errors/warnings

        Raises:
            FileError: If the file cannot be read

        Note:
            The validation process includes:

            1. Basic markdown syntax validation
            2. Heading hierarchy validation
            3. Chapter and section pattern validation
            4. Structure consistency checks

        """
        try:
            with file_path.open(encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            msg = f"Failed to read markdown file: {e!s}"
            raise FileError(msg) from e

        try:
            # Parse markdown with Marko
            markdown_doc = marko.parse(content)

            errors = []

            # Check for basic markdown syntax errors
            syntax_errors = self._check_basic_syntax(content)
            errors.extend(syntax_errors)

            # Check heading hierarchy and patterns using parsed AST
            structure_errors = self._check_heading_structure(markdown_doc)
            errors.extend(structure_errors)

            is_valid = len([e for e in errors if e.severity == "error"]) == 0

            return ValidationResult(
                is_valid=is_valid,
                errors=[e for e in errors if e.severity == "error"],
                warnings=[e for e in errors if e.severity == "warning"],
            )

        except (AttributeError, ValueError, TypeError) as e:
            # If validation fails due to unexpected data structure, return a
            # validation error
            error = ValidationError(
                line_number=1,
                message=f"Failed to validate markdown structure: {e!s}",
                severity="error",
            )
            return ValidationResult(is_valid=False, errors=[error], warnings=[])

    def _check_basic_syntax(self, content: str) -> list[ValidationError]:
        """
        Check for basic markdown syntax issues and section nesting violations.

        Scans the markdown content for:
        1. Section numbering with more than two levels (e.g., 1.1.1, A.1.1)
        2. Basic markdown syntax issues

        Args:
            content: Markdown content to check

        Returns:
            List of validation errors for syntax violations

        Note:
            This method enforces the two-level nesting limit for sections
            and chapters as required by the outline structure.

        """
        errors = []

        # Check for section numbering with more than two levels
        # Pattern for chapters: 1.1.1, 2.3.4, etc.
        deep_chapter_sections = re.finditer(
            r"^#+\s*(\d+\.\d+\.\d+)", content, re.MULTILINE
        )
        for match in deep_chapter_sections:
            errors.append(  # noqa: PERF401
                ValidationError(
                    line_number=content[: match.start()].count("\n") + 1,
                    message=(
                        f"Section numbering '{match.group(1)}' exceeds maximum of "
                        "two levels. Do not number section headings within chapters.'"
                    ),
                    severity="error",
                )
            )

        # Pattern for appendices: A.1.1, B.2.3, etc.
        deep_appendix_sections = re.finditer(
            r"^#+\s*([A-Z]\.\d+\.\d+)", content, re.MULTILINE
        )
        for match in deep_appendix_sections:
            errors.append(
                ValidationError(
                    line_number=content[: match.start()].count("\n") + 1,
                    message=f"Appendix section numbering '{match.group(1)}' exceeds maximum of two levels. Use format 'X.Y' instead of 'X.Y.Z'",
                    severity="error",
                )
            )

        return errors

    @dataclass
    class _ValidationState:
        """
        Internal class to hold validation state during heading structure validation.

        This class encapsulates the state needed during the validation process,
        including extracted headings, validation errors, and processing context.

        Note:
            This is an internal implementation detail and should not be used
            outside of the OutlineValidator class.

        """

        headings: list[tuple[int, str, Any]] = field(default_factory=list)
        errors: list[ValidationError] = field(default_factory=list)
        current_index: int = 0

    def _check_heading_structure(self, markdown_doc: Element) -> list[ValidationError]:
        """
        Check heading structure using parsed markdown AST.

        Analyzes the parsed markdown document to validate heading hierarchy
        and patterns. Ensures proper nesting, validates chapter and section
        formats, and checks for structural consistency.

        Args:
            markdown_doc: Parsed markdown document from Marko

        Returns:
            List of validation errors and warnings

        Raises:
            AttributeError: If markdown document structure is unexpected

        Note:
            This method orchestrates the validation process by delegating
            to specialized methods for different aspects of validation.

        """
        # Initialize validation state
        state = self._ValidationState()

        # Extract all headings from the parsed document
        self._extract_headings(markdown_doc, state)

        # Check for basic document structure
        if not state.headings:
            state.errors.append(
                ValidationError(
                    line_number=1,
                    message="Document must contain at least one heading",
                    severity="error",
                )
            )
            return state.errors

        # Validate heading hierarchy and patterns
        self._validate_heading_hierarchy(state)
        self._validate_heading_patterns(state)

        return state.errors

    def _extract_headings(self, markdown_doc: Element, state: _ValidationState) -> None:
        """
        Extract all headings from the parsed markdown document.

        Safely extracts heading information including level, text content,
        and element reference from the Marko AST.

        Args:
            markdown_doc: Parsed markdown document from Marko
            state: Validation state to update with extracted headings

        Note:
            This method handles the complexity of safely extracting text content
            from Marko heading elements, which can have nested structure.

        """
        for element in markdown_doc.children:  # type: ignore[attr-defined]
            if isinstance(element, Heading):
                heading_text = self._extract_heading_text(element)
                state.headings.append((element.level, heading_text, element))

    def _extract_heading_text(self, heading_element: Heading) -> str:
        """
        Extract text content from a heading element safely.

        Safely extracts the text content from a Marko Heading element,
        handling various nested structures that may be present.

        Args:
            heading_element: The Heading element to extract text from

        Returns:
            The extracted heading text as a string

        Note:
            This method handles the complexity of Marko's heading structure
            where text content may be nested in various ways.

        """
        try:
            children = getattr(heading_element, "children", [])
            if children and len(children) > 0:
                first_child = children[0]
                if hasattr(first_child, "children"):
                    # If it has children, join them to get the text
                    return "".join(str(child) for child in first_child.children)
                # Otherwise use the string representation
                return str(first_child)
            return str(heading_element)
        except (AttributeError, IndexError):
            # If we can't extract text safely, fall back to string representation
            return str(heading_element)

    def _validate_heading_hierarchy(self, state: _ValidationState) -> None:
        """
        Validate that heading levels follow proper hierarchy.

        Ensures that heading levels don't skip levels (e.g., H1 -> H3)
        and that the document starts with a level 1 heading.

        Args:
            state: Validation state containing headings and errors

        Note:
            This method checks for proper heading nesting and ensures
            the document structure follows valid markdown hierarchy rules.

        """
        for i, (level, _heading_text, _) in enumerate(state.headings):
            if i == 0 and level != 1:
                state.errors.append(
                    ValidationError(
                        line_number=1,
                        message=(
                            "Document must start with a level 1 heading (book title)"
                        ),
                        severity="error",
                    )
                )
            elif i > 0:
                prev_level = state.headings[i - 1][0]
                if level > prev_level + 1:
                    state.errors.append(
                        ValidationError(
                            line_number=1,  # Marko doesn't preserve line numbers easily
                            message=(
                                f"Invalid heading hierarchy: level {level} heading "
                                f"cannot follow level {prev_level} heading"
                            ),
                            severity="error",
                        )
                    )

    def _validate_heading_patterns(self, state: _ValidationState) -> None:
        """
        Validate heading patterns based on their level and context.

        Checks that chapter headings (H2) and section headings (H3) follow
        the required patterns for the document structure.

        Args:
            state: Validation state containing headings and errors

        Note:
            This method validates the specific format requirements for
            different heading levels, including special handling for
            appendix sections.

        """
        for i, (level, heading_text, _) in enumerate(state.headings):
            if level == 2:  # noqa: PLR2004
                self._validate_chapter_heading(heading_text, state)
            elif level == 3:  # noqa: PLR2004
                self._validate_section_heading(heading_text, i, state)

    def _validate_chapter_heading(
        self, heading_text: str, state: _ValidationState
    ) -> None:
        """
        Validate that a chapter heading follows the required pattern.

        Checks that H2 headings match the expected format for chapters,
        including Prologue, Introduction, numbered chapters, and appendices.

        Args:
            heading_text: The text content of the chapter heading
            state: Validation state to update with any errors

        Note:
            Chapter headings must follow specific patterns to ensure
            proper document structure generation.

        """
        if not self._chapter_pattern.match(heading_text):
            state.errors.append(
                ValidationError(
                    line_number=1,
                    message=(
                        f"Invalid chapter heading: '{heading_text}'. Must start"
                        " with 'Prologue', 'Introduction', 'Chapter [number]:',"
                        " or 'Appendix [letter]:'"
                    ),
                    severity="error",
                )
            )

    def _validate_section_heading(
        self, heading_text: str, heading_index: int, state: _ValidationState
    ) -> None:
        """
        Validate that a section heading follows the required pattern.

        Checks that H3 headings are either valid numbered sections or
        content headings, with special handling for appendix sections.

        Args:
            heading_text: The text content of the section heading
            heading_index: Index of the heading in the headings list
            state: Validation state to update with any errors

        Note:
            Section headings can be either numbered sections (which get
            their own files) or content headings (which are treated as
            content within the parent chapter).

        """
        # Check if this is a numbered section heading
        if re.match(SECTION_HEADING_PATTERN, heading_text):
            # This is a valid numbered section heading
            return

        # Find the parent chapter to determine context
        parent_chapter = self._find_parent_chapter(heading_index, state)

        if parent_chapter and parent_chapter.startswith("Appendix "):
            # Under appendix chapter - allow letter.number pattern (e.g., A.1, B.2)
            if re.match(r"^[A-Z]\.\d+$", heading_text):
                # This is a valid numbered appendix section heading
                return

        # This is an unnumbered H3 heading - treat as content, not a section
        # No validation needed for content headings

    def _find_parent_chapter(
        self, heading_index: int, state: _ValidationState
    ) -> str | None:
        """
        Find the parent chapter heading for a given section heading.

        Searches backwards from the current heading to find the most
        recent chapter heading (H2) that precedes this section.

        Args:
            heading_index: Index of the current heading in the headings list
            state: Validation state containing all headings

        Returns:
            The text of the parent chapter heading, or None if not found

        Note:
            This method is used to determine the context for section
            validation, particularly for appendix sections which have
            different validation rules.

        """
        for j in range(heading_index - 1, -1, -1):
            if state.headings[j][0] == 2:  # noqa: PLR2004
                return state.headings[j][1]
        return None
