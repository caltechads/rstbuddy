"""
Unit tests for summary generation service.

Tests the SummaryGenerationService functionality including OpenAI API integration,
RST file parsing, and summary formatting.
"""

from unittest.mock import Mock, patch

import pytest

from rstbuddy.exc import ConfigurationError, FileError
from rstbuddy.services.summary_generation import SummaryGenerationService
from rstbuddy.settings import Settings


class TestSummaryGenerationService:
    """Test cases for SummaryGenerationService."""

    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings(openai_api_key="test-key")

    @pytest.fixture
    def service(self, settings):
        """Create SummaryGenerationService instance."""
        return SummaryGenerationService(settings)

    @pytest.fixture
    def sample_rst_content(self):
        """Sample RST content for testing."""
        return """Python Testing Guide
===================

This guide covers how to write tests for a Python project.

## Test Categories

The test suite includes several categories:

- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test with real projects
- **CLI tests**: Test command-line interface functionality

## Test Naming Conventions

- Test files should be in the `tests/` directory
- Test files: `test_<module>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<description>`
"""

    def test_init_with_api_key(self, settings):
        """Test service initialization with API key."""
        service = SummaryGenerationService(settings)
        assert service.settings.openai_api_key == "test-key"

    def test_init_without_api_key(self):
        """Test service initialization without API key."""
        settings = Settings(openai_api_key="")
        service = SummaryGenerationService(settings)
        assert service.settings.openai_api_key == ""

    def test_generate_summary_success(self, service, sample_rst_content):
        """Test successful summary generation."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[
            0
        ].message.content = (
            "This guide provides comprehensive testing guidelines for Python projects."
        )

        with patch("rstbuddy.services.summary_generation.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            summary = service.generate_summary(sample_rst_content)

            assert "testing guidelines" in summary.lower()
            mock_client.chat.completions.create.assert_called_once()

    def test_generate_summary_no_api_key(self, sample_rst_content):
        """Test summary generation without API key raises error."""
        settings = Settings(openai_api_key="")
        service = SummaryGenerationService(settings)

        with pytest.raises(ConfigurationError, match="OpenAI API key is required"):
            service.generate_summary(sample_rst_content)

    def test_generate_summary_api_error(self, service, sample_rst_content):
        """Test summary generation with API error."""
        with patch("rstbuddy.services.summary_generation.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_openai.return_value = mock_client

            with pytest.raises(FileError, match="OpenAI API error"):
                service.generate_summary(sample_rst_content)

    def test_generate_summary_authentication_error(self, service, sample_rst_content):
        """Test summary generation with authentication error."""
        with patch("rstbuddy.services.summary_generation.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception(
                "authentication failed"
            )
            mock_openai.return_value = mock_client

            with pytest.raises(ConfigurationError, match="Invalid OpenAI API key"):
                service.generate_summary(sample_rst_content)

    def test_extract_main_content(self, service, sample_rst_content):
        """Test main content extraction from RST."""
        content = service._extract_main_content(sample_rst_content)  # noqa: SLF001

        assert "Python Testing Guide" in content
        assert "The test suite includes several categories" in content

    def test_clean_summary(self, service):
        """Test summary cleaning and formatting."""
        # Test removing quotes
        summary = service._clean_summary('"This is a test summary."')  # noqa: SLF001
        assert summary == "This is a test summary."

        # Test removing common prefixes
        summary = service._clean_summary(  # noqa: SLF001
            "This rule provides comprehensive testing guidelines."
        )
        assert summary == "comprehensive testing guidelines."

        # Test adding period
        summary = service._clean_summary("This is a test summary")  # noqa: SLF001
        assert summary == "This is a test summary."

    def test_format_summary(self, service):
        """Test RST directive formatting."""
        summary = "This is a test summary that should be formatted as an RST directive with proper indentation and wrapping."  # noqa: E501
        formatted = service.format_summary(summary)

        assert "Summary:" in formatted
        assert (
            "  This is a test summary that should be formatted as an RST" in formatted
        )
        assert "  indentation and wrapping." in formatted

    def test_create_summary_prompt(self, service, sample_rst_content):
        """Test prompt creation for OpenAI API."""
        prompt = service._create_summary_prompt(sample_rst_content)  # noqa: SLF001

        assert "Python Testing Guide" in prompt
        assert "The test suite includes several categories" in prompt
        assert "10 sentences maximum" in prompt

    def test_create_summary_prompt_no_rule_name(self, service, sample_rst_content):
        """Test prompt creation without rule name."""
        prompt = service._create_summary_prompt(sample_rst_content)  # noqa: SLF001

        assert "Python Testing Guide" in prompt

    def test_create_summary_prompt_content_limit(self, service):
        """Test prompt creation with content length limit."""
        long_content = "A" * 3000  # Very long content
        prompt = service._create_summary_prompt(long_content)  # noqa: SLF001

        # Should limit content length
        assert len(prompt) < 5000  # Reasonable limit  # noqa: PLR2004

    def test_extract_main_content_empty(self, service):
        """Test main content extraction from empty content."""
        content = service._extract_main_content("")  # noqa: SLF001
        assert content == ""

    def test_extract_main_content_only_comments(self, service):
        """Test main content extraction from content with only comments."""
        content = service._extract_main_content(".. comment\n# another comment\n---\n")  # noqa: SLF001
        assert content == ""

    def test_format_summary_empty(self, service):
        """Test RST formatting with empty summary."""
        formatted = service.format_summary("")
        assert formatted.count("\n") >= 2  # noqa: PLR2004

    def test_format_summary_long_word(self, service):
        """Test RST formatting with very long word."""
        long_word = "A" * 100
        formatted = service.format_summary(f"This is a test with {long_word} word.")

        assert (
            len(formatted.split("\n")[3]) <= 104  # noqa: PLR2004
        )  # 100 + 4 spaces for very long words
