"""
Tests for CLI utilities.
"""

from __future__ import annotations

from unittest.mock import patch

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

from rstbuddy.cli.utils import (
    console,
    create_progress,
    print_error,
    print_info,
    print_success,
    stderr_console,
)


class TestConsole:
    """Test console objects."""

    def test_console_objects_exist(self):
        """Test that console objects are properly initialized."""
        assert isinstance(console, Console)
        assert isinstance(stderr_console, Console)
        assert console != stderr_console


class TestCreateProgress:
    """Test progress creation."""

    def test_create_progress(self):
        """Test progress creation returns a Progress object."""
        progress = create_progress()
        assert isinstance(progress, Progress)

    def test_create_progress_has_spinner(self):
        """Test progress has spinner column."""
        progress = create_progress()
        # Check that it has a spinner column
        column_types = [type(col) for col in progress.columns]
        assert any("Spinner" in str(col_type) for col_type in column_types)

    def test_create_progress_has_text_column(self):
        """Test progress has text column."""
        progress = create_progress()
        # Check that it has a text column
        column_types = [type(col) for col in progress.columns]
        assert any("Text" in str(col_type) for col_type in column_types)


class TestPrintError:
    """Test error printing functions."""

    def test_print_error_basic(self, capsys):  # noqa: ARG002
        """Test basic error printing."""
        with patch.object(stderr_console, "print") as mock_print:
            print_error("Test error message")
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert isinstance(call_args, Panel)

    def test_print_error_with_suggestions(self, capsys):  # noqa: ARG002
        """Test error printing with suggestions."""
        suggestions = ["Fix this", "Try that"]
        with patch.object(stderr_console, "print") as mock_print:
            print_error("Test error", suggestions)
            # Should be called multiple times: once for error, once for
            # suggestions header, once for each suggestion
            assert mock_print.call_count >= 2  # noqa: PLR2004

    def test_print_error_without_suggestions(self, capsys):  # noqa: ARG002
        """Test error printing without suggestions."""
        with patch.object(stderr_console, "print") as mock_print:
            print_error("Test error")
            # Should be called once for error only
            assert mock_print.call_count == 1

    def test_print_error_panel_styling(self, capsys):  # noqa: ARG002
        """Test error panel has correct styling."""
        with patch.object(stderr_console, "print") as mock_print:
            print_error("Test error")
            call_args = mock_print.call_args[0][0]
            panel = call_args
            assert hasattr(panel, "border_style")


class TestPrintSuccess:
    """Test success printing functions."""

    def test_print_success_basic(self, capsys):  # noqa: ARG002
        """Test basic success printing."""
        with patch.object(stderr_console, "print") as mock_print:
            print_success("Test success message")
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert isinstance(call_args, Panel)

    def test_print_success_panel_styling(self, capsys):  # noqa: ARG002
        """Test success panel has correct styling."""
        with patch.object(stderr_console, "print") as mock_print:
            print_success("Test success")
            call_args = mock_print.call_args[0][0]
            panel = call_args
            assert hasattr(panel, "border_style")


class TestPrintInfo:
    """Test info printing functions."""

    def test_print_info_basic(self, capsys):  # noqa: ARG002
        """Test basic info printing."""
        with patch.object(stderr_console, "print") as mock_print:
            print_info("Test info message")
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert isinstance(call_args, Panel)

    def test_print_info_panel_styling(self, capsys):  # noqa: ARG002
        """Test info panel has correct styling."""
        with patch.object(stderr_console, "print") as mock_print:
            print_info("Test info")
            call_args = mock_print.call_args[0][0]
            panel = call_args
            assert hasattr(panel, "border_style")


class TestConsoleQuietMode:
    """Test console quiet mode functionality."""

    def test_console_quiet_mode(self):
        """Test that console can be set to quiet mode."""
        original_quiet = getattr(console, "quiet", False)
        try:
            console.quiet = True
            assert console.quiet is True
        finally:
            console.quiet = original_quiet

    def test_stderr_console_quiet_mode(self):
        """Test that stderr console can be set to quiet mode."""
        original_quiet = getattr(stderr_console, "quiet", False)
        try:
            stderr_console.quiet = True
            assert stderr_console.quiet is True
        finally:
            stderr_console.quiet = original_quiet
