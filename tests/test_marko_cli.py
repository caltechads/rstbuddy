"""
Tests for the new outline-to-rst CLI command.
"""

import pytest
from click.testing import CliRunner
from pathlib import Path

from rstbuddy.cli.cli import cli


class TestMarkoCLI:
    """Test the new outline-to-rst CLI command."""

    def test_outline_to_rst_help(self):
        """Test that the outline-to-rst command shows help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["outline-to-rst", "--help"])

        assert result.exit_code == 0
        assert (
            "Convert a markdown outline to RST file structure using Marko parser"
            in result.output
        )
        assert "--force" in result.output
        assert "--output-dir" in result.output
        assert "--dry-run" in result.output

    def test_outline_to_rst_dry_run(self, temp_dir):
        """Test that the outline-to-rst command works with dry-run."""
        # Create a simple test markdown file
        test_content = """# Test Book

## Chapter 1: Getting Started

This is chapter 1 content.

### 1.1 First Section
Section content here.

## Chapter 2: Advanced Topics

### 2.1 First Section
This is a section.
"""

        test_file = temp_dir / "test_outline.md"
        test_file.write_text(test_content, encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(cli, ["outline-to-rst", str(test_file), "--dry-run"])

        assert result.exit_code == 0
        # Check that the command succeeded and didn't create any files
        assert not (temp_dir / "index.rst").exists()
        assert not (temp_dir / "chapter1").exists()

    def test_outline_to_rst_actual_conversion(self, temp_dir):
        """Test that the outline-to-rst command actually converts files."""
        # Create a simple test markdown file
        test_content = """# Test Book

## Chapter 1: Getting Started

This is chapter 1 content.

### 1.1 First Section
Section content here.
"""

        test_file = temp_dir / "test_outline.md"
        test_file.write_text(test_content, encoding="utf-8")

        output_dir = temp_dir / "marko_output"

        runner = CliRunner()
        result = runner.invoke(
            cli, ["outline-to-rst", str(test_file), "--output-dir", str(output_dir)]
        )

        assert result.exit_code == 0

        # Check that files were actually created
        assert output_dir.exists()
        assert (output_dir / "index.rst").exists()
        assert (output_dir / "chapter1").exists()
        assert (output_dir / "chapter1" / "index.rst").exists()
        assert (output_dir / "chapter1" / "first-section.rst").exists()
