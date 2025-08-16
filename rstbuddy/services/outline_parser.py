"""
Markdown outline parser service.

Parses markdown files to extract book structure including chapters, sections,
and content blocks for conversion to RST.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from ..models.outline import (
    BookOutline,
    Chapter,
    ContentBlock,
    HeadingType,
    Section,
)
from ..settings import Settings

#: Canonical regex pattern for section headings (two levels maximum)
SECTION_HEADING_PATTERN = r"^(\d+\.\d+|[A-Z]\.\d+)(?!\.\d)\s+(.*)"


class OutlineParser:
    """
    Parses markdown outlines to extract book structure.

    This class analyzes markdown files to identify the hierarchical structure
    of books, including chapters, sections, and content blocks. It handles
    various heading formats and distinguishes between numbered sections and
    content headings.

    """

    def __init__(self) -> None:
        """
        Initialize the outline parser.

        Sets up regex patterns for identifying different types of headings
        in markdown files.
        """
        #: Regex pattern for matching chapter headings
        self._chapter_pattern = re.compile(r"^Chapter\s+(\d+):\s*(.*)")
        #: Regex pattern for matching appendix headings
        self._appendix_pattern = re.compile(r"^Appendix\s+([A-Z]):\s*(.*)")
        #: Regex pattern for matching section headings
        self._section_pattern = re.compile(SECTION_HEADING_PATTERN)

    def parse_file(
        self, file_path: Path, output_dir: Path | None = None
    ) -> BookOutline:
        """
        Parse a markdown file to extract book outline structure.

        This is the main entry point for parsing markdown files. It reads
        the file, parses the structure, and returns a complete BookOutline
        object with all chapters, sections, and content properly organized.

        Args:
            file_path: Path to the markdown file to parse
            output_dir: Custom output directory (default: uses settings)

        Returns:
            BookOutline with complete structure

        Raises:
            OSError: If the file cannot be opened or read
            UnicodeDecodeError: If the file cannot be decoded with UTF-8 encoding

        Note:
            If no output_dir is provided, uses the documentation directory
            from the application settings.

        """
        with file_path.open(encoding="utf-8") as f:
            lines = f.readlines()

        # Parse the structure
        title, introduction_content, chapters = self._parse_structure(lines)

        # Determine output directory
        if output_dir is None:
            # Use settings documentation directory
            settings = Settings()
            output_dir = Path(settings.documentation_dir)
        else:
            output_dir = Path(output_dir)

        return BookOutline(
            title=title,
            introduction_content=introduction_content,
            chapters=chapters,
            output_dir=output_dir,
        )

    @dataclass
    class _ParsingState:
        """
        Internal class to hold parsing state during outline parsing.

        This class encapsulates all the state variables needed during the parsing
        process, providing a clean interface for managing the current parsing
        context without cluttering the main parsing methods.

        Note:
            This is an internal implementation detail and should not be used
            outside of the OutlineParser class. All attributes are managed
            by the parser methods during the parsing process.

        """

        #: The document title extracted from the first H1 heading
        title: str = ""
        #: Line number where the title heading appears
        title_line: int = 0
        #: Line number of the first chapter heading (H2)
        first_h2_line: int = 0
        #: Line number where current chapter content begins
        chapter_content_start: int = 0
        #: The Chapter object currently being processed
        current_chapter: Chapter | None = None
        #: The Section object currently being processed
        current_section: Section | None = None
        #: Line number where current section content begins
        section_content_start: int = 0
        #: List of completed Chapter objects
        chapters: list[Chapter] = field(default_factory=list)

    def _initialize_parsing_state(self) -> _ParsingState:
        """
        Initialize the parsing state object.

        Creates a new _ParsingState instance with all attributes set to
        their default values. This method encapsulates the initialization
        logic and ensures consistent state setup.

        Returns:
            A new _ParsingState instance ready for parsing operations

        Note:
            The parsing state tracks the current parsing context including
            the current chapter, section, content boundaries, and accumulated
            results. This state is maintained throughout the parsing process
            and updated by various helper methods.

        """
        return self._ParsingState()

    def _parse_structure(
        self, lines: list[str]
    ) -> tuple[str, ContentBlock, list[Chapter]]:
        """
        Parse the complete structure from lines.

        Analyzes the markdown content line by line to extract the book
        structure. Identifies headings at different levels and organizes
        content into appropriate blocks.

        This method orchestrates the parsing process by delegating to
        specialized methods for different aspects of parsing, making the
        code more maintainable and testable.

        Args:
            lines: List of lines from the markdown file to parse

        Returns:
            Tuple containing:
                - title: The book title (from first H1 heading)
                - introduction_content: Content between title and first chapter
                - chapters: List of parsed Chapter objects with sections and content

        Note:
            The parsing process follows this sequence:

            1. Initialize parsing state
            2. Process each heading line to identify structure
            3. Finalize any remaining content at end of file
            4. Extract introduction content between title and first chapter

            This method delegates the complex parsing logic to specialized
            helper methods, each handling a specific aspect of the parsing
            process.

        """
        # Initialize parsing state
        state = self._initialize_parsing_state()

        # Parse all headings and content
        for i, line in enumerate(lines):
            line_num = i + 1
            if line.startswith("#"):
                self._process_heading(line, line_num, lines, state)

        # Finalize any remaining content
        self._finalize_remaining_content(lines, state)

        # Extract introduction content
        introduction_content = self._extract_introduction_content(lines, state)

        return state.title, introduction_content, state.chapters

    def _process_heading(
        self, line: str, line_num: int, lines: list[str], state: _ParsingState
    ) -> None:
        """
        Process a single heading line and update parsing state.

        Analyzes a heading line to determine its level and content, then
        delegates processing to the appropriate specialized method based
        on the heading level (H1, H2, or H3).

        Args:
            line: The raw line containing the heading
            line_num: The line number (1-indexed) where the heading appears
            lines: Complete list of lines for context and content extraction
            state: Current parsing state to update

        Note:
            This method acts as a router, determining the heading level
            and delegating to the appropriate processor:

            - H1 headings -> _process_title_heading
            - H2 headings -> _process_chapter_heading
            - H3 headings -> _process_section_heading (only if within a chapter)

            The heading level is determined by counting the number of '#' characters
            at the beginning of the line.

        """
        level = len(line) - len(line.lstrip("#"))
        heading_text = line.strip()[level:].strip()

        if level == 1 and not state.title:
            self._process_title_heading(heading_text, line_num, state)
        elif level == 2:  # noqa: PLR2004
            self._process_chapter_heading(heading_text, line_num, lines, state)
        elif level == 3 and state.current_chapter:  # noqa: PLR2004
            self._process_section_heading(heading_text, line_num, lines, state)

    def _process_title_heading(
        self, heading_text: str, line_num: int, state: _ParsingState
    ) -> None:
        """
        Process the document title (H1) heading.

        Sets the document title and initializes the parsing state for
        the beginning of the document. This method is only called for
        the first H1 heading encountered.

        Args:
            heading_text: The text content of the title heading
            line_num: Line number where the title appears
            state: Parsing state to update with title information

        Note:
            The title heading establishes the starting point for content
            extraction. Content between the title and the first chapter
            (H2) will be treated as introduction content.

            This method sets:

            - state.title: The document title text
            - state.title_line: Line number for content boundary calculation
            - state.chapter_content_start: Starting point for chapter content

        """
        state.title = heading_text
        state.title_line = line_num
        state.chapter_content_start = line_num

    def _process_chapter_heading(
        self, heading_text: str, line_num: int, lines: list[str], state: _ParsingState
    ) -> None:
        """
        Process a chapter (H2) heading.

        Handles the transition between chapters by finalizing the previous
        chapter (if any) and starting a new chapter. This method manages
        the chapter-level content boundaries and state transitions.

        Args:
            heading_text: The text content of the chapter heading
            line_num: Line number where the chapter heading appears
            lines: Complete list of lines for content extraction
            state: Parsing state to update with chapter information

        Note:
            This method performs several key operations:

            1. Finalizes the previous chapter by extracting its content
            2. Creates a new Chapter object from the heading text
            3. Updates parsing state for the new chapter context
            4. Records the first H2 line for introduction content calculation

            Chapter headings establish the major structural divisions of
            the document and reset the section context.

        """
        # Finalize the previous chapter if it exists
        if state.current_chapter:
            self._finalize_chapter(lines, state)

        # Start a new chapter
        state.current_chapter = self._parse_chapter_heading(heading_text, line_num)
        if not state.first_h2_line:
            state.first_h2_line = line_num
        state.chapter_content_start = line_num
        state.current_section = None

    def _process_section_heading(
        self, heading_text: str, line_num: int, lines: list[str], state: _ParsingState
    ) -> None:
        """
        Process a section heading by creating a Section object and handling
        content extraction.

        Creates a new Section object from the parsed heading and determines
        whether it's a content heading (no filename) or a real numbered section.
        For content headings, adds their content to the chapter. For real sections,
        extracts any chapter content that appears before the first section.

        Args:
            heading_text: The section heading text to process
            line_num: Line number where the section heading appears
            lines: Complete list of lines for content extraction
            state: Parsing state containing the current chapter and section

        Note:
            This method handles two types of H3 headings:

            1. Content headings (e.g., "Summary", "Learning Goals"): These are
               added to the chapter's main content and don't create separate files.
            2. Numbered sections (e.g., "1.1 Introduction"): These create separate
               files and trigger chapter content extraction.

            When the first numbered section is encountered, any content between
            the chapter heading and that section is extracted as chapter content.
        """
        # Finalize the previous section if it exists
        if state.current_section:
            self._finalize_section(lines, state, line_num)

        section = self._parse_section_heading(heading_text, line_num)

        if section.filename == "":
            # This is a content heading - only process it if the chapter has no sections yet
            # For chapters with sections, content headings should not be included in chapter content
            if state.current_chapter and len(state.current_chapter.sections) == 0:
                self._handle_content_heading(lines, line_num, state)
        else:
            # This is a real numbered section
            # If it's the first numbered section, extract chapter content before it
            if state.current_chapter and len(state.current_chapter.sections) == 0:
                self._extract_chapter_content_before_section(lines, state, line_num)
            # Start tracking it
            state.current_section = section
            state.section_content_start = line_num

    def _finalize_chapter(self, lines: list[str], state: _ParsingState) -> None:
        """
        Finalize the current chapter by adding it to the chapters list.

        Completes the processing of the current chapter by extracting any
        remaining content and adding the completed chapter to the results.
        This method is called when transitioning to a new chapter or at
        the end of the document.

        Args:
            lines: Complete list of lines for content extraction
            state: Parsing state containing the current chapter to finalize

        Note:
            This method handles two scenarios:

            1. Chapter with sections: Finalizes the last section and adds chapter
            2. Chapter without sections: Extracts chapter content to end of file

            After finalization, the chapter is added to the chapters list and
            becomes part of the final document structure.

        """
        if not state.current_chapter:
            return

        if len(state.current_chapter.sections) > 0:
            # Chapter has sections - finalize the last section if it exists
            if state.current_section:
                self._finalize_section(lines, state, len(lines))
        else:
            # Chapter has no sections - extract all content from chapter heading to next chapter
            next_heading_line = self._find_next_heading_after_chapter(
                lines, state.chapter_content_start
            )
            state.current_chapter.content = self._extract_content_block(
                lines, state.chapter_content_start, next_heading_line - 1
            )

        state.chapters.append(state.current_chapter)

    def _finalize_section(
        self, lines: list[str], state: _ParsingState, next_line: int
    ) -> None:
        """
        Finalize the current section by adding it to the current chapter.

        Completes the processing of the current section by extracting its
        content and adding it to the current chapter's sections list.
        This method is called when transitioning to a new section or
        when finalizing a chapter.

        Args:
            lines: Complete list of lines for content extraction
            state: Parsing state containing the current section to finalize
            next_line: Line number where the next section/chapter begins

        Note:
            This method extracts content from the section heading to the
            next section/chapter heading, creating a ContentBlock that represents
            the section's content. The completed section is then added
            to the current chapter's sections list.

            The method includes safety checks to ensure both current_chapter
            and current_section exist before processing.
        """
        if not state.current_chapter or not state.current_section:
            return

        state.current_section.content = self._extract_content_block(
            lines, state.section_content_start, next_line - 1
        )
        state.current_chapter.sections.append(state.current_section)

        # Clear the current section after finalizing it
        state.current_section = None

    def _extract_chapter_content_before_section(
        self, lines: list[str], state: _ParsingState, line_num: int
    ) -> None:
        """
        Extract chapter content that appears before the first section.

        When the first section heading is encountered within a chapter,
        this method extracts any content that appears between the chapter
        heading and the section heading. This content becomes part of
        the chapter's main content block.

        Args:
            lines: Complete list of lines for content extraction
            state: Parsing state containing the current chapter
            line_num: Line number where the section heading appears

        Note:
            This method is called only when processing the first section
            within a chapter. It ensures that any introductory content
            or content that doesn't belong to a specific section is
            properly captured as part of the chapter's main content.

            The content is extracted from the chapter heading line to
            the line before the section heading.
        """
        if not state.current_chapter:
            return

        # Extract content from chapter heading to the section heading
        state.current_chapter.content = self._extract_content_block(
            lines, state.chapter_content_start, line_num - 1
        )

    def _handle_content_heading(
        self, lines: list[str], line_num: int, state: _ParsingState
    ) -> None:
        """
        Handle a content heading (non-numbered H3) by adding its content to
        chapter content.

        Processes H3 headings that don't follow the numbered section pattern
        (e.g., "Summary", "Learning Objectives"). These headings are treated
        as content within the parent chapter rather than as separate sections.

        Args:
            lines: Complete list of lines for content extraction
            line_num: Line number where the content heading appears
            state: Parsing state containing the current chapter

        Note:
            This method performs several key operations:

            1. Finds the boundary for the content (next heading or end of file)
            2. Extracts the content block from the heading to the boundary
            3. Appends the content to the chapter's main content block
            4. Resets the current_section to None since this is not a real section

            Content headings are important for maintaining the logical flow
            of chapter content while avoiding the creation of unnecessary
            separate files.

            IMPORTANT: This method is only called for chapters WITHOUT sections.
            For chapters WITH sections, content headings are not processed here.
        """
        if not state.current_chapter:
            return

        # Extract content from this heading to the next heading or end of file
        content_end = self._find_next_heading_end(lines, line_num)

        content_block = self._extract_content_block(lines, line_num, content_end)

        # Append to existing chapter content
        if state.current_chapter.content.content:
            state.current_chapter.content.content += "\n\n" + content_block.content
        else:
            state.current_chapter.content = content_block

        # Don't add content headings to sections list - they're just content
        state.current_section = None

    def _find_next_heading_end(self, lines: list[str], start_line: int) -> int:
        """
        Find the line number where the next heading of the same or higher level ends.

        Scans forward from the given line number to find the next H3 heading
        and determines if it's a numbered section (which would end the content heading)
        or a content heading (which would indicate we've moved to the next chapter).

        Args:
            lines: List of all lines from the markdown file
            start_line: Line number to start scanning from (0-indexed)

        Returns:
            Line number where the next H3 heading appears, or len(lines) if no
            more H3 headings are found

        Note:
            This method is used to determine content boundaries for content
            headings (non-numbered H3s). It looks for H3 headings and determines
            whether they represent section boundaries or content heading boundaries
            by checking if they follow the numbered section pattern.

            The returned line number represents the exclusive end boundary,
            meaning content extraction should go up to but not include this line.

        """
        for i in range(start_line, len(lines)):
            line = lines[i].strip()
            if line.startswith("###"):
                # Check if this is a numbered section or a content heading
                heading_text = line[3:].strip()
                if re.match(r"^(\d+\.\d+|[A-Z]\.\d+)\b", heading_text):
                    # This is a numbered section - it ends the content heading
                    return i
                else:
                    # This is another content heading - continue looking for a numbered section
                    continue
        return len(lines)

    def _find_next_heading_after_chapter(
        self, lines: list[str], chapter_start: int
    ) -> int:
        """
        Find the next heading (H2 or H3) after a chapter position.

        Scans forward from the given position to find the next heading that
        would indicate the end of the current chapter's content.

        Args:
            lines: Complete list of lines to scan
            chapter_start: Line number where the chapter starts (1-indexed)

        Returns:
            Line number of the next heading, or len(lines) if no heading found

        Note:
            This method looks for both H2 (chapter) and H3 (section) headings
            since either would indicate the end of the current chapter's content.
            H2 headings start new chapters, while H3 headings start new sections
            within the current chapter.

            IMPORTANT: Content headings (like "Summary", "Learning Goals") are
            NOT treated as boundaries - only numbered section headings are.
        """
        for i in range(chapter_start, len(lines)):
            line = lines[i].strip()
            if line.startswith("##") and not line.startswith("###"):
                # Found next chapter heading (H2)
                return i
            elif line.startswith("###"):
                # Found H3 heading - check if it's a numbered section or content heading
                heading_text = line[3:].strip()
                if re.match(r"^(\d+\.\d+|[A-Z]\.\d+)(?!\.\d)", heading_text):
                    # This is a numbered section - it ends chapter content
                    return i
                # This is a content heading - continue looking for a numbered section
                continue
        # No more headings found, content extends to end of file
        return len(lines)

    def _finalize_remaining_content(
        self, lines: list[str], state: _ParsingState
    ) -> None:
        """
        Finalize any remaining chapter and section content at the end of the file.

        Called after processing all headings to ensure that any remaining
        content at the end of the file is properly captured and added
        to the final document structure.

        Args:
            lines: Complete list of lines for content extraction
            state: Parsing state containing any remaining content to finalize

        Note:
            This method handles the end-of-file scenario where content
            appears after the last heading. It ensures that:

            1. The last section (if any) is finalized with its content
            2. The last chapter (if any) is finalized with its content
            3. All content is properly extracted and added to the results

            This is crucial for documents where the last chapter or section
            has content that extends to the end of the file.

        """
        if state.current_chapter:
            if state.current_section:
                # Finalize the last section
                state.current_section.content = self._extract_content_block(
                    lines, state.section_content_start, len(lines)
                )
                state.current_chapter.sections.append(state.current_section)
            else:
                # Chapter has no sections - extract content from chapter heading
                # to end of file
                state.current_chapter.content = self._extract_content_block(
                    lines, state.chapter_content_start, len(lines)
                )
            state.chapters.append(state.current_chapter)

    def _extract_introduction_content(
        self, lines: list[str], state: _ParsingState
    ) -> ContentBlock:
        """
        Extract introduction content between title and first chapter.

        Identifies and extracts content that appears between the document
        title (H1) and the first chapter heading (H2). This content
        becomes the introduction section of the document.

        Args:
            lines: Complete list of lines for content extraction
            state: Parsing state containing title and chapter boundary information

        Returns:
            ContentBlock containing the introduction content, or an empty
            ContentBlock if no introduction content exists

        Note:
            This method is called after all chapters have been processed
            to extract the document-level introduction content. It requires:

            - At least one chapter to exist
            - Valid title and first chapter line numbers
            - Content between the title and first chapter

            The introduction content is typically used for document-level
            information such as overview, prerequisites, or general context
            that applies to the entire document.

        """
        if state.chapters and state.title_line and state.first_h2_line:
            return self._extract_content_block(
                lines, state.title_line, state.first_h2_line - 1
            )
        return ContentBlock("", 0, 0)

    def _parse_chapter_heading(self, text: str, line_number: int) -> Chapter:
        """
        Parse a chapter heading to determine type and metadata.

        Analyzes chapter heading text to determine the chapter type
        (prologue, introduction, chapter, or appendix) and extract
        relevant metadata like chapter numbers or appendix letters.

        Args:
            text: The chapter heading text to parse
            line_number: Line number where the heading appears

        Returns:
            Chapter object with appropriate type and metadata

        Note:
            Handles various chapter heading formats:

            - "Prologue" -> Prologue chapter
            - "Introduction" -> Introduction chapter
            - "Chapter 1: Title" -> Numbered chapter
            - "Appendix A: Title" -> Appendix chapter

        """
        if text.startswith("Prologue"):
            return Chapter(
                title=text,
                heading_type=HeadingType.PROLOGUE,
                folder_name="prologue",
                content=ContentBlock("", line_number, line_number),
                sections=[],
            )
        if text.startswith("Introduction"):
            return Chapter(
                title=text,
                heading_type=HeadingType.INTRODUCTION,
                folder_name="introduction",
                content=ContentBlock("", line_number, line_number),
                sections=[],
            )
        if match := self._chapter_pattern.match(text):
            chapter_num = int(match.group(1))
            return Chapter(
                title=text,
                heading_type=HeadingType.CHAPTER,
                folder_name=f"chapter{chapter_num}",
                content=ContentBlock("", line_number, line_number),
                sections=[],
                chapter_number=chapter_num,
            )
        if text.startswith("Appendix "):
            # Handle new appendix format: Appendix A, Appendix A.1, Appendix B.2.1, etc.
            appendix_part = text[9:]  # Remove "Appendix " prefix

            # Extract just the letter part (before any colon or space)
            if ":" in appendix_part:
                # Format: "A: Architecture shape: Monolith package vs many
                # focused Lambdas"
                base_letter = appendix_part.split(":")[0].strip()
            elif "." in appendix_part:
                # Format: "A.1" - extract just the base letter
                base_letter = appendix_part.split(".")[0].strip()
            else:
                # Format: "A" - just a single letter
                base_letter = appendix_part.strip()

            # Ensure we only have a single letter
            if len(base_letter) == 1 and base_letter.isalpha():
                folder_name = f"appendix{base_letter}"
            else:
                # Fallback if parsing fails
                folder_name = "appendix_unknown"

            return Chapter(
                title=text,
                heading_type=HeadingType.APPENDIX,
                folder_name=folder_name,
                content=ContentBlock("", line_number, line_number),
                sections=[],
                appendix_letter=base_letter,
            )
        # This shouldn't happen if validation passed, but handle gracefully
        return Chapter(
            title=text,
            heading_type=HeadingType.CHAPTER,
            folder_name="unknown",
            content=ContentBlock("", line_number, line_number),
            sections=[],
        )

    def _parse_section_heading(self, text: str, line_number: int) -> Section:
        """
        Parse a section heading to extract number and title.

        Analyzes section heading text to determine if it's a numbered
        section or a content heading. Creates appropriate Section objects
        with filenames for numbered sections and empty filenames for content.

        Args:
            text: The section heading text to parse
            line_number: Line number where the heading appears

        Returns:
            Section object with appropriate metadata

        Note:
            This method distinguishes between:

            - Numbered sections (1.1, 2.3, etc.) -> get filenames
            - Appendix sections (D.1, A.2, etc.) -> get filenames
            - Content headings (Summary, Learning Goals, etc.) -> no filename

            Note: Only two-level nesting is supported (e.g., 1.1, not 1.1.1)

        """
        # Clean the text first
        text = text.strip()

        # Try section pattern (1.1, 2.3, A.1, B.2, etc.)
        match = re.match(SECTION_HEADING_PATTERN, text)
        if match:
            number = match.group(1)
            title = match.group(2).strip()  # Clean title without numbers

            # If title is empty, use a default
            if not title:
                title = f"Section {number}"

            # Use the cleaned title for filename
            filename = self._sanitize_filename(title)

            return Section(
                title=title,
                number=number,
                content=ContentBlock("", line_number, line_number),
                filename=filename,
            )

        # Handle content headings (like Summary, Learning Goals, Example Types)
        # These are NOT sections - they're content that goes into the
        # chapter/appendix index.rst Create a special section with empty
        # filename to indicate it's content, not a separate file
        return Section(
            title=text,
            number="",  # No number for content headings
            content=ContentBlock("", line_number, line_number),
            filename="",  # Empty filename indicates this is content, not a section file
        )

    def _extract_content_block(
        self, lines: list[str], start_line: int, end_line: int
    ) -> ContentBlock:
        """
        Extract content between two line numbers.

        Creates a ContentBlock object containing all content between
        the specified start and end line numbers. Handles edge cases
        like invalid line ranges gracefully.

        Args:
            lines: List of all lines from the markdown file
            start_line: Starting line number (1-indexed)
            end_line: Ending line number (1-indexed)

        Returns:
            ContentBlock containing the extracted content

        Note:
            Line numbers are 1-indexed for user-friendly error reporting.
            The method converts to 0-indexed for list operations.

        """
        if start_line > end_line or start_line > len(lines):
            return ContentBlock("", start_line, end_line)

        # Adjust to 0-based indexing
        start_idx = start_line - 1
        end_idx = min(end_line, len(lines))

        content_lines = lines[start_idx:end_idx]
        content = "".join(content_lines)

        return ContentBlock(content, start_line, end_line)

    def _sanitize_filename(self, title: str) -> str:
        """
        Convert section title to a safe filename.

        Transforms section titles into filesystem-safe filenames by
        removing or replacing problematic characters and normalizing
        the format.

        Args:
            title: Section title to convert to filename

        Returns:
            Safe filename with .rst extension

        Note:
            The sanitization process:

            1. Removes non-word characters (except spaces and hyphens)
            2. Replaces multiple spaces/hyphens with single hyphens
            3. Trims leading/trailing hyphens
            4. Converts to lowercase
            5. Adds .rst extension

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
