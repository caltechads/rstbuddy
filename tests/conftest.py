"""
Test configuration and fixtures for the ai-coding project.

This file contains shared fixtures and configuration that can be used across
all test files in the project.
"""

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)
