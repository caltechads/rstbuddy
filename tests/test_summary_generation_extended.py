"""Extended tests for SummaryGenerationService to improve coverage."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from openai import AuthenticationError, RateLimitError

from rstbuddy.exc import ConfigurationError, FileError
from rstbuddy.services.summary_generation import SummaryGenerationService


class TestSummaryGenerationServiceExtended:
    """Extended tests for SummaryGenerationService to cover missing lines."""

    def test_create_summary_prompt_with_content_truncation(self):
        """Test _create_summary_prompt truncates content to 4000 characters."""
        # Create a mock settings object
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-key"

        service = SummaryGenerationService(mock_settings)

        # Create content longer than 4000 characters
        long_content = "x" * 5000

        # Mock _extract_main_content to return our long content
        with patch.object(service, "_extract_main_content", return_value=long_content):
            prompt = service._create_summary_prompt("dummy content")  # noqa: SLF001

            # Should truncate content to 4000 characters
            assert "x" * 4000 in prompt
            assert "x" * 4001 not in prompt

    def test_create_summary_prompt_with_short_content(self):
        """Test _create_summary_prompt handles content shorter than 4000 characters."""
        # Create a mock settings object
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-key"

        service = SummaryGenerationService(mock_settings)

        # Create content shorter than 4000 characters
        short_content = "Short content here"

        # Mock _extract_main_content to return our short content
        with patch.object(service, "_extract_main_content", return_value=short_content):
            prompt = service._create_summary_prompt("dummy content")  # noqa: SLF001

            # Should include the full content
            assert short_content in prompt

    def test_extract_main_content_with_only_comments(self):
        """
        Test _extract_main_content returns empty string for content with only comments.
        """
        # Create a mock settings object
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-key"

        service = SummaryGenerationService(mock_settings)

        # Content with only comments and metadata that fallback logic will recognize
        comment_only_content = """.. comment: This is a comment
# This is also a comment
.. directive: value
"""

        # Mock PandocConverter to raise an exception to force fallback
        with patch(
            "rstbuddy.services.summary_generation.PandocConverter"
        ) as mock_converter_class:
            mock_converter = Mock()
            mock_converter.convert_rst_to_md.side_effect = Exception("Pandoc failed")
            mock_converter_class.return_value = mock_converter

            result = service._extract_main_content(comment_only_content)  # noqa: SLF001

            # Should return empty string for comment-only content when using fallback
            assert result == ""

    def test_extract_main_content_with_mixed_content(self):
        """Test _extract_main_content identifies real content mixed with comments."""
        # Create a mock settings object
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-key"

        service = SummaryGenerationService(mock_settings)

        # Content with comments and real content
        mixed_content = """.. comment: This is a comment
# Another comment

Real content here
More real content

.. directive: value
"""

        result = service._extract_main_content(mixed_content)  # noqa: SLF001

        # Should identify that there is real content
        assert result != ""

    def test_extract_main_content_with_pandoc_failure_fallback(self):
        """
        Test _extract_main_content falls back to simple extraction when
        Pandoc fails.
        """
        # Create a mock settings object
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-key"

        service = SummaryGenerationService(mock_settings)

        # Content with real content
        content = """.. comment: This is a comment
Real content here
More real content
.. directive: value
"""

        # Mock PandocConverter to raise an exception
        with patch(
            "rstbuddy.services.summary_generation.PandocConverter"
        ) as mock_converter_class:
            mock_converter = Mock()
            mock_converter.convert_rst_to_md.side_effect = Exception("Pandoc failed")
            mock_converter_class.return_value = mock_converter

            result = service._extract_main_content(content)  # noqa: SLF001

            # Should fall back to simple extraction
            assert "Real content here" in result
            assert "More real content" in result
            assert ".. comment: This is a comment" not in result
            assert ".. directive: value" not in result

    def test_extract_main_content_with_pandoc_failure_only_comments(self):
        """
        Test _extract_main_content fallback returns empty string when only
        comments exist.
        """
        # Create a mock settings object
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-key"

        service = SummaryGenerationService(mock_settings)

        # Content with only comments
        comment_only_content = """.. comment: This is a comment
# Another comment
.. directive: value
"""

        # Mock PandocConverter to raise an exception
        with patch(
            "rstbuddy.services.summary_generation.PandocConverter"
        ) as mock_converter_class:
            mock_converter = Mock()
            mock_converter.convert_rst_to_md.side_effect = Exception("Pandoc failed")
            mock_converter_class.return_value = mock_converter

            result = service._extract_main_content(comment_only_content)  # noqa: SLF001

            # Should return empty string when fallback finds only comments
            assert result == ""

    def test_extract_main_content_with_pandoc_failure_mixed_content(self):
        """Test _extract_main_content fallback handles mixed content correctly."""
        # Create a mock settings object
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-key"

        service = SummaryGenerationService(mock_settings)

        # Content with comments, real content, and empty lines
        mixed_content = """.. comment: This is a comment

Real content here

# Another comment
More real content

.. directive: value
"""

        # Mock PandocConverter to raise an exception
        with patch(
            "rstbuddy.services.summary_generation.PandocConverter"
        ) as mock_converter_class:
            mock_converter = Mock()
            mock_converter.convert_rst_to_md.side_effect = Exception("Pandoc failed")
            mock_converter_class.return_value = mock_converter

            result = service._extract_main_content(mixed_content)  # noqa: SLF001

            # Should extract real content and handle empty lines
            assert "Real content here" in result
            assert "More real content" in result
            assert ".. comment: This is a comment" not in result
            assert ".. directive: value" not in result
            assert "# Another comment" not in result

    def test_extract_main_content_with_pandoc_failure_content_only(self):
        """Test _extract_main_content fallback returns content when Pandoc fails."""
        # Create a mock settings object
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-key"

        service = SummaryGenerationService(mock_settings)

        # Content with only real content (no comments)
        content_only = """Real content here
More real content
Even more content
"""

        # Mock PandocConverter to raise an exception
        with patch(
            "rstbuddy.services.summary_generation.PandocConverter"
        ) as mock_converter_class:
            mock_converter = Mock()
            mock_converter.convert_rst_to_md.side_effect = Exception("Pandoc failed")
            mock_converter_class.return_value = mock_converter

            result = service._extract_main_content(content_only)  # noqa: SLF001

            # Should return all content lines joined together
            assert "Real content here" in result
            assert "More real content" in result
            assert "Even more content" in result
            # Should be joined with newlines
            assert "\n" in result

    def test_generate_summary_with_authentication_error(self):
        """Test generate_summary handles OpenAI authentication errors."""
        # Create a mock settings object
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-key"

        service = SummaryGenerationService(mock_settings)

        # Mock _create_summary_prompt
        with patch.object(  # noqa: SIM117
            service, "_create_summary_prompt", return_value="test prompt"
        ):
            # Mock OpenAI client to raise authentication error
            with patch(
                "rstbuddy.services.summary_generation.OpenAI"
            ) as mock_openai_class:
                mock_client = Mock()
                mock_client.chat.completions.create.side_effect = AuthenticationError(
                    "Invalid API key", response=Mock(), body=None
                )
                mock_openai_class.return_value = mock_client

                # Should raise ConfigurationError for authentication issues
                with pytest.raises(ConfigurationError) as exc_info:
                    service.generate_summary("test content")

                assert "Invalid OpenAI API key" in str(exc_info.value)

    def test_generate_summary_with_rate_limit_error(self):
        """Test generate_summary handles OpenAI rate limit errors."""
        # Create a mock settings object
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-key"

        service = SummaryGenerationService(mock_settings)

        # Mock _create_summary_prompt
        with patch.object(  # noqa: SIM117
            service, "_create_summary_prompt", return_value="test prompt"
        ):
            # Mock OpenAI client to raise rate limit error
            with patch(
                "rstbuddy.services.summary_generation.OpenAI"
            ) as mock_openai_class:
                mock_client = Mock()
                mock_client.chat.completions.create.side_effect = RateLimitError(
                    "Rate limit exceeded", response=Mock(), body=None
                )
                mock_openai_class.return_value = mock_client

                # Should raise FileError for rate limit issues
                with pytest.raises(FileError) as exc_info:
                    service.generate_summary("test content")

                assert "rate limit exceeded" in str(exc_info.value).lower()

    def test_generate_summary_with_generic_openai_error(self):
        """Test generate_summary handles generic OpenAI errors."""
        # Create a mock settings object
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-key"

        service = SummaryGenerationService(mock_settings)

        # Mock _create_summary_prompt
        with patch.object(  # noqa: SIM117
            service, "_create_summary_prompt", return_value="test prompt"
        ):
            # Mock OpenAI client to raise generic error
            with patch(
                "rstbuddy.services.summary_generation.OpenAI"
            ) as mock_openai_class:
                mock_client = Mock()
                mock_client.chat.completions.create.side_effect = Exception(
                    "Generic OpenAI error"
                )
                mock_openai_class.return_value = mock_client

                # Should raise FileError for generic errors
                with pytest.raises(FileError) as exc_info:
                    service.generate_summary("test content")

                assert "OpenAI API error: Generic OpenAI error" in str(exc_info.value)

    def test_generate_summary_with_empty_response(self):
        """Test generate_summary handles empty OpenAI response."""
        # Create a mock settings object
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-key"

        service = SummaryGenerationService(mock_settings)

        # Mock _create_summary_prompt
        with patch.object(  # noqa: SIM117
            service, "_create_summary_prompt", return_value="test prompt"
        ):
            # Mock OpenAI client to return empty response
            with patch(
                "rstbuddy.services.summary_generation.OpenAI"
            ) as mock_openai_class:
                mock_client = Mock()
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = None  # Empty response
                mock_client.chat.completions.create.return_value = mock_response
                mock_openai_class.return_value = mock_client

                # Mock _clean_summary
                with patch.object(
                    service, "_clean_summary", return_value="Cleaned summary"
                ):
                    result = service.generate_summary("test content")

                    # Should handle empty response gracefully
                    assert result == "Cleaned summary"

    def test_generate_summary_with_whitespace_response(self):
        """Test generate_summary handles whitespace-only OpenAI response."""
        # Create a mock settings object
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-key"

        service = SummaryGenerationService(mock_settings)

        # Mock _create_summary_prompt
        with patch.object(  # noqa: SIM117
            service, "_create_summary_prompt", return_value="test prompt"
        ):
            # Mock OpenAI client to return whitespace-only response
            with patch(
                "rstbuddy.services.summary_generation.OpenAI"
            ) as mock_openai_class:
                mock_client = Mock()
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[
                    0
                ].message.content = "   \n  \t  "  # Whitespace only
                mock_client.chat.completions.create.return_value = mock_response
                mock_openai_class.return_value = mock_client

                # Mock _clean_summary
                with patch.object(
                    service, "_clean_summary", return_value="Cleaned summary"
                ):
                    result = service.generate_summary("test content")

                    # Should handle whitespace response gracefully
                    assert result == "Cleaned summary"

    def test_clean_summary_with_quotes(self):
        """Test _clean_summary removes quotes from summary."""
        # Create a mock settings object
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-key"

        service = SummaryGenerationService(mock_settings)

        # Test with quotes
        result = service._clean_summary('"This is a quoted summary"')  # noqa: SLF001
        assert result == "This is a quoted summary."

        # Test with single quotes
        result = service._clean_summary("'Another quoted summary'")  # noqa: SLF001
        assert result == "Another quoted summary."

    def test_clean_summary_with_prefixes(self):
        """Test _clean_summary removes common prefixes."""
        # Create a mock settings object
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-key"

        service = SummaryGenerationService(mock_settings)

        # Test with various prefixes
        prefixes = [
            "This rule provides ",
            "This document provides ",
            "This guide provides ",
            "This file provides ",
            "Summary: ",
            "The summary: ",
        ]

        for prefix in prefixes:
            test_summary = prefix + "actual content"
            result = service._clean_summary(test_summary)  # noqa: SLF001
            assert result == "actual content."

    def test_clean_summary_without_prefixes(self):
        """Test _clean_summary doesn't modify summaries without prefixes."""
        # Create a mock settings object
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-key"

        service = SummaryGenerationService(mock_settings)

        # Test without prefixes
        test_summary = "This is a normal summary"
        result = service._clean_summary(test_summary)  # noqa: SLF001
        assert result == "This is a normal summary."

    def test_clean_summary_adds_period(self):
        """Test _clean_summary adds period if missing."""
        # Create a mock settings object
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-key"

        service = SummaryGenerationService(mock_settings)

        # Test without period
        test_summary = "This summary has no period"
        result = service._clean_summary(test_summary)  # noqa: SLF001
        assert result == "This summary has no period."

        # Test with period
        test_summary = "This summary has a period."
        result = service._clean_summary(test_summary)  # noqa: SLF001
        assert result == "This summary has a period."

    def test_format_summary_wraps_text(self):
        """Test format_summary wraps text to 88 characters."""
        # Create a mock settings object
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-key"

        service = SummaryGenerationService(mock_settings)

        # Create a long summary that should be wrapped
        long_summary = "This is a very long summary that should be wrapped to multiple lines because it exceeds the 88 character limit that is set for formatting purposes."  # noqa: E501

        result = service.format_summary(long_summary)

        # Should contain the summary directive
        assert "Summary:" in result

        # Should wrap text (multiple lines)
        lines = result.strip().split("\n")
        assert len(lines) > 3  # Header + content + footer  # noqa: PLR2004

        # Check that no line exceeds 88 characters (plus 2 spaces for indentation)
        for line in lines:
            if line.strip() and not line.startswith("Summary:"):
                assert len(line) <= 90  # 88 + 2 spaces  # noqa: PLR2004

    def test_format_summary_with_short_text(self):
        """Test format_summary handles short text correctly."""
        # Create a mock settings object
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-key"

        service = SummaryGenerationService(mock_settings)

        # Create a short summary
        short_summary = "Short summary"

        result = service.format_summary(short_summary)

        # Should contain the summary directive
        assert "Summary:" in result

        # Should have proper formatting
        lines = result.strip().split("\n")
        # Filter out empty lines for accurate counting
        non_empty_lines = [line for line in lines if line.strip()]
        assert len(non_empty_lines) == 2  # Header + content  # noqa: PLR2004

        # Check that the content line is properly indented
        content_lines = [
            line for line in lines if line.strip() and not line.startswith("Summary:")
        ]
        assert len(content_lines) == 1
        assert content_lines[0] == "  Short summary"
