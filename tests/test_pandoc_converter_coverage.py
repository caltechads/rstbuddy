"""
Tests to cover missing lines in the pandoc converter service.
"""

from __future__ import annotations

from subprocess import CalledProcessError
from unittest.mock import patch

import pytest

from rstbuddy.exc import ConversionError
from rstbuddy.services.pandoc_converter import (
    PandocConverter,
    get_pandoc_installation_instructions,
)


class TestGetPandocInstallationInstructions:
    """Test the get_pandoc_installation_instructions function to cover missing lines."""

    def test_get_pandoc_instructions_darwin(self):
        """Test installation instructions for macOS."""
        with patch("platform.system", return_value="Darwin"):
            instructions = get_pandoc_installation_instructions()
            assert "macOS" in instructions
            assert "Homebrew" in instructions
            assert "brew install pandoc" in instructions

    def test_get_pandoc_instructions_linux_ubuntu(self):
        """Test installation instructions for Ubuntu/Debian."""
        with patch("platform.system", return_value="Linux"):  # noqa: SIM117
            with patch("pathlib.Path.open") as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = (
                    "ubuntu"
                )
                instructions = get_pandoc_installation_instructions()
                assert "Ubuntu/Debian" in instructions
                assert "sudo apt-get install pandoc" in instructions

    def test_get_pandoc_instructions_linux_fedora(self):
        """Test installation instructions for Fedora/RHEL."""
        with patch("platform.system", return_value="Linux"):  # noqa: SIM117
            with patch("pathlib.Path.open") as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = (
                    "fedora"
                )
                instructions = get_pandoc_installation_instructions()
                assert "Fedora/RHEL/CentOS/Amazon Linux" in instructions
                assert "sudo dnf install pandoc" in instructions

    def test_get_pandoc_instructions_linux_generic(self):
        """Test installation instructions for generic Linux."""
        with patch("platform.system", return_value="Linux"):  # noqa: SIM117
            with patch("pathlib.Path.open", side_effect=FileNotFoundError):
                instructions = get_pandoc_installation_instructions()
                assert "Linux" in instructions
                assert "package manager" in instructions

    def test_get_pandoc_instructions_linux_unknown_distro(self):
        """Test installation instructions for unknown Linux distribution."""
        with patch("platform.system", return_value="Linux"):  # noqa: SIM117
            with patch("pathlib.Path.open") as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = (
                    "unknown_distro"
                )
                instructions = get_pandoc_installation_instructions()
                assert "Linux" in instructions
                assert "package manager" in instructions

    def test_get_pandoc_instructions_windows(self):
        """Test installation instructions for Windows."""
        with patch("platform.system", return_value="Windows"):
            instructions = get_pandoc_installation_instructions()
            assert "Windows" in instructions
            assert "installer" in instructions
            assert "Chocolatey" in instructions

    def test_get_pandoc_instructions_unknown_platform(self):
        """Test installation instructions for unknown platform."""
        with patch("platform.system", return_value="Unknown"):
            instructions = get_pandoc_installation_instructions()
            assert "https://pandoc.org/installing.html" in instructions

    def test_get_pandoc_instructions_linux_centos(self):
        """Test installation instructions for CentOS."""
        with patch("platform.system", return_value="Linux"):  # noqa: SIM117
            with patch("pathlib.Path.open") as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = (
                    "centos"
                )
                instructions = get_pandoc_installation_instructions()
                assert "Fedora/RHEL/CentOS/Amazon Linux" in instructions
                assert "sudo dnf install pandoc" in instructions

    def test_get_pandoc_instructions_linux_redhat(self):
        """Test installation instructions for RedHat."""
        with patch("platform.system", return_value="Linux"):  # noqa: SIM117
            with patch("pathlib.Path.open") as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = (
                    "redhat"
                )
                instructions = get_pandoc_installation_instructions()
                assert "Fedora/RHEL/CentOS/Amazon Linux" in instructions
                assert "sudo dnf install pandoc" in instructions

    def test_get_pandoc_instructions_linux_amazon(self):
        """Test installation instructions for Amazon Linux."""
        with patch("platform.system", return_value="Linux"):  # noqa: SIM117
            with patch("pathlib.Path.open") as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = (
                    "amazon"
                )
                instructions = get_pandoc_installation_instructions()
                assert "Fedora/RHEL/CentOS/Amazon Linux" in instructions
                assert "sudo dnf install pandoc" in instructions


class TestPandocConverterErrorHandling:
    """Test error handling in PandocConverter to cover missing lines."""

    def test_convert_with_pandoc_called_process_error(self):
        """Test handling of CalledProcessError in _convert_with_pandoc."""
        with patch("subprocess.run") as mock_run:
            # Mock the version check in __init__
            mock_run.return_value.returncode = 0

            converter = PandocConverter()

            # Mock the conversion to fail with CalledProcessError

            mock_run.side_effect = CalledProcessError(
                1, "pandoc", stderr=b"Error message"
            )

            with pytest.raises(ConversionError) as exc_info:
                converter.convert_rst_to_md("# Title\n\nContent")

            assert "Pandoc conversion failed with exit code 1" in str(exc_info.value)
            assert "Error message" in str(exc_info.value)

    def test_convert_with_pandoc_file_not_found_error(self):
        """Test handling of FileNotFoundError in _convert_with_pandoc."""
        with patch("subprocess.run") as mock_run:
            # Mock the version check in __init__
            mock_run.return_value.returncode = 0

            converter = PandocConverter()

            # Mock the conversion to fail with FileNotFoundError
            mock_run.side_effect = FileNotFoundError("pandoc not found")

            with pytest.raises(ConversionError) as exc_info:
                converter.convert_rst_to_md("# Title\n\nContent")

            assert "Pandoc is not installed or not found in PATH" in str(exc_info.value)
            assert "To install pandoc" in str(exc_info.value)

    def test_convert_with_pandoc_called_process_error_no_stderr(self):
        """
        Test handling of CalledProcessError without stderr in _convert_with_pandoc.
        """
        with patch("subprocess.run") as mock_run:
            # Mock the version check in __init__
            mock_run.return_value.returncode = 0

            converter = PandocConverter()

            mock_error = CalledProcessError(1, "pandoc")
            mock_error.stderr = None
            mock_run.side_effect = mock_error

            with pytest.raises(ConversionError) as exc_info:
                converter.convert_rst_to_md("# Title\n\nContent")

            assert "Pandoc conversion failed with exit code 1" in str(exc_info.value)
            assert "Error message" not in str(exc_info.value)
