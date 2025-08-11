"""
Tests for the summarize CLI command.
"""

from __future__ import annotations

from rstbuddy.cli.cli import cli


class TestSummarizeCommand:
    """Test the summarize command."""

    def test_summarize_command_file_not_found(self, runner):
        """Test summarize command with non-existent file."""
        result = runner.invoke(cli, ["summarize", "nonexistent.rst"])

        # Should fail because file doesn't exist
        assert result.exit_code != 0

    def test_summarize_command_help(self, runner):
        """Test summarize command shows help."""
        result = runner.invoke(cli, ["summarize", "--help"])
        assert result.exit_code == 0
        assert "summarize" in result.output

    def test_summarize_command_invalid_file_type(self, runner):
        """Test summarize command with invalid file type."""
        result = runner.invoke(cli, ["summarize", "test.txt"])
        # Should fail because it's not an RST file
        assert result.exit_code != 0

    def test_summarize_command_missing_argument(self, runner):
        """Test summarize command without file argument."""
        result = runner.invoke(cli, ["summarize"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output

    def test_summarize_command_extra_arguments(self, runner):
        """Test summarize command with extra arguments."""
        result = runner.invoke(cli, ["summarize", "file1.rst", "file2.rst"])
        # Click validates file existence before checking for extra arguments
        assert result.exit_code != 0
        assert "Invalid value for 'RST_FILE'" in result.output
