"""
Tests for the gather-links CLI command.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from rstbuddy.cli.cli import cli
from rstbuddy.services.gather_links import RSTLinkGatherer


@pytest.fixture
def sample_rst_files(temp_dir):
    """Create sample RST files with various link patterns for testing."""
    # File 1: Simple external links
    file1 = temp_dir / "file1.rst"
    file1.write_text(
        """Title
=====

This is a sample file with external links.

See the GitHub <https://github.com>_ for more information.
Also check out the Python docs <https://docs.python.org>`_.

More links: `Stack Overflow <https://stackoverflow.com>`_.
""",
        encoding="utf-8",
    )

    # File 2: Links with labels
    file2 = temp_dir / "file2.rst"
    file2.write_text(
        """Another Title
============

This file has labeled links.

Check the `Django documentation <https://docs.djangoproject.com>`_.
And the `Flask docs <https://flask.palletsprojects.com>`_.
""",
        encoding="utf-8",
    )

    # File 3: References section (should be skipped)
    file3 = temp_dir / "file3.rst"
    file3.write_text(
        """References
==========

Here are some references:

- `Paper 1 <https://arxiv.org/abs/1234.5678>`_
- `Paper 2 <https://doi.org/10.1234/example`_
""",
        encoding="utf-8",
    )

    # File 4: Mixed content
    file4 = temp_dir / "subdir" / "file4.rst"
    file4.parent.mkdir()
    file4.write_text(
        """Subdirectory File
================

This file is in a subdirectory.

Visit `PyPI <https://pypi.org>`_ for packages.
Check `Read the Docs <https://readthedocs.org>`_ for documentation.
""",
        encoding="utf-8",
    )

    return temp_dir


@pytest.fixture
def mock_settings():
    """Create a mock settings object."""
    mock = Mock()
    mock.documentation_dir = "doc/source"
    return mock


class TestRSTLinkGatherer:
    """Test the RSTLinkGatherer service class."""

    def test_init(self, temp_dir):
        """Test RSTLinkGatherer initialization."""
        gatherer = RSTLinkGatherer(temp_dir)
        assert gatherer.documentation_dir == temp_dir
        assert gatherer.links_file == temp_dir / "_links.rst"
        assert len(gatherer.links) == 0
        assert len(gatherer.labels) == 0

    def test_is_valid_external_url(self, temp_dir):
        """Test URL validation."""
        gatherer = RSTLinkGatherer(temp_dir)

        # Valid URLs
        assert gatherer._is_valid_external_url("https://example.com")
        assert gatherer._is_valid_external_url("http://github.com/user/repo")
        assert gatherer._is_valid_external_url("https://www.python.org/docs/")

        # Invalid URLs
        assert not gatherer._is_valid_external_url("not-a-url")
        assert not gatherer._is_valid_external_url("#section")
        assert not gatherer._is_valid_external_url("ftp://example.com")
        assert not gatherer._is_valid_external_url("")

    def test_generate_label_domain_only(self, temp_dir):
        """Test label generation for domain-only URLs."""
        gatherer = RSTLinkGatherer(temp_dir)

        # Test basic domain
        label = gatherer._generate_label("https://github.com")
        assert label == "GithubCom"

        # Test with www prefix
        label = gatherer._generate_label("https://www.python.org")
        assert label == "PythonOrg"

        # Test with trailing slash
        label = gatherer._generate_label("https://docs.python.org/")
        assert label == "DocsPythonOrg"

    def test_generate_label_with_path(self, temp_dir):
        """Test label generation for URLs with paths."""
        gatherer = RSTLinkGatherer(temp_dir)

        # Test with simple path
        label = gatherer._generate_label("https://github.com/user/repo")
        assert label == "GithubComRepo"

        # Test with .html extension
        label = gatherer._generate_label("https://example.com/page.html")
        assert label == "ExampleComPage"

        # Test with complex path
        label = gatherer._generate_label("https://docs.python.org/3/library/os.html")
        assert label == "DocsPythonOrgOs"

    def test_generate_label_uniqueness(self, temp_dir):
        """Test that generated labels are unique."""
        gatherer = RSTLinkGatherer(temp_dir)

        # Add first link
        gatherer._add_link("https://github.com/user1/repo1", None)
        assert "GithubComRepo1" in gatherer.labels

        # Add second link with same label but different URL
        gatherer._add_link("https://github.com/user2/repo2", None)
        assert "GithubComRepo2" in gatherer.labels

        # Verify they're different
        assert gatherer.labels["GithubComRepo1"] != gatherer.labels["GithubComRepo2"]

    def test_is_in_references_section(self, temp_dir):
        """Test References section detection."""
        gatherer = RSTLinkGatherer(temp_dir)

        # Test with References section
        content = """References
==========

Some content here."""
        assert gatherer._is_in_references_section(content)

        # Test with lowercase references
        content = """references
==========

Some content here."""
        assert gatherer._is_in_references_section(content)

        # Test with mixed case
        content = """Further References
==================

Some content here."""
        assert gatherer._is_in_references_section(content)

        # Test without References section
        content = """Introduction
============

Some content here."""
        assert not gatherer._is_in_references_section(content)

    def test_extract_links(self, temp_dir):
        """Test link extraction from RST content."""
        gatherer = RSTLinkGatherer(temp_dir)

        content = """Title
=====

Link 1: <https://example.com>_
Link 2: Label <https://github.com>_
Link 3: <https://python.org>_
"""

        # Extract links
        links_found = gatherer._extract_links(content, False)

        assert links_found
        assert len(gatherer.links) == 3
        assert "https://example.com" in gatherer.links
        assert "https://github.com" in gatherer.links
        assert "https://python.org" in gatherer.links

    def test_extract_links_skip_references(self, temp_dir):
        """Test that links in References sections are skipped."""
        gatherer = RSTLinkGatherer(temp_dir)

        content = """References
==========

Link: <https://example.com>_
"""

        # Extract links (should be skipped)
        links_found = gatherer._extract_links(content, True)

        assert not links_found
        assert len(gatherer.links) == 0

    def test_create_links_file(self, temp_dir):
        """Test _links.rst file creation."""
        gatherer = RSTLinkGatherer(temp_dir)

        # Add some test links
        gatherer._add_link("https://github.com", "Github")
        gatherer._add_link("https://python.org", "Python")

        # Create links file
        gatherer.create_links_file()

        # Check file was created
        assert gatherer.links_file.exists()

        # Check content
        content = gatherer.links_file.read_text(encoding="utf-8")
        assert ".. _Github: https://github.com" in content
        assert ".. _Python: https://python.org" in content

    def test_create_links_file_dry_run(self, temp_dir, capsys):
        """Test _links.rst file creation in dry-run mode."""
        gatherer = RSTLinkGatherer(temp_dir)

        # Add some test links
        gatherer._add_link("https://github.com", "Github")

        # Create links file (dry run)
        gatherer.create_links_file(dry_run=True)

        # Check file was NOT created
        assert not gatherer.links_file.exists()

        # Check output
        captured = capsys.readouterr()
        assert "Would create/update" in captured.out

    def test_backup_files(self, temp_dir):
        """Test file backup functionality."""
        gatherer = RSTLinkGatherer(temp_dir)

        # Create a test file
        test_file = temp_dir / "test.rst"
        test_file.write_text("Test content", encoding="utf-8")

        # Add to files to modify
        gatherer.files_to_modify.append(test_file)

        # Create backups
        success = gatherer.backup_files()

        assert success

        # Check backup was created
        backup_files = list(temp_dir.glob("*.bak"))
        assert len(backup_files) == 1

        # Check backup content
        backup_content = backup_files[0].read_text(encoding="utf-8")
        assert backup_content == "Test content"

    def test_replace_links(self, temp_dir):
        """Test link replacement in files."""
        gatherer = RSTLinkGatherer(temp_dir)

        # Create a test file with links
        test_file = temp_dir / "test.rst"
        test_file.write_text(
            "Link: <https://github.com>_\nLabeled: GitHub <https://github.com>_",
            encoding="utf-8",
        )

        # Add link to gatherer
        gatherer._add_link("https://github.com", "Github")
        gatherer.files_to_modify.append(test_file)

        # Replace links
        gatherer.replace_links()

        # Check content was updated
        content = test_file.read_text(encoding="utf-8")
        assert "Link: `Github`_" in content
        assert "Labeled: GitHub `Github`_" in content

    def test_update_conf_py(self, temp_dir):
        """Test conf.py update functionality."""
        gatherer = RSTLinkGatherer(temp_dir)

        # Create a test conf.py
        conf_py = temp_dir / "conf.py"
        conf_py.write_text(
            """extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
]

# Other settings
""",
            encoding="utf-8",
        )

        # Update conf.py
        success = gatherer.update_conf_py()

        assert success

        # Check content was updated
        content = conf_py.read_text(encoding="utf-8")
        assert "rst_epilog" in content
        assert 'with open("_links.rst"' in content

    def test_update_conf_py_already_exists(self, temp_dir):
        """Test conf.py update when rst_epilog already exists."""
        gatherer = RSTLinkGatherer(temp_dir)

        # Create a test conf.py with existing rst_epilog
        conf_py = temp_dir / "conf.py"
        conf_py.write_text(
            """extensions = ['sphinx.ext.autodoc']

rst_epilog = "existing content"
""",
            encoding="utf-8",
        )

        # Update conf.py
        success = gatherer.update_conf_py()

        assert success

        # Check content was not changed
        content = conf_py.read_text(encoding="utf-8")
        assert 'rst_epilog = "existing content"' in content

    def test_run_complete_process(self, sample_rst_files):
        """Test the complete run process."""
        gatherer = RSTLinkGatherer(sample_rst_files)

        # Run the process
        success = gatherer.run()

        assert success

        # Check that _links.rst was created
        assert gatherer.links_file.exists()

        # Check that files were modified
        assert len(gatherer.files_to_modify) > 0

        # Check that backups were created
        backup_files = list(sample_rst_files.rglob("*.bak"))
        assert len(backup_files) > 0

    def test_run_dry_run(self, sample_rst_files, capsys):
        """Test the complete run process in dry-run mode."""
        gatherer = RSTLinkGatherer(sample_rst_files)

        # Run the process (dry run)
        success = gatherer.run(dry_run=True)

        assert success

        # Check that _links.rst was NOT created
        assert not gatherer.links_file.exists()

        # Check output
        captured = capsys.readouterr()
        assert "Would create/update" in captured.out
        # In dry-run mode, backup message is not shown since no files are modified


class TestGatherLinksCLI:
    """Test the gather-links CLI command."""

    def test_gather_links_command_exists(self, runner):
        """Test that the gather-links command is available."""
        result = runner.invoke(cli, ["gather-links", "--help"])
        assert result.exit_code == 0
        assert "gather-links" in result.output

    def test_gather_links_dry_run(self, runner, sample_rst_files):
        """Test gather-links command with dry-run option."""
        result = runner.invoke(
            cli,
            ["gather-links", str(sample_rst_files), "--dry-run"],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.output
        assert "Dry run completed successfully" in result.output

    def test_gather_links_verbose(self, runner, sample_rst_files):
        """Test gather-links command with verbose option."""
        result = runner.invoke(
            cli,
            ["gather-links", str(sample_rst_files), "--verbose"],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "Using documentation directory:" in result.output
        assert "Link gathering completed successfully" in result.output

    def test_gather_links_default_directory(self, runner, temp_dir):
        """Test gather-links command using default documentation directory."""
        # Set environment variable to point to temp directory
        import os

        original_dir = os.environ.get("RSTBUDDY_DOCUMENTATION_DIR")
        os.environ["RSTBUDDY_DOCUMENTATION_DIR"] = str(temp_dir)

        try:
            # Create a sample RST file in the temp directory
            sample_file = temp_dir / "sample.rst"
            sample_file.write_text(
                "Test file with link: <https://example.com>_",
                encoding="utf-8",
            )

            # Run command without specifying directory (should use default)
            result = runner.invoke(
                cli,
                ["gather-links", "--dry-run"],
                catch_exceptions=False,
            )

            # Should succeed in dry-run mode
            assert result.exit_code == 0
            assert "DRY RUN MODE" in result.output

        finally:
            # Restore original environment
            if original_dir is not None:
                os.environ["RSTBUDDY_DOCUMENTATION_DIR"] = original_dir
            else:
                del os.environ["RSTBUDDY_DOCUMENTATION_DIR"]

    def test_gather_links_invalid_directory(self, runner):
        """Test gather-links command with invalid directory."""
        result = runner.invoke(
            cli,
            ["gather-links", "/nonexistent/directory"],
            catch_exceptions=False,
        )

        assert result.exit_code != 0
        assert "does not exist" in result.output

    def test_gather_links_file_not_directory(self, runner, temp_dir):
        """Test gather-links command with file instead of directory."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test", encoding="utf-8")

        result = runner.invoke(
            cli,
            ["gather-links", str(test_file)],
            catch_exceptions=False,
        )

        assert result.exit_code != 0
        assert "is a file" in result.output
