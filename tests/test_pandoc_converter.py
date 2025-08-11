"""
Tests for the PandocConverter service.

Tests the enhanced RST to Markdown conversion using pandoc with custom post-processing.
"""

import pytest

from rstbuddy.services.pandoc_converter import PandocConverter


class TestPandocConverter:
    """Test cases for PandocConverter."""

    @pytest.fixture
    def converter(self):
        """Create a converter instance for testing."""
        return PandocConverter()

    def test_remove_sphinx_targets(self, converter):
        """Test removal of Sphinx target lines."""
        content = """.. _test_target:

# Test Document

.. _another_target:
## Section

Content here."""

        result = converter._preprocess_rst_content(content)  # noqa: SLF001

        # The preprocessing should remove the target lines
        assert ".. _test_target:" not in result
        assert ".. _another_target:" not in result

    def test_fix_code_blocks(self, converter):
        """Test fixing of malformed code blocks."""
        content = """# Test Document

```python
def test_function():
    return "test"

This code block is not properly closed.

```python
def another_function():
    return "another test"
```"""

        result = converter._fix_code_blocks(content)  # noqa: SLF001

        # Check that all code blocks are properly closed
        lines = result.split("\n")
        code_block_count = sum(1 for line in lines if line.startswith("```"))
        assert code_block_count % 2 == 0  # Should be even (pairs of opening/closing)

    def test_remove_empty_sections(self, converter):
        """Test removal of empty sections."""
        content = """# Main Title

## Empty Section

## Section with Content

This section has content.

## Another Empty Section

## Final Section

More content here."""

        result = converter._remove_empty_sections(content)  # noqa: SLF001

        # Check that empty sections are removed
        assert "Empty Section" not in result
        assert "Another Empty Section" not in result
        assert "Section with Content" in result
        assert "Final Section" in result

    def test_full_conversion(self, converter):
        """Test full conversion with comments before main title."""
        rst_content = """.. here's a comment
..
.. More comments

General Python Coding Standards
===============================

Packaging
---------

- Use ``uv`` for package management.
- The ``uv`` configuration is in ``pyproject.toml``.

.. code-block:: python

    def example_function():
        return "example"
"""

        result = converter.convert_rst_to_md(rst_content)

        # Comments should be removed
        assert "here's a comment" not in result
        assert "More comments" not in result
        # The main title should be converted by pandoc
        assert "## General Python Coding Standards" not in result
        assert "## Packaging" in result
        # Comments before main title should be removed
        assert "```" in result  # Code blocks
        assert "def example_function():" in result

    def test_full_conversion_with_empty_ai_instructions(self, converter):
        """Test full conversion when comments before main title are removed."""
        rst_content = """.. here's a comment
..
.. More comments

General Python Coding Standards
===============================

Packaging
---------

- Use ``uv`` for package management.
- The ``uv`` configuration is in ``pyproject.toml``.

.. code-block:: python

    def example_function():
        return "example"
"""

        result = converter.convert_rst_to_md(rst_content)

        # The main title should be converted by pandoc
        # Comments before main title should be removed
        assert "here's a comment" not in result
        assert "More comments" not in result
        assert "General Python Coding Standards" not in result
        assert "Packaging" in result
        assert "```" in result  # Code blocks
        assert "def example_function():" in result

    def test_pandoc_conversion(self, converter):
        """Test basic pandoc conversion."""
        rst_content = """Test Document
============

This is a test document.

## Section

Content here.

.. code-block:: python

    def test_function():
        return "test"
"""

        result = converter._convert_with_pandoc(rst_content)  # noqa: SLF001

        # Check that pandoc converted the content properly
        # Note: pandoc might not convert the title as expected, so we check for
        # the content
        assert "Test Document" in result
        assert "This is a test document" in result
        assert "```" in result
        assert "def test_function():" in result

    def test_format_markdown_with_mdformat_success(self, converter):
        """Test successful mdformat formatting."""
        content = """# Test Document

This is a test document.

1. First item
1. Second item
1. Third item

## Section

More content here."""

        result = converter._format_markdown_with_mdformat(content)  # noqa: SLF001

        # Check that mdformat applied consecutive numbering
        assert "1. First item" in result
        assert "2. Second item" in result
        assert "3. Third item" in result
        # Check that other content remains intact
        assert "# Test Document" in result
        assert "This is a test document" in result
        assert "## Section" in result
        assert "More content here" in result

    def test_format_markdown_with_mdformat_import_error(self, converter, monkeypatch):
        """Test mdformat formatting when mdformat is not available."""
        content = """# Test Document

1. First item
1. Second item"""

        # Mock import error
        def mock_import_error(*args, **kwargs):  # noqa: ARG001
            msg = "No module named 'mdformat'"
            raise ImportError(msg)

        monkeypatch.setattr("builtins.__import__", mock_import_error)

        result = converter._format_markdown_with_mdformat(content)  # noqa: SLF001

        # Should return content as-is when mdformat is not available
        assert result == content

    def test_format_markdown_with_mdformat_exception(self, converter, monkeypatch):
        """Test mdformat formatting when formatting fails."""
        content = """# Test Document

1. First item
1. Second item"""

        # Mock mdformat to raise an exception
        def mock_mdformat_text(*args, **kwargs):  # noqa: ARG001
            msg = "mdformat formatting failed"
            raise Exception(msg)  # noqa: TRY002

        monkeypatch.setattr("mdformat.text", mock_mdformat_text)

        result = converter._format_markdown_with_mdformat(content)  # noqa: SLF001

        # Should return content as-is when formatting fails
        assert result == content

    def test_full_conversion_includes_mdformat(self, converter, monkeypatch):
        """Test that full conversion includes mdformat formatting."""

        # Mock pandoc conversion
        def mock_convert_with_pandoc(content):  # noqa: ARG001
            return "# Test Document\n\n1. First item\n1. Second item"

        monkeypatch.setattr(converter, "_convert_with_pandoc", mock_convert_with_pandoc)

        # Mock post-processing
        def mock_postprocess(content):
            return content

        monkeypatch.setattr(
            converter, "_postprocess_markdown_content", mock_postprocess
        )

        # Mock mdformat to track if it was called
        mdformat_called = False

        def mock_mdformat_text(content, options=None):  # noqa: ARG001
            nonlocal mdformat_called
            mdformat_called = True
            # Apply consecutive numbering
            return content.replace("1. First item", "1. First item").replace(
                "1. Second item", "2. Second item"
            )

        monkeypatch.setattr("mdformat.text", mock_mdformat_text)

        rst_content = "Test Document\n===========\n\n1. First item\n1. Second item"
        result = converter.convert_rst_to_md(rst_content)

        # Check that mdformat was called
        assert mdformat_called
        # Check that consecutive numbering was applied
        assert "1. First item" in result
        assert "2. Second item" in result
