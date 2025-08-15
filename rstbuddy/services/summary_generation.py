"""
Summary generation service for Cursor rules.

Uses OpenAI API to generate concise summaries of RST rule files.
"""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, Final

import openai
from openai import OpenAI
from rich.console import Console

from ..exc import ConfigurationError, FileError
from .pandoc_converter import PandocConverter

if TYPE_CHECKING:
    from ..settings import Settings

_SYSTEM_PROMPT: Final[str] = """
You are a technical documentation expert.

Generate concise, informative summaries of RST documentation files. The summary
should be 10 sentences maximum. The summary should be in the same language as
the documentation file.",

"""


_USER_PROMPT: Final[str] = """
Please generate a concise, informative summary of this documentation file.

Content:
{content}  # Limit content length for API

Requirements:
- 10 sentences maximum
- Focus on the main purpose and key features
- Use clear, technical language
- Avoid redundant phrases like "This rule provides" or "This document contains"
- Be specific about what the rule covers

Summary:"""


class SummaryGenerationService:
    """
    Service for generating AI-powered summaries of RST rule files.

    Uses OpenAI API to generate concise, informative summaries that are stored
    as `.. summary::` directives in RST files.
    """

    def __init__(self, settings: Settings, console: Console | None = None) -> None:
        """
        Initialize the summary generation service.

        Args:
            settings: Application settings containing OpenAI configuration
            console: Rich console for output (optional)

        """
        self.settings = settings
        self.console = console or Console()

        # Configure OpenAI client
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key

    def generate_summary(self, rst_content: str) -> str:
        """
        Generate a summary for RST content using OpenAI API.

        Args:
            rst_content: The RST content to summarize
            rule_name: Optional name of the rule for context

        Returns:
            Generated summary text (2-3 sentences)

        Raises:
            ConfigurationError: If OpenAI API is not configured
            FileError: If summary generation fails

        """
        if not self.settings.openai_api_key:
            msg = (
                "OpenAI API key is required for summary generation. "
                "Set RSTBUDDY_OPENAI_API_KEY environment variable "
                "or add openai_api_key to .rstbuddy.toml"
            )
            raise ConfigurationError(msg)

        try:
            # Prepare the prompt for OpenAI
            prompt = self._create_summary_prompt(rst_content)

            # Call OpenAI API
            client = OpenAI(api_key=self.settings.openai_api_key)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": _SYSTEM_PROMPT,
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1000,
                temperature=0.3,
            )

            summary = response.choices[0].message.content or ""
            summary = summary.strip()

            # Clean up the summary
            return self._clean_summary(summary)

        except Exception as e:
            if "authentication" in str(e).lower() or "invalid" in str(e).lower():
                msg = "Invalid OpenAI API key. Please check your configuration."
                raise ConfigurationError(msg) from e
            if "rate limit" in str(e).lower():
                msg = "OpenAI API rate limit exceeded. Please try again later."
                raise FileError(msg) from e
            msg = f"OpenAI API error: {e}"
            raise FileError(msg) from e

    def _create_summary_prompt(self, rst_content: str) -> str:
        """
        Create a prompt for OpenAI API.

        Args:
            rst_content: The RST content to summarize

        Returns:
            Formatted prompt for OpenAI

        """
        # Convert RST to clean MDC content using PandocConverter
        content = self._extract_main_content(rst_content)
        return _USER_PROMPT.format(content=content[:4000])

    def _extract_main_content(self, rst_content: str) -> str:
        """
        Extract main content from RST by converting to MDC and stripping metadata.

        Args:
            rst_content: The full RST content

        Returns:
            Cleaned content for summarization

        """
        # First check if the content is only comments/metadata
        lines = rst_content.split("\n")
        has_real_content = False

        for line in lines:
            line_stripped = line.strip()
            if (
                line_stripped
                and not line_stripped.startswith("..")
                and not line_stripped.startswith("#")
                and not line_stripped.startswith("---")
            ):
                has_real_content = True
                break

        # If no real content, return empty string
        if not has_real_content:
            return ""

        try:
            converter = PandocConverter()
            # Convert RST to MDC content
            return converter.convert_rst_to_md(rst_content)
        except Exception:  # noqa: BLE001
            # Fallback to simple extraction if conversion fails
            lines = rst_content.split("\n")
            content_lines = []

            for line in lines:
                # Skip comment lines and metadata
                if (
                    line.strip().startswith("..")
                    or line.strip().startswith("#")
                    or line.strip() == ""
                ):
                    continue

                content_lines.append(line)

            # If we only have comments, return empty string
            if not content_lines:
                return ""

            return "\n".join(content_lines)

    def _clean_summary(self, summary: str) -> str:
        """
        Clean and format the generated summary.

        Args:
            summary: Raw summary from OpenAI

        Returns:
            Cleaned and formatted summary

        """
        # Remove quotes if present
        summary = summary.strip("\"'")

        # Remove common prefixes
        prefixes_to_remove = [
            "This rule provides ",
            "This document provides ",
            "This guide provides ",
            "This file provides ",
            "Summary: ",
            "The summary: ",
        ]

        for prefix in prefixes_to_remove:
            if summary.startswith(prefix):
                summary = summary[len(prefix) :]
                break

        # Ensure proper sentence structure
        if not summary.endswith("."):
            summary += "."

        return summary

    def format_summary(self, summary: str) -> str:
        """
        Format summary for nice display.

        Args:
            summary: The summary text

        Returns:
            Formatted summary with RST directive in Sphinx comments

        """
        # Wrap text to 88 characters
        wrapped_lines = textwrap.wrap(
            summary, width=88, break_long_words=False, break_on_hyphens=False
        )

        formatted = "Summary:\n"
        formatted += "\n"

        for line in wrapped_lines:
            formatted += f"  {line}\n"

        formatted += "\n"

        return formatted
