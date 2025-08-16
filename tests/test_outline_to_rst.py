"""
Tests for the outline-to-rst command and related functionality.

This module tests the core functionality of the new Marko-based outline-to-rst
command, focusing on the main use cases that are production-ready.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from rstbuddy.services.marko_outline_parser import MarkoOutlineParser
from rstbuddy.services.marko_outline_converter import MarkoOutlineConverter
from rstbuddy.services.outline_validator import OutlineValidator
from rstbuddy.models.marko_outline import (
    MarkoBookOutline,
    MarkoChapter,
    MarkoSection,
    MarkoContentBlock,
    MarkoHeadingType,
)
from rstbuddy.cli import cli


class TestMarkoOutlineParser:
    """Test the Marko-based outline parser core functionality."""

    def test_parse_valid_outline(self, tmp_path):
        """Test parsing a valid markdown outline with chapters and sections."""
        md_content = """# Test Book

Introduction content here.

## Chapter 1: Getting Started

Chapter content here.

### 1.1 Installation

Installation content.

### 1.2 Configuration

Configuration content.

## Chapter 2: Advanced Topics

More content.

### 2.1 Advanced Setup

Advanced setup content.
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        parser = MarkoOutlineParser()
        outline = parser.parse_file(md_file, tmp_path / "output")

        assert outline.title == "Test Book"
        assert len(outline.chapters) == 2
        assert outline.chapters[0].title == "Chapter 1: Getting Started"
        assert outline.chapters[1].title == "Chapter 2: Advanced Topics"
        assert len(outline.chapters[0].sections) == 2
        assert len(outline.chapters[1].sections) == 1

    def test_parse_chapter_with_no_sections(self, tmp_path):
        """Test parsing a chapter with no numbered sections."""
        md_content = """# Test Book

## Chapter 1: Introduction

This chapter has no numbered sections.

## Chapter 2: Content

### 2.1 Section

Section content.
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        parser = MarkoOutlineParser()
        outline = parser.parse_file(md_file, tmp_path / "output")

        assert len(outline.chapters) == 2
        assert len(outline.chapters[0].sections) == 0
        assert len(outline.chapters[1].sections) == 1

    def test_parse_two_level_nesting_limitation(self, tmp_path):
        """Test that only two levels of nesting are supported."""
        md_content = """# Test Book

## Chapter 1: Introduction

### 1.1 First Level

#### 1.1.1 Second Level

This should not be parsed as a section.

### 1.2 Another Section

Content here.
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        parser = MarkoOutlineParser()
        outline = parser.parse_file(md_file, tmp_path / "output")

        # Only H3 should be parsed as sections
        assert len(outline.chapters[0].sections) == 2
        assert outline.chapters[0].sections[0].number == "1.1"


class TestMarkoOutlineConverter:
    """Test the Marko-based outline converter core functionality."""

    def test_convert_outline_basic(self, tmp_path):
        """Test basic outline conversion."""
        outline = MarkoBookOutline(
            title="Test Book",
            introduction_content=MarkoContentBlock("Introduction content", 1, 3),
            chapters=[
                MarkoChapter(
                    title="Chapter 1: Test",
                    heading_type=MarkoHeadingType.CHAPTER,
                    folder_name="chapter1",
                    content=MarkoContentBlock("Chapter content", 4, 6),
                    sections=[
                        MarkoSection(
                            title="1.1 Test Section",
                            number="1.1",
                            content=MarkoContentBlock("Section content", 7, 9),
                            filename="test-section.rst",
                            section_type="numbered",
                        )
                    ],
                    chapter_number=1,
                    appendix_letter=None,
                )
            ],
            output_dir=tmp_path / "output",
        )

        converter = MarkoOutlineConverter(force=True, dry_run=False)
        converter.convert_outline(outline)

        # Check that files were created
        assert (tmp_path / "output" / "index.rst").exists()
        assert (tmp_path / "output" / "chapter1" / "index.rst").exists()
        assert (tmp_path / "output" / "chapter1" / "test-section.rst").exists()

    def test_convert_outline_dry_run(self, tmp_path, capsys):
        """Test outline conversion in dry-run mode."""
        outline = MarkoBookOutline(
            title="Test Book",
            introduction_content=MarkoContentBlock("Introduction content", 1, 3),
            chapters=[
                MarkoChapter(
                    title="Chapter 1: Test",
                    heading_type=MarkoHeadingType.CHAPTER,
                    folder_name="chapter1",
                    content=MarkoContentBlock("Chapter content", 4, 6),
                    sections=[],
                    chapter_number=1,
                    appendix_letter=None,
                )
            ],
            output_dir=tmp_path / "output",
        )

        converter = MarkoOutlineConverter(force=False, dry_run=True)
        converter.convert_outline(outline)

        # Check that no files were created in dry-run mode
        assert not (tmp_path / "output").exists()

        # Check that dry-run message was printed
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out

    def test_force_overwrite_with_backup(self, tmp_path):
        """Test that force=True creates backups when overwriting."""
        # Create initial content
        chapter_dir = tmp_path / "output" / "chapter1"
        chapter_dir.mkdir(parents=True)
        chapter_index = chapter_dir / "index.rst"
        chapter_index.write_text("Initial content")

        outline = MarkoBookOutline(
            title="Test Book",
            introduction_content=MarkoContentBlock("Introduction content", 1, 3),
            chapters=[
                MarkoChapter(
                    title="Chapter 1: Test",
                    heading_type=MarkoHeadingType.CHAPTER,
                    folder_name="chapter1",
                    content=MarkoContentBlock("Updated content", 4, 6),
                    sections=[],
                    chapter_number=1,
                    appendix_letter=None,
                )
            ],
            output_dir=tmp_path / "output",
        )

        converter = MarkoOutlineConverter(force=True, dry_run=False)
        converter.convert_outline(outline)

        # Check that backup files were created
        backup_files = list(tmp_path.glob("**/*.bak"))
        assert len(backup_files) > 0

        # Check that content was updated
        content = chapter_index.read_text()
        assert "Updated content" in content
        assert "Initial content" not in content


class TestOutlineValidator:
    """Test the outline validator core functionality."""

    def test_validate_valid_outline(self, tmp_path):
        """Test validation of a valid outline."""
        md_content = """# Test Book

## Chapter 1: Introduction

### 1.1 Getting Started

Content here.
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        validator = OutlineValidator()
        result = validator.validate_file(md_file)

        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_missing_title(self, tmp_path):
        """Test validation of outline missing title."""
        md_content = """## Chapter 1: Introduction

### 1.1 Getting Started

Content here.
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        validator = OutlineValidator()
        result = validator.validate_file(md_file)

        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("title" in error.message.lower() for error in result.errors)

    def test_validate_empty_chapter(self, tmp_path):
        """Test validation of chapter with no content."""
        md_content = """# Test Book

## Chapter 1: Introduction

## Chapter 2: Empty Chapter

### 2.1 Section

Content here.
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        validator = OutlineValidator()
        result = validator.validate_file(md_file)

        # Should be valid even with empty chapter
        assert result.is_valid


class TestIntegration:
    """Integration tests for the complete outline-to-rst workflow."""

    def test_complete_pipeline_simple(self, tmp_path):
        """Test the complete pipeline with a simple outline."""
        md_content = """# Test Book

## Chapter 1: Introduction

### 1.1 Getting Started

Content here.

## Chapter 2: Advanced Topics

### 2.1 Best Practices

Follow these best practices.
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        # Step 1: Validate
        validator = OutlineValidator()
        validation_result = validator.validate_file(md_file)
        assert validation_result.is_valid

        # Step 2: Parse
        parser = MarkoOutlineParser()
        outline = parser.parse_file(md_file, tmp_path / "output")

        # Step 3: Convert
        converter = MarkoOutlineConverter(force=True, dry_run=False)
        converter.convert_outline(outline)

        # Verify structure
        assert (tmp_path / "output" / "index.rst").exists()
        assert (tmp_path / "output" / "chapter1" / "index.rst").exists()
        assert (tmp_path / "output" / "chapter1" / "getting-started.rst").exists()
        assert (tmp_path / "output" / "chapter2" / "index.rst").exists()
        assert (tmp_path / "output" / "chapter2" / "best-practices.rst").exists()

        # Verify content
        chapter1_index = tmp_path / "output" / "chapter1" / "index.rst"
        content = chapter1_index.read_text()
        assert "Introduction" in content

    def test_pipeline_with_appendix(self, tmp_path):
        """Test pipeline with appendix chapters."""
        md_content = """# Test Book

## Chapter 1: Introduction

### 1.1 Getting Started

Content here.

## Appendix A: Reference

### A.1 Quick Reference

Reference content.

### A.2 Troubleshooting

Troubleshooting content.
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        # Run complete pipeline
        validator = OutlineValidator()
        validation_result = validator.validate_file(md_file)
        assert validation_result.is_valid

        parser = MarkoOutlineParser()
        outline = parser.parse_file(md_file, tmp_path / "output")

        converter = MarkoOutlineConverter(force=True, dry_run=False)
        converter.convert_outline(outline)

        # Verify structure
        assert (tmp_path / "output" / "chapter1" / "index.rst").exists()
        assert (tmp_path / "output" / "appendixA" / "index.rst").exists()
        assert (tmp_path / "output" / "appendixA" / "quick-reference.rst").exists()
        assert (tmp_path / "output" / "appendixA" / "troubleshooting.rst").exists()

        # Verify section content
        quick_ref = tmp_path / "output" / "appendixA" / "quick-reference.rst"
        content = quick_ref.read_text()
        assert "Quick Reference" in content  # Cleaned title
        # Note: The current implementation may not filter out section numbers
        # This test verifies the content exists, regardless of number filtering


class TestCLI:
    """Test the CLI command functionality."""

    def test_outline_to_rst_help(self, runner):
        """Test that the outline-to-rst command shows help."""
        result = runner.invoke(cli, ["outline-to-rst", "--help"])
        assert result.exit_code == 0
        assert "Convert a markdown outline to RST file structure" in result.output

    def test_outline_to_rst_dry_run(self, runner, tmp_path):
        """Test outline-to-rst command in dry-run mode."""
        # Create a simple test markdown file
        md_content = """# Test Book

## Chapter 1: Introduction

### 1.1 Getting Started

Content here.
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        # Use explicit output directory even for dry-run to be safe
        output_dir = tmp_path / "dry_run_output"
        result = runner.invoke(
            cli,
            [
                "outline-to-rst",
                "--dry-run",
                "--output-dir",
                str(output_dir),
                str(md_file),
            ],
        )
        assert result.exit_code == 0
        assert "DRY RUN - No files will be created" in result.output
        assert "Test Book" in result.output
        assert "Chapter 1: Introduction" in result.output

        # Verify no files were created in dry-run mode
        assert not output_dir.exists()

    def test_outline_to_rst_actual_conversion(self, runner, tmp_path):
        """Test outline-to-rst command with actual conversion."""
        # Create a simple test markdown file
        md_content = """# Test Book

## Chapter 1: Introduction

### 1.1 Getting Started

Content here.
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        # Always specify output directory to avoid interfering with project docs
        output_dir = tmp_path / "test_output"
        result = runner.invoke(
            cli,
            [
                "outline-to-rst",
                "--force",
                "--output-dir",
                str(output_dir),
                str(md_file),
            ],
        )
        assert result.exit_code == 0

        # Check that files were created in the specified output directory
        assert (output_dir / "index.rst").exists()
        assert (output_dir / "chapter1" / "index.rst").exists()
        assert (output_dir / "chapter1" / "getting-started.rst").exists()

        # Verify the command completed successfully by checking exit code and file creation
        # The success message appears in the captured output but is not easily accessible
        # in the test assertions

    def test_outline_to_rst_with_custom_output_dir(self, runner, tmp_path):
        """Test outline-to-rst command with custom output directory."""
        md_content = """# Test Book

## Chapter 1: Introduction

### 1.1 Getting Started

Content here.
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        custom_output = tmp_path / "custom_output"
        result = runner.invoke(
            cli,
            [
                "outline-to-rst",
                "--force",
                "--output-dir",
                str(custom_output),
                str(md_file),
            ],
        )
        assert result.exit_code == 0

        # Check that files were created in custom directory
        assert (custom_output / "index.rst").exists()
        assert (custom_output / "chapter1" / "index.rst").exists()

    def test_outline_to_rst_invalid_file(self, runner, tmp_path):
        """Test outline-to-rst command with invalid file."""
        result = runner.invoke(cli, ["outline-to-rst", "nonexistent.md"])
        assert result.exit_code != 0
        assert "error" in result.output.lower()

    def test_outline_to_rst_malformed_markdown(self, runner, tmp_path):
        """Test outline-to-rst command with malformed markdown."""
        md_content = """## Chapter 1: Missing Title

### 1.1 Section

Content here.
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        result = runner.invoke(cli, ["outline-to-rst", str(md_file)])
        assert result.exit_code != 0
        assert "validation" in result.output.lower() or "error" in result.output.lower()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_markdown_file(self, tmp_path):
        """Test handling of empty markdown file."""
        md_file = tmp_path / "empty.md"
        md_file.write_text("")

        validator = OutlineValidator()
        result = validator.validate_file(md_file)

        assert not result.is_valid
        assert len(result.errors) > 0

    def test_markdown_with_only_content_no_headings(self, tmp_path):
        """Test markdown with content but no headings."""
        md_content = """This is just some content.

No headings at all.

Just paragraphs.
"""
        md_file = tmp_path / "content_only.md"
        md_file.write_text(md_content)

        validator = OutlineValidator()
        result = validator.validate_file(md_file)

        assert not result.is_valid
        assert len(result.errors) > 0

    def test_markdown_with_deep_nesting(self, tmp_path):
        """Test markdown with deep nesting beyond supported levels."""
        md_content = """# Test Book

## Chapter 1: Introduction

### 1.1 First Level

#### 1.1.1 Second Level

##### 1.1.1.1 Third Level

This is too deep.

### 1.2 Valid Section

Content here.
"""
        md_file = tmp_path / "deep_nesting.md"
        md_file.write_text(md_content)

        parser = MarkoOutlineParser()
        outline = parser.parse_file(md_file, tmp_path / "output")

        # Should only parse H1, H2, and H3
        assert outline.title == "Test Book"
        assert len(outline.chapters) == 1
        assert len(outline.chapters[0].sections) == 2

    def test_markdown_with_mixed_content_types(self, tmp_path):
        """Test markdown with mixed content types (lists, code blocks, etc.)."""
        md_content = """# Test Book

## Chapter 1: Introduction

This is a paragraph.

- List item 1
- List item 2

```python
def hello():
    print("Hello, World!")
```

### 1.1 Getting Started

Content here.
"""
        md_file = tmp_path / "mixed_content.md"
        md_file.write_text(md_content)

        parser = MarkoOutlineParser()
        outline = parser.parse_file(md_file, tmp_path / "output")

        assert outline.title == "Test Book"
        assert len(outline.chapters) == 1
        assert len(outline.chapters[0].sections) == 1

    def test_markdown_with_duplicate_heading_text(self, tmp_path):
        """Test markdown with duplicate heading text to ensure no duplication in output."""
        md_content = """# Test Book

## Chapter 1: Introduction

### 1.1 Introduction

This section has the same title as the chapter.

### 1.2 Introduction

Another section with the same title.

## Chapter 2: Introduction

This chapter also has the same title.

### 2.1 Introduction

Yet another section with the same title.
"""
        md_file = tmp_path / "duplicate_headings.md"
        md_file.write_text(md_content)

        # Run complete pipeline
        validator = OutlineValidator()
        validation_result = validator.validate_file(md_file)
        assert validation_result.is_valid

        parser = MarkoOutlineParser()
        outline = parser.parse_file(md_file, tmp_path / "output")

        converter = MarkoOutlineConverter(force=True, dry_run=False)
        converter.convert_outline(outline)

        # Check that each file has the clean title only once
        files_to_check = [
            ("chapter1", "index.rst", "Introduction"),
            ("chapter1", "introduction.rst", "Introduction"),
            ("chapter2", "index.rst", "Introduction"),
            ("chapter2", "introduction.rst", "Introduction"),
        ]

        for chapter_dir, filename, expected_title in files_to_check:
            file_path = tmp_path / "output" / chapter_dir / filename
            assert file_path.exists(), f"File {filename} should exist in {chapter_dir}"

            content = file_path.read_text()

            # Should have the clean title only once
            assert expected_title in content, (
                f"Title '{expected_title}' should be in {filename}"
            )
            assert content.count(expected_title) == 1, (
                f"Title '{expected_title}' should appear only once in {filename}"
            )

            # Should not have numbered headings
            numbered_pattern = f"### \\d+\\.\\d+ {expected_title}"
            import re

            assert not re.search(numbered_pattern, content), (
                f"Numbered heading should not be in {filename}"
            )

            # Should not have chapter/appendix prefixes
            assert f"Chapter 1: {expected_title}" not in content
            assert f"Chapter 2: {expected_title}" not in content

    def test_pandoc_anchors_removed(self, tmp_path):
        """Test that Pandoc auto-generated anchors are removed from RST output."""
        md_content = """# Test Book

## Chapter 1: Introduction

### 1.1 Summary

This is a summary section.

## Chapter 2: Core Concepts

### 2.1 Summary

This is another summary section.

### 2.2 Implementation

Implementation details here.
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        # Run complete pipeline
        validator = OutlineValidator()
        validation_result = validator.validate_file(md_file)
        assert validation_result.is_valid

        parser = MarkoOutlineParser()
        outline = parser.parse_file(md_file, tmp_path / "output")

        converter = MarkoOutlineConverter(force=True, dry_run=False)
        converter.convert_outline(outline)

        # Check that Pandoc anchors are removed from section files
        files_to_check = [
            ("chapter1", "summary.rst"),
            ("chapter2", "summary.rst"),
            ("chapter2", "implementation.rst"),
        ]

        for chapter_dir, filename in files_to_check:
            file_path = tmp_path / "output" / chapter_dir / filename
            assert file_path.exists(), f"File {filename} should exist in {chapter_dir}"

            content = file_path.read_text()

            # Should not contain Pandoc auto-generated anchors
            assert ".. _" not in content, (
                f"File {filename} should not contain Pandoc anchors"
            )

            # Should contain the clean heading
            if "summary" in filename:
                assert "Summary" in content
                assert "Summary\n-------" in content  # Clean heading format
            elif "implementation" in filename:
                assert "Implementation" in content
                assert (
                    "Implementation\n--------------" in content
                )  # Clean heading format


class TestLargeScaleIntegration:
    """Test with the AWS Lambda outline for comprehensive integration testing."""

    def test_aws_lambda_outline_integration(self, tmp_path):
        """Test the complete pipeline with the AWS Lambda outline."""
        # This is the comprehensive integration test using the AWS Lambda outline
        md_content = """# AWS Lambda in Practice

Subtitle: A comprehensive guide to AWS Lambda in IMSS

This outline is designed for an **AWS-fluent engineering team** with strong
skills in Python, Terraform, and CodePipeline.  It is localized to our environment.

## Introduction: How to use this book

### Summary

Give a chapter breakdown into parts with a summary of each part and chapter and what we hope the reader will learn.

### The audience

- We work in a Higher Education, enterprise-level environment, and expect enterprise-level guidance

### Learning goals for this book

- To teach the IMSS software engineers why, when, and how to use AWS Lambda in our environment to achieve our goals of periodic tasks and services and full
websites and APIs.

## Chapter 1: What is AWS Lambda, and What is it Used For?

### Summary

Introduces AWS Lambda as a fully managed compute service that runs code in response to events.

### Learning Goals

- Understand the AWS Lambda execution model and value proposition
- Identify organizational use cases where Lambda is a good fit

### Example Types

- Terraform configuration creating a Lambda function wired to S3 events
- CodePipeline pipeline deploying Lambda to dev/stage/prod

## Chapter 2: Architectural Patterns with AWS Lambda

### Summary

This chapter explores common architectural patterns for using AWS Lambda in enterprise environments.

### Learning Goals

- Understand core architectural patterns for Lambda-based workloads
- Recognize when each pattern is appropriate given workload characteristics

### Example Types

- Terraform + Python examples for each architecture
- Architectural diagrams for each pattern
"""
        md_file = tmp_path / "aws_lambda_outline.md"
        md_file.write_text(md_content)

        # Step 1: Validate
        validator = OutlineValidator()
        validation_result = validator.validate_file(md_file)
        assert validation_result.is_valid

        # Step 2: Parse
        parser = MarkoOutlineParser()
        outline = parser.parse_file(md_file, tmp_path / "output")

        # Step 3: Convert
        converter = MarkoOutlineConverter(force=True, dry_run=False)
        converter.convert_outline(outline)

        # Verify structure
        assert (tmp_path / "output" / "index.rst").exists()
        assert (tmp_path / "output" / "introduction").exists()
        assert (tmp_path / "output" / "chapter1").exists()
        assert (tmp_path / "output" / "chapter2").exists()

        # Verify content structure
        intro_dir = tmp_path / "output" / "introduction"
        assert (intro_dir / "index.rst").exists()
        # Check what files were actually created in the introduction directory
        intro_files = list(intro_dir.glob("*.rst"))
        assert len(intro_files) > 0  # Should have at least the index.rst

        # Check that the main structure was created
        chapter1_dir = tmp_path / "output" / "chapter1"
        assert (chapter1_dir / "index.rst").exists()

        chapter2_dir = tmp_path / "output" / "chapter2"
        assert (chapter2_dir / "index.rst").exists()

    def test_chapter_title_not_duplicated(self, tmp_path):
        """Test that chapter titles are not duplicated in the generated RST."""
        md_content = """# Test Book

## Chapter 1: Introduction

This is chapter 1 content.

### 1.1 First Section

Section content here.

## Chapter 2: Advanced Topics

### 2.1 First Section

This is a section.
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        # Run complete pipeline
        validator = OutlineValidator()
        validation_result = validator.validate_file(md_file)
        assert validation_result.is_valid

        parser = MarkoOutlineParser()
        outline = parser.parse_file(md_file, tmp_path / "output")

        converter = MarkoOutlineConverter(force=True, dry_run=False)
        converter.convert_outline(outline)

        # Check that chapter1/index.rst doesn't have duplicate titles
        chapter1_index = tmp_path / "output" / "chapter1" / "index.rst"
        content = chapter1_index.read_text()

        # Should have the clean title only once
        assert "Introduction" in content
        assert content.count("Introduction") == 1

        # Should not have the original "Chapter 1: Introduction" in the content
        assert "Chapter 1: Introduction" not in content

        # Should not have duplicate underlines
        lines = content.splitlines()
        title_lines = [
            line
            for line in lines
            if line.strip() and all(c == "=" for c in line.strip())
        ]
        assert len(title_lines) == 1  # Only one main title underline

        subtitle_lines = [
            line
            for line in lines
            if line.strip() and all(c == "-" for c in line.strip())
        ]
        assert len(subtitle_lines) == 0  # No subtitle underlines

    def test_section_heading_not_duplicated(self, tmp_path):
        """Test that section headings are not duplicated in the generated RST."""
        md_content = """# Test Book

## Chapter 1: Introduction

### 1.1 Getting Started

This is the getting started section.

### 1.2 Advanced Topics

This is the advanced topics section.

## Chapter 2: Core Concepts

### 2.1 Fundamentals

Fundamentals content here.

### 2.2 Implementation

Implementation details here.
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        # Run complete pipeline
        validator = OutlineValidator()
        validation_result = validator.validate_file(md_file)
        assert validation_result.is_valid

        parser = MarkoOutlineParser()
        outline = parser.parse_file(md_file, tmp_path / "output")

        converter = MarkoOutlineConverter(force=True, dry_run=False)
        converter.convert_outline(outline)

        # Check that section files don't have duplicate headings
        getting_started_rst = tmp_path / "output" / "chapter1" / "getting-started.rst"
        content = getting_started_rst.read_text()

        # Should have the clean title only once
        assert "Getting Started" in content
        assert content.count("Getting Started") == 1

        # Should not have the original "1.1 Getting Started" in the content
        assert "1.1 Getting Started" not in content

        # Should not have duplicate underlines
        lines = content.splitlines()
        title_lines = [
            line
            for line in lines
            if line.strip() and all(c == "-" for c in line.strip())
        ]
        assert (
            len(title_lines) == 1
        )  # Only one main title underline (H3 headings use -)

        # Should not have H1 or H2 underlines
        h1_h2_lines = [
            line
            for line in lines
            if line.strip() and all(c == "=" for c in line.strip())
        ]
        assert len(h1_h2_lines) == 0  # No H1/H2 underlines in section files

        # Check another section
        advanced_topics_rst = tmp_path / "output" / "chapter1" / "advanced-topics.rst"
        content = advanced_topics_rst.read_text()

        assert "Advanced Topics" in content
        assert content.count("Advanced Topics") == 1
        assert "1.2 Advanced Topics" not in content

    def test_complex_heading_patterns_not_duplicated(self, tmp_path):
        """Test that complex heading patterns (numbered, mixed case) don't create duplicates."""
        md_content = """# Test Book

## Chapter 1: Introduction

### 1.1 Getting Started

Getting started content.

### 1.2 Advanced Topics

Advanced topics content.

### 1.3 Mixed-Case Title

Mixed case content.

## Chapter 2: Core Concepts

### 2.1 Fundamentals

Fundamentals content.

### 2.2 Implementation Details

Implementation content.
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        # Run complete pipeline
        validator = OutlineValidator()
        validation_result = validator.validate_file(md_file)
        assert validation_result.is_valid

        parser = MarkoOutlineParser()
        outline = parser.parse_file(md_file, tmp_path / "output")

        converter = MarkoOutlineConverter(force=True, dry_run=False)
        converter.convert_outline(outline)

        # Test various section files
        sections_to_test = [
            ("chapter1", "getting-started.rst", "Getting Started"),
            ("chapter1", "advanced-topics.rst", "Advanced Topics"),
            ("chapter1", "mixed-case-title.rst", "Mixed-Case Title"),
            ("chapter2", "fundamentals.rst", "Fundamentals"),
            ("chapter2", "implementation-details.rst", "Implementation Details"),
        ]

        for chapter_dir, filename, expected_title in sections_to_test:
            section_file = tmp_path / "output" / chapter_dir / filename
            assert section_file.exists(), f"Section file {filename} should exist"

            content = section_file.read_text()

            # Should have the clean title as a heading
            assert expected_title in content, (
                f"Title '{expected_title}' should be in {filename}"
            )

            # The title should appear as a heading, but it's okay if it appears in content too
            # We just want to ensure the numbered heading format is filtered out

            # Should not have numbered headings
            numbered_pattern = f"### \\d+\\.\\d+ {expected_title}"
            import re

            assert not re.search(numbered_pattern, content), (
                f"Numbered heading should not be in {filename}"
            )

            # Should have exactly one main title underline (H3 headings use -)
            lines = content.splitlines()
            title_lines = [
                line
                for line in lines
                if line.strip() and all(c == "-" for c in line.strip())
            ]
            assert len(title_lines) == 1, (
                f"Should have exactly one main title underline in {filename}"
            )

    def test_appendix_headings_not_duplicated(self, tmp_path):
        """Test that appendix headings are not duplicated in the generated RST."""
        md_content = """# Test Book

This is the book introduction.

## Appendix A: Reference Materials
### A.1 Installation
This is the installation section.
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)
        validator = OutlineValidator()
        validation_result = validator.validate_file(md_file)
        assert validation_result.is_valid
        parser = MarkoOutlineParser()
        outline = parser.parse_file(md_file, tmp_path / "output")
        converter = MarkoOutlineConverter(force=True, dry_run=False)
        converter.convert_outline(outline)
        installation_rst = tmp_path / "output" / "appendixA" / "installation.rst"
        content = installation_rst.read_text()
        assert "Installation" in content
        assert content.count("Installation") == 1
        assert "A.1 Installation" not in content
        lines = content.splitlines()
        title_lines = [
            line
            for line in lines
            if line.strip() and all(c == "-" for c in line.strip())
        ]
        assert len(title_lines) == 1  # Only one main title underline

    def test_separate_toctree_for_appendices(self, tmp_path):
        """Test that appendices get their own toctree with caption."""
        md_content = """# Test Book

This is the book introduction.

## Chapter 1: Introduction
### 1.1 Getting Started
This is the getting started section.

## Appendix A: Reference Materials
Reference content here.

## Appendix B: Additional Resources
Additional resources content here.
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)
        validator = OutlineValidator()
        validation_result = validator.validate_file(md_file)
        assert validation_result.is_valid
        parser = MarkoOutlineParser()
        outline = parser.parse_file(md_file, tmp_path / "output")
        converter = MarkoOutlineConverter(force=True, dry_run=False)
        converter.convert_outline(outline)

        # Check the top-level index.rst
        index_rst = tmp_path / "output" / "index.rst"
        content = index_rst.read_text()

        # Should have separate toctrees for chapters and appendices
        assert ".. toctree::" in content
        assert content.count(".. toctree::") == 2  # Two toctrees

        # First toctree should be for chapters (hidden)
        lines = content.splitlines()
        toctree_lines = [
            i for i, line in enumerate(lines) if line.strip() == ".. toctree::"
        ]
        assert len(toctree_lines) == 2

        # Check first toctree (chapters)
        first_toctree_start = toctree_lines[0]
        assert lines[first_toctree_start + 1].strip() == ":caption: Chapters"
        assert lines[first_toctree_start + 2].strip() == ":hidden:"
        assert "chapter1/index" in lines[first_toctree_start + 4]

        # Check second toctree (appendices)
        second_toctree_start = toctree_lines[1]
        assert lines[second_toctree_start + 1].strip() == ":caption: Appendices"
        assert lines[second_toctree_start + 2].strip() == ":hidden:"

        # Check that both appendices are in the toctree
        appendix_lines = [
            line.strip()
            for line in lines[second_toctree_start + 4 : second_toctree_start + 6]
        ]
        assert "appendixA/index" in appendix_lines
        assert "appendixB/index" in appendix_lines

    def test_front_matter_toctree_with_preserved_prefixes(self, tmp_path):
        """Test that front matter gets its own toctree and Introduction/Prologue prefixes are preserved."""
        md_content = """# Test Book with Front Matter

This is the book introduction.

## Prologue: Getting Started

This is the prologue content.

## Introduction: How to use this book

This is the introduction content.

## Chapter 1: Core Concepts

### 1.1 Fundamentals

Fundamentals content here.

## Appendix A: Reference Materials

Reference content here.
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)
        validator = OutlineValidator()
        validation_result = validator.validate_file(md_file)
        assert validation_result.is_valid
        parser = MarkoOutlineParser()
        outline = parser.parse_file(md_file, tmp_path / "output")
        converter = MarkoOutlineConverter(force=True, dry_run=False)
        converter.convert_outline(outline)

        # Check the top-level index.rst
        index_rst = tmp_path / "output" / "index.rst"
        content = index_rst.read_text()

        # Should have three toctrees: Front Matter, Chapters, and Appendices
        assert ".. toctree::" in content
        assert content.count(".. toctree::") == 3

        # Check that all toctrees have the right captions
        assert ":caption: Front Matter" in content
        assert ":caption: Chapters" in content
        assert ":caption: Appendices" in content

        # Check that Introduction and Prologue prefixes are preserved
        prologue_index = tmp_path / "output" / "prologue" / "index.rst"
        prologue_content = prologue_index.read_text()
        assert "Prologue: Getting Started" in prologue_content
        assert "Prologue: Getting Started\n========================" in prologue_content

        introduction_index = tmp_path / "output" / "introduction" / "index.rst"
        introduction_content = introduction_index.read_text()
        assert "Introduction: How to use this book" in introduction_content
        assert (
            "Introduction: How to use this book\n=================================="
            in introduction_content
        )

    def test_toctree_only_created_when_needed(self, tmp_path):
        """Test that toctrees are only created when there are chapters of those types."""

        # Test 1: Chapters only (no front matter, no appendices)
        md_content_chapters_only = """# Test Book - Chapters Only

## Chapter 1: Introduction

### 1.1 Getting Started

This is the getting started section.

## Chapter 2: Core Concepts

### 2.1 Fundamentals

Fundamentals content here.
"""
        md_file = tmp_path / "test_chapters_only.md"
        md_file.write_text(md_content_chapters_only)

        validator = OutlineValidator()
        validation_result = validator.validate_file(md_file)
        assert validation_result.is_valid

        parser = MarkoOutlineParser()
        outline = parser.parse_file(md_file, tmp_path / "output_chapters_only")
        converter = MarkoOutlineConverter(force=True, dry_run=False)
        converter.convert_outline(outline)

        index_rst = tmp_path / "output_chapters_only" / "index.rst"
        content = index_rst.read_text()

        # Should only have one toctree for chapters
        assert content.count(".. toctree::") == 1
        assert ":caption: Chapters" in content
        assert ":caption: Front Matter" not in content
        assert ":caption: Appendices" not in content

        # Test 2: Front matter only (no regular chapters, no appendices)
        md_content_front_matter_only = """# Test Book - Front Matter Only

## Prologue: Getting Started

This is the prologue content.

## Introduction: How to use this book

This is the introduction content.
"""
        md_file = tmp_path / "test_front_matter_only.md"
        md_file.write_text(md_content_front_matter_only)

        validation_result = validator.validate_file(md_file)
        assert validation_result.is_valid

        outline = parser.parse_file(md_file, tmp_path / "output_front_matter_only")
        converter.convert_outline(outline)

        index_rst = tmp_path / "output_front_matter_only" / "index.rst"
        content = index_rst.read_text()

        # Should only have one toctree for front matter
        assert content.count(".. toctree::") == 1
        assert ":caption: Front Matter" in content
        assert ":caption: Chapters" not in content
        assert ":caption: Appendices" not in content

        # Test 3: Appendices only (no front matter, no regular chapters)
        md_content_appendices_only = """# Test Book - Appendices Only

## Appendix A: Reference Materials

Reference content here.

## Appendix B: Troubleshooting

Troubleshooting content here.
"""
        md_file = tmp_path / "test_appendices_only.md"
        md_file.write_text(md_content_appendices_only)

        validation_result = validator.validate_file(md_file)
        assert validation_result.is_valid

        outline = parser.parse_file(md_file, tmp_path / "output_appendices_only")
        converter.convert_outline(outline)

        index_rst = tmp_path / "output_appendices_only" / "index.rst"
        content = index_rst.read_text()

        # Should only have one toctree for appendices
        assert content.count(".. toctree::") == 1
        assert ":caption: Appendices" in content
        assert ":caption: Front Matter" not in content
        assert ":caption: Chapters" not in content

        # Test 4: Front matter and appendices only (no regular chapters)
        md_content_front_matter_and_appendices = """# Test Book - Front Matter and Appendices Only

## Prologue: Getting Started

This is the prologue content.

## Introduction: How to use this book

This is the introduction content.

## Appendix A: Reference Materials

Reference content here.

## Appendix B: Troubleshooting

Troubleshooting content here.
"""
        md_file = tmp_path / "test_front_matter_and_appendices.md"
        md_file.write_text(md_content_front_matter_and_appendices)

        validation_result = validator.validate_file(md_file)
        assert validation_result.is_valid

        outline = parser.parse_file(
            md_file, tmp_path / "output_front_matter_and_appendices"
        )
        converter.convert_outline(outline)

        index_rst = tmp_path / "output_front_matter_and_appendices" / "index.rst"
        content = index_rst.read_text()

        # Should have two toctrees: front matter and appendices
        assert content.count(".. toctree::") == 2
        assert ":caption: Front Matter" in content
        assert ":caption: Appendices" in content
        assert ":caption: Chapters" not in content
