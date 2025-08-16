"""
Tests for the convert-outline functionality.

This module tests the Markdown outline to RST conversion pipeline including:
- Outline validation
- Outline parsing
- RST conversion
- CLI command
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from rstbuddy.cli.cli import cli
from rstbuddy.models.outline import (
    BookOutline,
    Chapter,
    ContentBlock,
    HeadingType,
    Section,
)
from rstbuddy.services.outline_converter import OutlineConverter
from rstbuddy.services.outline_parser import OutlineParser
from rstbuddy.services.outline_validator import OutlineValidator
from rstbuddy.exc import FileError


@pytest.fixture
def sample_outline_md():
    """Create a sample Markdown outline for testing."""
    return """# Sample Book Title

This is introduction content between the title and first chapter.

## Introduction: How to use this book

Introduction content here.

### Summary
Summary content.

### Learning Goals
Learning goals content.

## Chapter 1: Getting Started

Chapter 1 content here.

### 1.1 First Steps
First steps content.

### 1.2 Next Steps
Next steps content.

## Chapter 2: Advanced Topics

Chapter 2 content here.

### 2.1 Advanced Concepts
Advanced concepts content.

### 2.2 Best Practices
Best practices content.

## Appendix A: Reference Material

Appendix content here.

### A.1 Quick Reference
Quick reference content.

### A.2 Detailed Reference
Detailed reference content.
"""


@pytest.fixture
def invalid_outline_md():
    """Create an invalid Markdown outline for testing validation errors."""
    return """# Sample Book Title

## Invalid Chapter (no proper prefix)

### Invalid Section (no number)

## Chapter 1: Valid Chapter

### 1.1 Valid Section
Content here.
"""


@pytest.fixture
def temp_outline_file(temp_dir, sample_outline_md):
    """Create a temporary Markdown outline file for testing."""
    outline_file = temp_dir / "test_outline.md"
    outline_file.write_text(sample_outline_md, encoding="utf-8")
    return outline_file


class TestOutlineValidator:
    """Test the outline validation functionality."""

    def test_validate_valid_outline(self, temp_dir, sample_outline_md):
        """Test that a valid outline passes validation."""
        # Create a temporary file for validation
        outline_file = temp_dir / "valid_outline.md"
        outline_file.write_text(sample_outline_md, encoding="utf-8")

        validator = OutlineValidator()
        result = validator.validate_file(outline_file)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_invalid_outline(self, temp_dir, invalid_outline_md):
        """Test that an invalid outline fails validation."""
        # Create a temporary file for validation
        outline_file = temp_dir / "invalid_outline.md"
        outline_file.write_text(invalid_outline_md, encoding="utf-8")

        validator = OutlineValidator()
        result = validator.validate_file(outline_file)

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_empty_content(self, temp_dir):
        """Test validation of empty content."""
        outline_file = temp_dir / "empty.md"
        outline_file.write_text("", encoding="utf-8")

        validator = OutlineValidator()
        result = validator.validate_file(outline_file)

        assert result.is_valid is False
        assert any(
            "Document must contain at least one heading" in str(error)
            for error in result.errors
        )

    def test_validate_missing_title(self, temp_dir):
        """Test validation when no H1 heading is found."""
        content = """## Introduction: How to use this book

### Summary
Content here.
"""
        outline_file = temp_dir / "no_title.md"
        outline_file.write_text(content, encoding="utf-8")

        validator = OutlineValidator()
        result = validator.validate_file(outline_file)

        assert result.is_valid is False
        # Check for any validation error since the exact message may vary
        assert len(result.errors) > 0

    def test_validate_duplicate_chapter_titles(self, temp_dir):
        """Test validation when duplicate chapter titles exist."""
        content = """# Sample Book

## Chapter 1: Getting Started
Content here.

## Chapter 1: Getting Started
Duplicate content.
"""
        outline_file = temp_dir / "duplicate.md"
        outline_file.write_text(content, encoding="utf-8")

        validator = OutlineValidator()
        result = validator.validate_file(outline_file)

        # This should pass validation since the validator doesn't check for duplicates
        # The parser will handle this gracefully
        assert result.is_valid is True

    def test_validate_deep_nesting_violations(self, temp_dir):
        """Test that deep nesting (more than two levels) is caught as an error."""
        content = """# Sample Book

## Chapter 1: Getting Started
Content here.

### 1.1 First Steps
First steps content.

#### 1.1.1 Sub-subsection
This should be invalid - too many levels.

### 1.2 Next Steps
Next steps content.

#### 1.2.1 Another deep subsection
This should also be invalid.

## Appendix A: Reference Material

### A.1 Quick Reference
Quick reference content.

#### A.1.1 Deep appendix subsection
This should be invalid for appendices too.
"""
        outline_file = temp_dir / "deep_nesting.md"
        outline_file.write_text(content, encoding="utf-8")

        validator = OutlineValidator()
        result = validator.validate_file(outline_file)

        assert result.is_valid is False
        assert len(result.errors) > 0

        # Check that we have errors for deep nesting
        error_messages = [str(error) for error in result.errors]
        assert any("exceeds maximum of two levels" in msg for msg in error_messages)
        assert any("1.1.1" in msg for msg in error_messages)
        assert any("1.2.1" in msg for msg in error_messages)
        assert any("A.1.1" in msg for msg in error_messages)


class TestOutlineParser:
    """Test the outline parsing functionality."""

    def test_parse_valid_outline(self, temp_dir, sample_outline_md):
        """Test parsing a valid outline."""
        # Create a temporary file for parsing
        outline_file = temp_dir / "valid_outline.md"
        outline_file.write_text(sample_outline_md, encoding="utf-8")

        parser = OutlineParser()
        outline = parser.parse_file(outline_file, temp_dir)

        assert outline.title == "Sample Book Title"
        assert (
            "introduction content between the title and first chapter"
            in outline.introduction_content.content
        )
        assert (
            len(outline.chapters) == 4
        )  # Introduction, Chapter 1, Chapter 2, Appendix A

        # Check chapter types
        assert outline.chapters[0].heading_type == HeadingType.INTRODUCTION
        assert outline.chapters[1].heading_type == HeadingType.CHAPTER
        assert outline.chapters[2].heading_type == HeadingType.CHAPTER
        assert outline.chapters[3].heading_type == HeadingType.APPENDIX

        # Check folder names
        assert outline.chapters[0].folder_name == "introduction"
        assert outline.chapters[1].folder_name == "chapter1"
        assert outline.chapters[2].folder_name == "chapter2"
        assert outline.chapters[3].folder_name == "appendixA"

    def test_parse_chapter_with_sections(self, temp_dir, sample_outline_md):
        """Test parsing chapters with sections."""
        outline_file = temp_dir / "valid_outline.md"
        outline_file.write_text(sample_outline_md, encoding="utf-8")

        parser = OutlineParser()
        outline = parser.parse_file(outline_file, temp_dir)

        chapter1 = outline.chapters[1]  # Chapter 1: Getting Started
        assert len(chapter1.sections) == 2
        # The parser cleans the titles, so we expect the cleaned version
        assert chapter1.sections[0].title == "First Steps"
        assert chapter1.sections[0].filename == "first-steps.rst"
        assert chapter1.sections[1].title == "Next Steps"
        assert chapter1.sections[1].filename == "next-steps.rst"

    def test_parse_appendix_with_letter_sections(self, temp_dir):
        """Test parsing an appendix with letter-based section numbering."""
        content = """# Sample Book

## Appendix A: Reference Material

### A.1 Quick Reference
Quick reference content.

### A.2 Detailed Reference
Detailed reference content.
"""
        outline_file = temp_dir / "appendix_outline.md"
        outline_file.write_text(content, encoding="utf-8")

        parser = OutlineParser()
        outline = parser.parse_file(outline_file, temp_dir)

        assert outline.title == "Sample Book"
        assert len(outline.chapters) == 1
        appendix = outline.chapters[0]
        assert appendix.title == "Appendix A: Reference Material"
        assert len(appendix.sections) == 2
        assert appendix.sections[0].title == "Quick Reference"
        assert appendix.sections[1].title == "Detailed Reference"

    def test_parse_two_level_nesting_limitation(self, temp_dir):
        """Test that the parser correctly handles the two-level nesting limitation."""
        content = """# Sample Book

## Chapter 1: Getting Started

### 1.1 First Steps
First steps content.

### 1.2 Next Steps
Next steps content.

### 1.1.1 Deep Subsection
This should be treated as a content heading, not a section.

### 1.2.1 Another Deep Subsection
This should also be treated as a content heading.

## Appendix A: Reference

### A.1 Quick Reference
Quick reference content.

### A.1.1 Deep Appendix Subsection
This should be treated as a content heading.
"""
        outline_file = temp_dir / "two_level_limitation.md"
        outline_file.write_text(content, encoding="utf-8")

        parser = OutlineParser()
        outline = parser.parse_file(outline_file, temp_dir)

        assert outline.title == "Sample Book"
        assert len(outline.chapters) == 2

        # Chapter 1 should have 2 numbered sections (content headings are not tracked as sections)
        chapter1 = outline.chapters[0]
        assert chapter1.title == "Chapter 1: Getting Started"
        assert len(chapter1.sections) == 2  # Only the numbered sections

        # Check that numbered sections get filenames
        numbered_sections = [s for s in chapter1.sections if s.filename]
        assert len(numbered_sections) == 2
        assert numbered_sections[0].title == "First Steps"
        assert numbered_sections[1].title == "Next Steps"

        # Deep nesting headings are treated as content, not as sections
        # They should be in the chapter content, not in the sections list

        # Appendix should have 1 numbered section (content headings are not tracked as sections)
        appendix = outline.chapters[1]
        assert appendix.title == "Appendix A: Reference"
        assert len(appendix.sections) == 1  # Only the numbered section

        # Check that numbered appendix sections get filenames
        numbered_appendix_sections = [s for s in appendix.sections if s.filename]
        assert len(numbered_appendix_sections) == 1
        assert numbered_appendix_sections[0].title == "Quick Reference"

        # Deep appendix nesting is treated as content, not as sections
        # It should be in the appendix content, not in the sections list

    def test_parse_content_headings(self, temp_dir):
        """Test parsing unnumbered H3 headings as content."""
        content = """# Sample Book

## Chapter 1: Getting Started

### Summary
This is a summary.

### Learning Goals
These are learning goals.

### 1.1 First Section
This is a numbered section.
"""
        outline_file = temp_dir / "content_headings.md"
        outline_file.write_text(content, encoding="utf-8")

        parser = OutlineParser()
        outline = parser.parse_file(outline_file, temp_dir)

        chapter = outline.chapters[0]
        # Summary and Learning Goals should not appear in sections list (they're content)
        assert len(chapter.sections) == 1  # Only the numbered section
        assert chapter.sections[0].filename == "first-section.rst"  # 1.1 First Section

        # Content headings should be in chapter content, not as separate sections
        assert "Summary" in chapter.content.content
        assert "Learning Goals" in chapter.content.content

    def test_parse_first_h1_only(self, temp_dir):
        """Test that only the first H1 heading is used as the title."""
        content = """# First Title

## Introduction

# Second Title (should be ignored)

## Chapter 1
"""
        outline_file = temp_dir / "multiple_h1.md"
        outline_file.write_text(content, encoding="utf-8")

        parser = OutlineParser()
        outline = parser.parse_file(outline_file, temp_dir)

        assert outline.title == "First Title"
        assert len(outline.chapters) == 2  # Introduction and Chapter 1

    def test_parse_chapter_with_no_sections(self, temp_dir):
        """Test parsing chapters with no sections - content should be extracted."""
        content = """# Sample Book

## Chapter 1: Getting Started

This is chapter 1 content with no sections.

## Chapter 2: Advanced Topics

### 2.1 First Section
This is a section.

### 2.2 Second Section
This is another section.

## Chapter 3: Final Chapter

This is chapter 3 content with no sections.
"""
        outline_file = temp_dir / "no_sections.md"
        outline_file.write_text(content, encoding="utf-8")

        parser = OutlineParser()
        outline = parser.parse_file(outline_file, temp_dir)

        # Chapter 1 should have no sections but have content
        chapter1 = outline.chapters[0]
        assert len(chapter1.sections) == 0
        assert "This is chapter 1 content with no sections" in chapter1.content.content

        # Chapter 2 should have sections
        chapter2 = outline.chapters[1]
        assert len(chapter2.sections) == 2
        assert chapter2.sections[0].title == "First Section"
        assert chapter2.sections[1].title == "Second Section"

        # Chapter 3 should have no sections but have content
        chapter3 = outline.chapters[2]
        assert len(chapter3.sections) == 0
        assert "This is chapter 3 content with no sections" in chapter3.content.content


class TestOutlineConverter:
    """Test the outline conversion functionality."""

    def test_convert_outline_basic(self, temp_dir, sample_outline_md):
        """Test basic outline conversion."""
        converter = OutlineConverter(force=True, dry_run=False)

        # Create a simple outline
        outline = BookOutline(
            title="Sample Book Title",
            introduction_content=ContentBlock("Introduction content", 1, 3),
            chapters=[
                Chapter(
                    title="Introduction: How to use this book",
                    heading_type=HeadingType.INTRODUCTION,
                    folder_name="introduction",
                    content=ContentBlock("Intro content", 4, 6),
                    sections=[
                        Section(
                            title="Summary",
                            number="",
                            content=ContentBlock("Summary content", 7, 8),
                            filename="",
                        )
                    ],
                ),
                Chapter(
                    title="Chapter 1: Getting Started",
                    heading_type=HeadingType.CHAPTER,
                    folder_name="chapter1",
                    content=ContentBlock("Chapter content", 10, 12),
                    sections=[
                        Section(
                            title="1.1 First Steps",
                            number="1.1",
                            content=ContentBlock("First steps content", 13, 14),
                            filename="first-steps.rst",
                        )
                    ],
                ),
            ],
            output_dir=temp_dir,
        )

        # Convert the outline
        converter.convert_outline(outline)

        # Check that files were created
        assert (temp_dir / "index.rst").exists()
        assert (temp_dir / "introduction" / "index.rst").exists()
        assert (temp_dir / "chapter1" / "index.rst").exists()
        assert (temp_dir / "chapter1" / "first-steps.rst").exists()

    def test_convert_outline_dry_run(self, temp_dir, sample_outline_md):
        """Test outline conversion in dry-run mode."""
        converter = OutlineConverter(force=False, dry_run=True)

        outline = BookOutline(
            title="Sample Book Title",
            introduction_content=ContentBlock("", 1, 1),
            chapters=[],
            output_dir=temp_dir,
        )

        # Convert the outline (should not create files)
        converter.convert_outline(outline)

        # Check that no files were created
        assert not (temp_dir / "index.rst").exists()

    def test_clean_section_title(self):
        """Test cleaning section titles."""
        converter = OutlineConverter()

        # Test numbered sections
        assert converter._get_clean_section_title("1.1 First Steps") == "First Steps"
        assert (
            converter._get_clean_section_title("2.3.1 Advanced Topic")
            == "Advanced Topic"
        )

        # Test appendix sections
        assert (
            converter._get_clean_section_title("A.1 Quick Reference")
            == "Quick Reference"
        )
        assert (
            converter._get_clean_section_title("D.1.2 Detailed Info") == "Detailed Info"
        )

        # Test sections with colons
        assert (
            converter._get_clean_section_title("1.1: Title with Colon")
            == "Title with Colon"
        )
        assert (
            converter._get_clean_section_title(": Title Starting with Colon")
            == "Title Starting with Colon"
        )

        # Test content headings (should not be modified)
        assert converter._get_clean_section_title("Summary") == "Summary"
        assert converter._get_clean_section_title("Learning Goals") == "Learning Goals"

    def test_clean_chapter_title(self):
        """Test cleaning chapter titles."""
        converter = OutlineConverter()

        # Test regular chapters
        chapter = Chapter(
            title="Chapter 1: Getting Started",
            heading_type=HeadingType.CHAPTER,
            folder_name="chapter1",
            content=ContentBlock("", 1, 1),
            sections=[],
        )
        assert converter._get_clean_chapter_title(chapter) == "Getting Started"

        # Test appendices
        appendix = Chapter(
            title="Appendix A: Reference Material",
            heading_type=HeadingType.APPENDIX,
            folder_name="appendixA",
            content=ContentBlock("", 1, 1),
            sections=[],
        )
        assert converter._get_clean_chapter_title(appendix) == "Reference Material"

        # Test introduction
        intro = Chapter(
            title="Introduction: How to use this book",
            heading_type=HeadingType.INTRODUCTION,
            folder_name="introduction",
            content=ContentBlock("", 1, 1),
            sections=[],
        )
        assert converter._get_clean_chapter_title(intro) == "How to use this book"

    def test_content_filtering(self):
        """Test filtering of original headings from content."""
        converter = OutlineConverter()

        # Test chapter heading filtering
        content = """# Chapter Title

Some content here.

## Section Title
Section content.
"""
        filtered = converter._filter_chapter_heading(content, "Chapter Title")
        assert "Chapter Title" not in filtered
        assert "Some content here" in filtered

        # Test section heading filtering
        content = """## Section Title

Section content here.
"""
        filtered = converter._filter_section_heading(content, "Section Title")
        assert "Section Title" not in filtered
        assert "Section content here" in filtered

    @patch("rstbuddy.services.outline_converter.subprocess.run")
    def test_convert_content_to_rst(self, mock_run):
        """Test Markdown to RST conversion."""
        # Mock pandoc to fail (simulate pandoc not being available)
        mock_run.side_effect = FileNotFoundError("pandoc not found")

        converter = OutlineConverter()

        # Test with simple content - should raise FileError with installation instructions
        with pytest.raises(
            FileError, match="Pandoc is not installed or not found in PATH"
        ):
            converter.convert_content_to_rst("**Bold text**")

        # Test with empty content
        result = converter.convert_content_to_rst("")
        assert result == ""

    def test_content_comparison(self):
        """Test content comparison for determining if files need updating."""
        converter = OutlineConverter()

        # Test with non-existent file (should return True - content is different)
        content = "Hello\nWorld\n"
        assert converter._content_is_different(Path("nonexistent"), content)

        # Test with existing file that has different content
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Different content\n")
            temp_file = Path(f.name)

        try:
            assert converter._content_is_different(temp_file, content)
        finally:
            temp_file.unlink()

    def test_content_comparison_with_encoding_error(self):
        """Test content comparison when file cannot be read due to encoding issues."""
        converter = OutlineConverter()

        # Create a temporary file with non-UTF-8 content
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(b"Invalid UTF-8: \xff\xfe\xfd")
            temp_file = Path(f.name)

        try:
            # Should handle encoding errors gracefully
            result = converter._content_is_different(temp_file, "new content")
            assert result is True  # Should assume different if can't read
        finally:
            temp_file.unlink()

    def test_content_comparison_with_os_error(self):
        """Test content comparison when file operations fail."""
        converter = OutlineConverter()

        # Mock a file that raises OSError when opened
        with patch("pathlib.Path.open", side_effect=OSError("Permission denied")):
            result = converter._content_is_different(
                Path("/nonexistent"), "new content"
            )
            assert result is True  # Should assume different if can't read

    def test_backup_file_if_exists_dry_run(self):
        """Test backup file creation in dry run mode."""
        converter = OutlineConverter(force=True, dry_run=True)

        # Create a temporary file to backup
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            temp_file = Path(f.name)

        try:
            with patch("builtins.print") as mock_print:
                converter._backup_file_if_exists(temp_file)
                # Check that the print was called with a message containing the expected text
                mock_print.assert_called()
                call_args = mock_print.call_args[0][0]
                assert "[DRY RUN] Would backup:" in call_args
                assert str(temp_file) in call_args
        finally:
            temp_file.unlink()

    def test_backup_file_if_exists_actual_backup(self):
        """Test actual backup file creation."""
        converter = OutlineConverter(force=True, dry_run=False)

        # Create a temporary file to backup
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            temp_file = Path(f.name)

        try:
            with patch("builtins.print") as mock_print:
                converter._backup_file_if_exists(temp_file)
                # Check that the print was called with a message containing the expected text
                mock_print.assert_called()
                call_args = mock_print.call_args[0][0]
                assert "Backed up:" in call_args
                assert str(temp_file) in call_args
                assert ".bak" in call_args

                # Check that backup file was created
                backup_files = list(temp_file.parent.glob(f"{temp_file.name}.*.bak"))
                assert len(backup_files) == 1
                backup_files[0].unlink()  # Clean up
        finally:
            temp_file.unlink()

    def test_backup_and_write_file_skips_unchanged(self):
        """Test that unchanged files are skipped."""
        converter = OutlineConverter(force=True, dry_run=False)

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            temp_file = Path(f.name)

        try:
            with patch("builtins.print") as mock_print:
                converter._backup_and_write_file(temp_file, "test content")
                # Check that the print was called with a message containing the expected text
                mock_print.assert_called()
                call_args = mock_print.call_args[0][0]
                assert "Skipping" in call_args
                assert "content unchanged" in call_args
                assert str(temp_file) in call_args
        finally:
            temp_file.unlink()

    def test_backup_and_write_file_dry_run(self):
        """Test backup and write in dry run mode."""
        converter = OutlineConverter(force=True, dry_run=True)

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("old content")
            temp_file = Path(f.name)

        try:
            with patch("builtins.print") as mock_print:
                converter._backup_and_write_file(temp_file, "new content")
                # Check that the print was called with a message containing the expected text
                mock_print.assert_called()
                call_args = mock_print.call_args[0][0]
                assert "[DRY RUN] Would update:" in call_args
                assert str(temp_file) in call_args
        finally:
            temp_file.unlink()

    def test_convert_content_to_rst_with_temp_file_creation_error(self):
        """Test RST conversion when temporary file creation fails."""
        converter = OutlineConverter()

        with patch(
            "tempfile.NamedTemporaryFile", side_effect=OSError("Permission denied")
        ):
            with pytest.raises(FileError, match="Failed to create temporary file"):
                converter.convert_content_to_rst("test content")

    def test_convert_content_to_rst_with_pandoc_failure(self):
        """Test RST conversion when pandoc command fails."""
        converter = OutlineConverter()

        with patch("rstbuddy.services.outline_converter.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "pandoc", "error")

            with pytest.raises(FileError, match="Pandoc conversion failed"):
                converter.convert_content_to_rst("test content")

    def test_convert_content_to_rst_with_file_read_error(self):
        """Test RST conversion when reading temporary file fails."""
        converter = OutlineConverter()

        with patch("rstbuddy.services.outline_converter.subprocess.run"):
            with patch("pathlib.Path.open", side_effect=OSError("Permission denied")):
                with pytest.raises(FileError, match="Failed to read temporary file"):
                    converter.convert_content_to_rst("test content")

    def test_convert_content_to_rst_success(self):
        """Test successful RST conversion."""
        converter = OutlineConverter()

        with patch("rstbuddy.services.outline_converter.subprocess.run"):
            with patch("pathlib.Path.open") as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = (
                    "# RST Content"
                )

                result = converter.convert_content_to_rst("**Bold text**")
                assert result == "# RST Content"
                assert "**Bold text**" in converter._content_cache

    def test_convert_content_to_rst_empty_content(self):
        """Test RST conversion with empty content."""
        converter = OutlineConverter()

        result = converter.convert_content_to_rst("")
        assert result == ""

        result = converter.convert_content_to_rst("   \n  \t  ")
        assert result == ""

    def test_convert_content_to_rst_cache_hit(self):
        """Test that cached results are returned."""
        converter = OutlineConverter()

        # Prime the cache
        converter._content_cache["test content"] = "cached result"

        result = converter.convert_content_to_rst("test content")
        assert result == "cached result"


class TestConvertOutlineCLI:
    """Test the convert-outline CLI command."""

    def test_convert_outline_command_basic(self, runner, temp_outline_file, temp_dir):
        """Test basic convert-outline command execution."""
        # Use a unique output directory for this test
        unique_output_dir = temp_dir / "output_basic"
        unique_output_dir.mkdir()

        with patch("rstbuddy.services.outline_parser.Settings") as mock_settings:
            mock_settings.return_value.documentation_dir = str(unique_output_dir)

            result = runner.invoke(
                cli,
                ["convert-outline", str(temp_outline_file), "--force"],
                catch_exceptions=False,
            )

            assert result.exit_code == 0
            assert (
                "Conversion completed successfully" in result.output
                or "Updated:" in result.output
            )

    def test_convert_outline_command_dry_run(self, runner, temp_outline_file, temp_dir):
        """Test convert-outline command with --dry-run flag."""
        # Use a unique output directory for this test
        unique_output_dir = temp_dir / "output_dry_run"
        unique_output_dir.mkdir()

        with patch("rstbuddy.services.outline_parser.Settings") as mock_settings:
            mock_settings.return_value.documentation_dir = str(unique_output_dir)

            result = runner.invoke(
                cli,
                ["convert-outline", str(temp_outline_file), "--dry-run"],
                catch_exceptions=False,
            )

            assert result.exit_code == 0
            assert "DRY RUN - No files will be created" in result.output
            assert not (unique_output_dir / "index.rst").exists()

    def test_convert_outline_command_force(self, runner, temp_outline_file, temp_dir):
        """Test convert-outline command with --force flag."""
        # Use a unique output directory for this test
        unique_output_dir = temp_dir / "output_force"
        unique_output_dir.mkdir()

        with patch("rstbuddy.services.outline_parser.Settings") as mock_settings:
            mock_settings.return_value.documentation_dir = str(unique_output_dir)

            result = runner.invoke(
                cli,
                ["convert-outline", str(temp_outline_file), "--force"],
                catch_exceptions=False,
            )

            assert result.exit_code == 0
            assert (
                "Conversion completed successfully" in result.output
                or "Updated:" in result.output
            )
            assert (unique_output_dir / "index.rst").exists()

    def test_convert_outline_command_invalid_file(self, runner, temp_dir):
        """Test convert-outline command with invalid file."""
        with patch("rstbuddy.settings.Settings") as mock_settings:
            mock_settings.return_value.documentation_dir = str(temp_dir)

            result = runner.invoke(
                cli, ["convert-outline", "nonexistent.md"], catch_exceptions=False
            )

            assert result.exit_code != 0
            assert "does not exist" in result.output

    def test_convert_outline_command_validation_error(self, runner, temp_dir):
        """Test convert-outline command with validation errors."""
        # Create an invalid outline
        invalid_outline = temp_dir / "invalid.md"
        invalid_outline.write_text("## Invalid Chapter\n", encoding="utf-8")

        with patch("rstbuddy.settings.Settings") as mock_settings:
            mock_settings.return_value.documentation_dir = str(temp_dir)

            result = runner.invoke(
                cli, ["convert-outline", str(invalid_outline)], catch_exceptions=False
            )

            assert result.exit_code != 0
            assert "validation failed" in result.output.lower()


class TestIntegration:
    """Integration tests for the complete convert-outline pipeline."""

    def test_complete_pipeline(self, temp_dir, sample_outline_md):
        """Test the complete pipeline from validation to conversion."""
        # Create a temporary file for the pipeline
        outline_file = temp_dir / "pipeline_test.md"
        outline_file.write_text(sample_outline_md, encoding="utf-8")

        # Step 1: Validate
        validator = OutlineValidator()
        validation_result = validator.validate_file(outline_file)
        assert validation_result.is_valid is True

        # Step 2: Parse
        parser = OutlineParser()
        outline = parser.parse_file(outline_file, temp_dir)
        assert outline.title == "Sample Book Title"
        assert len(outline.chapters) == 4

        # Step 3: Convert
        converter = OutlineConverter(force=True, dry_run=False)
        converter.convert_outline(outline)

        # Step 4: Verify output
        assert (temp_dir / "index.rst").exists()
        assert (temp_dir / "introduction" / "index.rst").exists()
        assert (temp_dir / "chapter1" / "index.rst").exists()
        assert (temp_dir / "chapter1" / "first-steps.rst").exists()
        assert (temp_dir / "chapter1" / "next-steps.rst").exists()

        # Check main index content
        main_index = (temp_dir / "index.rst").read_text(encoding="utf-8")
        assert "Sample Book Title" in main_index
        assert "introduction/index" in main_index
        assert "chapter1/index" in main_index

        # Check chapter index content
        chapter_index = (temp_dir / "chapter1" / "index.rst").read_text(
            encoding="utf-8"
        )
        assert "Getting Started" in chapter_index
        assert "first-steps" in chapter_index
        assert "next-steps" in chapter_index

    def test_pipeline_with_content_headings(self, temp_dir):
        """Test pipeline with unnumbered H3 headings that should be content."""
        content = """# Sample Book

## Chapter 1: Getting Started

### Summary
This is a summary.

### Learning Goals
These are learning goals.

### 1.1 First Section
This is a numbered section.
"""

        # Create a temporary file for the pipeline
        outline_file = temp_dir / "content_headings_pipeline.md"
        outline_file.write_text(content, encoding="utf-8")

        # Run through pipeline
        validator = OutlineValidator()
        validation_result = validator.validate_file(outline_file)
        assert validation_result.is_valid is True

        parser = OutlineParser()
        outline = parser.parse_file(outline_file, temp_dir)

        converter = OutlineConverter(force=True, dry_run=False)
        converter.convert_outline(outline)

        # Verify that content headings don't create separate files
        chapter_dir = temp_dir / "chapter1"
        assert (chapter_dir / "index.rst").exists()
        assert (chapter_dir / "first-section.rst").exists()
        assert not (chapter_dir / "summary.rst").exists()
        assert not (chapter_dir / "learning-goals.rst").exists()

        # Check that content headings are processed as content, not as sections
        chapter = outline.chapters[0]  # Chapter 1
        assert len(chapter.sections) == 1  # Only the numbered section
        # Content headings should have empty filenames
        content_headings = [s for s in chapter.sections if not s.filename]
        assert len(content_headings) == 0  # No content headings in sections list
        # Numbered sections should have filenames
        numbered_sections = [s for s in chapter.sections if s.filename]
        assert len(numbered_sections) == 1  # Only First Section

        # Content headings should be in chapter content
        assert "Summary" in chapter.content.content
        assert "Learning Goals" in chapter.content.content

        # The content headings should be in the chapter index as content, not as toctree entries
        chapter_index = (chapter_dir / "index.rst").read_text(encoding="utf-8")
        # The toctree should only contain the actual section file
        assert "first-section" in chapter_index
        # The content headings should be processed as content within the chapter
        # but they won't appear as separate entries in the index

    def test_convert_outline_chapters_with_no_sections(self, temp_dir):
        """Test that chapters with no sections have their content properly written."""
        content = """# Sample Book

## Chapter 1: Getting Started

This is chapter 1 content with no sections.

## Chapter 2: Advanced Topics

### 2.1 First Section
This is a section.

## Chapter 3: Final Chapter

This is chapter 3 content with no sections.
"""
        outline_file = temp_dir / "no_sections_convert.md"
        outline_file.write_text(content, encoding="utf-8")

        # Run through pipeline
        validator = OutlineValidator()
        validation_result = validator.validate_file(outline_file)
        assert validation_result.is_valid is True

        parser = OutlineParser()
        outline = parser.parse_file(outline_file, temp_dir)

        converter = OutlineConverter(force=True, dry_run=False)
        converter.convert_outline(outline)

        # Check that Chapter 1 index.rst contains the content
        chapter1_index = (temp_dir / "chapter1" / "index.rst").read_text(
            encoding="utf-8"
        )
        assert "Getting Started" in chapter1_index
        assert "This is chapter 1 content with no sections" in chapter1_index

        # Check that Chapter 2 index.rst contains the section
        chapter2_index = (temp_dir / "chapter2" / "index.rst").read_text(
            encoding="utf-8"
        )
        assert "Advanced Topics" in chapter2_index
        assert "first-section" in chapter2_index

        # Check that Chapter 3 index.rst contains the content
        chapter3_index = (temp_dir / "chapter3" / "index.rst").read_text(
            encoding="utf-8"
        )
        assert "Final Chapter" in chapter3_index
        assert "This is chapter 3 content with no sections" in chapter3_index
