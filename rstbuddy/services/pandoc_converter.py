"""
Enhanced RST to Markdown conversion service using pandoc.

Handles conversion of RST recipe files to Markdown files using pandoc
with custom post-processing for specific requirements.
"""

from __future__ import annotations

import platform
import re
import subprocess
from pathlib import Path

import mdformat

from ..exc import ConversionError, NoPandocError


def get_pandoc_installation_instructions() -> str:  # noqa: PLR0911
    """
    Get OS-dependent pandoc installation instructions.

    Returns:
        Installation instructions for the current operating system

    """
    system = platform.system().lower()

    if system == "darwin":  # macOS
        return """To install pandoc on macOS:

1. Using Homebrew (recommended):
   brew install pandoc

2. Using MacPorts:
   sudo port install pandoc

3. Download from https://pandoc.org/installing.html"""

    if system == "linux":
        # Try to detect the distribution
        try:
            with Path("/etc/os-release").open(encoding="utf-8") as f:
                content = f.read().lower()
                if "ubuntu" in content or "debian" in content:
                    return """To install pandoc on Ubuntu/Debian:

sudo apt-get update
sudo apt-get install pandoc

Or for the latest version:
sudo apt-get install software-properties-common
sudo apt-add-repository 'deb https://pandoc.org/installing.html ubuntu/'
sudo apt-get update
sudo apt-get install pandoc"""
                if (
                    "fedora" in content
                    or "redhat" in content
                    or "centos" in content
                    or "amazon" in content
                ):
                    return """To install pandoc on Fedora/RHEL/CentOS/Amazon Linux:

sudo dnf install pandoc

Or for older versions:

sudo yum install pandoc"""
                # Don't know what Linux this is
                return """To install pandoc on Linux:

1. Using your package manager (e.g., apt, dnf, yum, pacman)
2. Download from https://pandoc.org/installing.html
3. Or use the package manager specific to your distribution"""
        except FileNotFoundError:
            return """To install pandoc on Linux:

1. Using your package manager (e.g., apt, dnf, yum, pacman)
2. Download from https://pandoc.org/installing.html"""

    elif system == "windows":
        return """To install pandoc on Windows:

1. Download the installer from https://pandoc.org/installing.html
2. Run the installer and follow the setup wizard
3. Or use Chocolatey: choco install pandoc
4. Or use Scoop: scoop install pandoc
5. Or use Windows Subsystem for Linux (WSL) and install via apt/dnf"""

    else:
        return """To install pandoc:

1. Visit https://pandoc.org/installing.html
2. Download the appropriate version for your operating system
3. Follow the installation instructions for your platform"""


class PandocConverter:
    """
    Enhanced RST to Markdown converter using pandoc with custom post-processing.

    Handles the complete conversion process including content transformation,
    metadata generation, and documentation creation with improved RST parsing.
    """

    def __init__(self) -> None:
        """
        Initialize the converter.
        """
        # See if pandoc is installed
        try:
            subprocess.run(["pandoc", "--version"], check=True)
        except FileNotFoundError as e:
            msg = "Pandoc is not installed"
            raise NoPandocError(msg) from e

    def convert_rst_to_md(self, rst_content: str) -> str:
        """
        Convert RST content to Markdown content using pandoc with post-processing.

        Args:
            rst_content: The RST content to convert

        Returns:
            Converted Markdown content

        Raises:
            ConversionError: If conversion fails

        """
        try:
            # Pre-process RST content to handle Sphinx-specific elements
            processed_content = self._preprocess_rst_content(rst_content)

            # Convert using pandoc
            markdown_content = self._convert_with_pandoc(processed_content)

            # Post-process the markdown content
            content = self._postprocess_markdown_content(markdown_content)

            # Format markdown content with mdformat
            content = self._format_markdown_with_mdformat(content)

        except Exception as e:
            msg = f"Failed to convert RST to Markdown: {e}"
            raise ConversionError(msg) from e
        else:
            return content

    def _preprocess_rst_content(self, content: str) -> str:
        """
        Pre-process RST content to handle Sphinx-specific elements before pandoc
        conversion.

        Args:
            content: The original RST content

        Returns:
            Pre-processed RST content

        """
        # Remove Sphinx targets (.. _<any text>:) - remove entire lines
        lines = content.split("\n")
        filtered_lines = []
        for line in lines:
            if not line.strip().startswith(".. _") or not line.strip().endswith(":"):
                filtered_lines.append(line)  # noqa: PERF401
        return "\n".join(filtered_lines)

    def _convert_with_pandoc(self, content: str) -> str:
        """
        Convert RST content to markdown using pandoc.

        Args:
            content: The RST content to convert

        Returns:
            Converted markdown content

        Raises:
            ConversionError: If pandoc conversion fails

        """
        try:
            # Use subprocess to call pandoc
            result = subprocess.run(
                ["pandoc", "-f", "rst", "-t", "markdown"],
                input=content,
                text=True,
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            error_msg = f"Pandoc conversion failed with exit code {e.returncode}"
            if e.stderr:
                error_msg += f": {e.stderr.strip()}"
            raise ConversionError(error_msg) from e
        except FileNotFoundError as e:
            instructions = get_pandoc_installation_instructions()
            msg = f"Pandoc is not installed or not found in PATH.\n\n{instructions}"
            raise ConversionError(msg) from e
        else:
            return result.stdout

    def _postprocess_markdown_content(self, content: str) -> str:
        """
        Post-process markdown content to handle specific requirements.

        Args:
            content: The markdown content from pandoc

        Returns:
            Post-processed markdown content

        """
        # Note: [Human] and [AI] lines are now handled in pre-processing

        # Fix any malformed code blocks
        content = self._fix_code_blocks(content)

        # Remove empty sections
        content = self._remove_empty_sections(content)

        # Clean up extra whitespace
        return re.sub(r"\n{3,}", r"\n\n", content)

    def _fix_code_blocks(self, content: str) -> str:
        """
        Fix malformed code blocks.

        Args:
            content: The content to process

        Returns:
            Content with fixed code blocks

        """
        # Ensure code blocks are properly closed
        lines = content.split("\n")
        fixed_lines = []
        in_code_block = False

        for line in lines:
            if line.startswith("```"):
                if in_code_block:  # noqa: SIM108
                    # Close the code block
                    in_code_block = False
                else:
                    # Open a new code block
                    in_code_block = True
                fixed_lines.append(line)
            else:
                fixed_lines.append(line)

        # If we're still in a code block at the end, close it
        if in_code_block:
            fixed_lines.append("```")

        return "\n".join(fixed_lines)

    def _remove_empty_sections(self, content: str) -> str:
        """
        Remove empty sections from the content.

        Args:
            content: The content to process

        Returns:
            Content with empty sections removed

        """
        lines = content.split("\n")
        result_lines = []
        skip_until_next_heading = False

        for i, line in enumerate(lines):
            # Check if this is a heading
            if line.startswith("#"):
                # Look ahead to see if this section is empty
                section_content = []
                j = i + 1
                while j < len(lines) and not lines[j].startswith("#"):
                    if lines[j].strip():
                        section_content.append(lines[j])
                    j += 1

                # If section has content, include it
                if section_content:
                    skip_until_next_heading = False
                    result_lines.append(line)
                else:
                    # Skip this heading and its empty content
                    skip_until_next_heading = True
            elif not skip_until_next_heading:
                result_lines.append(line)

        return "\n".join(result_lines)

    def _format_markdown_with_mdformat(self, content: str) -> str:
        """
        Format markdown content using mdformat library.

        Args:
            content: The markdown content to format

        Returns:
            Formatted markdown content

        Raises:
            ConversionError: If mdformat formatting fails

        """
        try:
            return mdformat.text(content, options={"number": True, "wrap": 1000})
        except ImportError:
            # If mdformat is not available, return content as-is
            return content
        except Exception:  # noqa: BLE001
            # If formatting fails, return content as-is but log the error
            return content
