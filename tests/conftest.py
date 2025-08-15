"""
Test configuration and fixtures for the ai-coding project.

This file contains shared fixtures and configuration that can be used across
all test files in the project.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest
from click.testing import CliRunner
from rich.console import Console


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_console():
    """Create a mock console for testing."""
    return Mock(spec=Console)


@pytest.fixture
def mock_settings():
    """Create a mock settings object for testing."""
    mock = Mock()
    mock.model_dump.return_value = {
        "app_name": "rstbuddy",
        "app_version": "0.1.0",
        "documentation_dir": "doc/source",
        "openai_api_key": "test-key",
        "clean_rst_extra_protected_regexes": [],
        "check_rst_links_skip_domains": [],
        "check_rst_links_extra_skip_directives": [],
        "default_output_format": "table",
        "enable_colors": True,
        "quiet_mode": False,
        "log_level": "INFO",
        "log_file": None,
    }
    return mock


@pytest.fixture
def sample_rst_file(temp_dir):
    """Create a sample RST file for testing."""
    rst_file = temp_dir / "sample.rst"
    rst_file.write_text(
        """Title
=====

This is a sample RST file for testing.

.. _test-label:

Section
-------

Content here.

External link: https://example.com

.. code-block:: python

   def hello():
       print("Hello, World!")

.. note:: This is a note.

.. warning:: This is a warning.
""",
        encoding="utf-8",
    )
    return rst_file


@pytest.fixture
def broken_rst_file(temp_dir):
    """Create a broken RST file for testing."""
    rst_file = temp_dir / "broken.rst"
    rst_file.write_text(
        """Title
=====

This is a broken RST file.

.. _broken-label:

Section
-------

Content here.

.. _duplicate-label:

Another Section
--------------

More content.

.. _duplicate-label:

Duplicate label!
""",
        encoding="utf-8",
    )
    return rst_file


@pytest.fixture
def markdown_file(temp_dir):
    """Create a sample markdown file for testing."""
    md_file = temp_dir / "sample.md"
    md_file.write_text(
        """# Title

This is a sample markdown file for testing.

## Section

Content here.

[External link](https://example.com)

```python
def hello():
    print("Hello, World!")
```

> **Note:** This is a note.

> **Warning:** This is a warning.
""",
        encoding="utf-8",
    )
    return md_file


@pytest.fixture
def cli_context(mock_settings, mock_console):
    """Create a mock CLI context for testing."""
    return {
        "settings": mock_settings,
        "utils": Mock(),
        "console": mock_console,
        "output": "table",
    }


@pytest.fixture(autouse=True)
def reset_console_state():
    """Reset console state after each test to prevent test interference."""
    from rstbuddy.cli.utils import console, stderr_console

    # Store original state
    original_console_quiet = getattr(console, "quiet", False)
    original_stderr_console_quiet = getattr(stderr_console, "quiet", False)

    yield

    # Restore original state
    console.quiet = original_console_quiet
    stderr_console.quiet = original_stderr_console_quiet
