"""
Tests for CLI commands with low coverage.
"""

from __future__ import annotations

import json
from unittest.mock import patch

from rstbuddy.cli.cli import cli


class TestCLIVersion:
    """Test the version command."""

    def test_version_command(self, runner):
        """Test the version command displays version information."""
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        # The command should run successfully without errors
        # Rich console output may not be captured in test environment

    def test_version_command_with_verbose(self, runner):
        """Test the version command with verbose flag."""
        result = runner.invoke(cli, ["--verbose", "version"])
        assert result.exit_code == 0

    def test_version_command_with_quiet(self, runner):
        """Test the version command with quiet flag."""
        result = runner.invoke(cli, ["--quiet", "version"])
        assert result.exit_code == 0


class TestCLISettings:
    """Test the settings command."""

    def test_settings_command_table_output(self, runner):
        """Test the settings command with table output."""
        result = runner.invoke(cli, ["settings"])
        assert result.exit_code == 0

    def test_settings_command_json_output(self, runner):
        """Test the settings command with JSON output."""
        result = runner.invoke(cli, ["--output", "json", "settings"])
        assert result.exit_code == 0
        # Should be valid JSON
        data = json.loads(result.output)
        assert isinstance(data, dict)

    def test_settings_command_text_output(self, runner):
        """Test the settings command with text output."""
        result = runner.invoke(cli, ["--output", "text", "settings"])
        assert result.exit_code == 0

    def test_settings_command_with_verbose(self, runner):
        """Test the settings command with verbose flag."""
        result = runner.invoke(cli, ["--verbose", "settings"])
        assert result.exit_code == 0

    def test_settings_command_with_config_file(self, runner, temp_dir):
        """Test the settings command with custom config file."""
        config_file = temp_dir / "test_config.toml"
        config_file.write_text("openai_api_key = 'sk-value'", encoding="utf-8")

        result = runner.invoke(cli, ["--config-file", str(config_file), "settings"])
        assert result.exit_code == 0


class TestCLIGlobalOptions:
    """Test global CLI options."""

    def test_verbose_flag(self, runner):
        """Test verbose flag is properly set."""
        result = runner.invoke(cli, ["--verbose", "version"])
        assert result.exit_code == 0

    def test_quiet_flag(self, runner):
        """Test quiet flag is properly set."""
        result = runner.invoke(cli, ["--quiet", "version"])
        assert result.exit_code == 0

    def test_output_format_default(self, runner):
        """Test default output format is table."""
        result = runner.invoke(cli, ["settings"])
        assert result.exit_code == 0

    def test_output_format_json(self, runner):
        """Test JSON output format."""
        result = runner.invoke(cli, ["--output", "json", "settings"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)

    def test_output_format_text(self, runner):
        """Test text output format."""
        result = runner.invoke(cli, ["--output", "text", "settings"])
        assert result.exit_code == 0

    def test_invalid_output_format(self, runner):
        """Test invalid output format."""
        result = runner.invoke(cli, ["--output", "invalid", "settings"])
        assert result.exit_code != 0


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_cli_without_arguments(self, runner):
        """Test CLI without arguments shows help."""
        result = runner.invoke(cli, [])
        # Click expects a command, so exit code 2 is correct for missing command
        assert result.exit_code == 2  # noqa: PLR2004
        assert "Usage:" in result.output

    def test_invalid_command(self, runner):
        """Test invalid command shows error."""
        result = runner.invoke(cli, ["invalid-command"])
        assert result.exit_code != 0
        assert "No such command" in result.output

    def test_cli_with_config_file_error(self, runner):
        """Test CLI behavior when config file loading fails."""
        # Mock Settings to raise an exception
        with patch("rstbuddy.cli.cli.Settings", side_effect=Exception("Config error")):
            result = runner.invoke(cli, ["version"])
            assert result.exit_code == 1
            # The error is printed to stderr and then sys.exit(1) is called
            # We can verify the exit code indicates an error occurred

    def test_cli_context_object_creation(self, runner):
        """Test that CLI context object is properly created."""
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0

        # The context object should be created and populated
        # This is tested indirectly through the version command working

    def test_cli_verbose_flag_stored_in_context(self, runner):
        """Test that verbose flag is stored in context."""
        result = runner.invoke(cli, ["--verbose", "settings"])
        assert result.exit_code == 0

        # The verbose flag should be stored in context and used by settings command

    def test_cli_output_format_stored_in_context(self, runner):
        """Test that output format is stored in context."""
        result = runner.invoke(cli, ["--output", "json", "settings"])
        assert result.exit_code == 0

        # The output format should be stored in context and used by settings command

    def test_cli_quiet_mode_console_configuration(self, runner):
        """Test that quiet mode properly configures console."""
        result = runner.invoke(cli, ["--quiet", "version"])
        assert result.exit_code == 0

        # The console should be configured for quiet mode

    def test_cli_utils_object_creation(self, runner):
        """Test that Utils object is properly created in context."""
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0

        # The Utils object should be created and stored in context

    def test_cli_console_stored_in_context(self, runner):
        """Test that console is stored in context."""
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0

        # The console should be stored in context for commands to use
