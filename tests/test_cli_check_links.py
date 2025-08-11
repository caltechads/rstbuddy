from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

from click.testing import CliRunner

from rstbuddy.cli.cli import cli

if TYPE_CHECKING:
    from pathlib import Path


def write(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")


def test_check_links_reports_broken_external_and_ref_and_doc(tmp_path: Path):
    src = tmp_path / "doc" / "source"
    tmpl = tmp_path / "doc" / "templates"

    # Define a label in one file
    file_with_label = src / "a.rst"
    write(
        file_with_label,
        """
.. _good-label:

Section
=======

Content here.
""".lstrip(),
    )

    # A file that includes various links
    file_check = src / "b.rst"
    write(
        file_check,
        """
Title
=====

External: https://example.invalid.domain.tld/this-should-fail

Ref good: :ref:`good-label`
Ref bad: :ref:`missing-label`

Doc abs bad: :doc:`/nonexistent/path`
Doc rel bad: :doc:`missing-doc`

.. note:: This admonition contains a bad link https://definitely.invalid.tld/abc

.. code-block:: bash

   # This link should be ignored: https://ignore.me/in/code
""".lstrip(),
    )

    # Create a template file to ensure scanning outside doc/source
    write(tmpl / "migration.rst", "Template with :ref:`missing-label` too")

    runner = CliRunner()
    result = runner.invoke(
        cli, ["--output", "json", "check-links", str(tmp_path / "doc")]
    )

    assert result.exit_code != 0  # broken links found

    data = json.loads(result.output)
    # Expect entries for b.rst and templates/migration.rst
    keys = list(data.keys())
    assert any(k.endswith("b.rst") for k in keys)
    assert any("templates/migration.rst" in k for k in keys)

    # Ensure that the code-block link is not present, but admonition one is
    for items in data.values():
        for item in items:
            assert "ignore.me" not in item["link"]


def test_check_links_text_output(tmp_path: Path):
    """Test check-links with text output format."""
    src = tmp_path / "doc" / "source"

    # Create a file with broken links
    file_with_broken_links = src / "broken.rst"
    write(
        file_with_broken_links,
        """
Title
=====

Bad link: https://definitely.invalid.tld/abc
Missing ref: :ref:`missing-label`
""".lstrip(),
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--output", "text", "check-links", str(tmp_path / "doc")],
        catch_exceptions=False,
    )

    # Should exit with 1 when broken links are found
    assert result.exit_code == 1
    # The output should contain the table before the SystemExit
    assert "Broken RST Links" in result.output


def test_check_links_table_output(tmp_path: Path):
    """Test check-links with table output format (default)."""
    src = tmp_path / "doc" / "source"

    # Create a file with broken links
    file_with_broken_links = src / "broken.rst"
    write(
        file_with_broken_links,
        """
Title
=====

Bad link: https://definitely.invalid.tld/abc
Missing ref: :ref:`missing-label`
""".lstrip(),
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["check-links", str(tmp_path / "doc")],  # No --output flag, defaults to table
        catch_exceptions=False,
    )

    # Should exit with 1 when broken links are found
    assert result.exit_code == 1
    # The output should contain the table before the SystemExit
    assert "Broken RST Links" in result.output


def test_check_links_table_output_explicit(tmp_path: Path):
    """Test check-links with explicit table output format."""
    src = tmp_path / "doc" / "source"

    # Create a file with broken links
    file_with_broken_links = src / "broken.rst"
    write(
        file_with_broken_links,
        """
Title
=====

Bad link: https://definitely.invalid.tld/abc
Missing ref: :ref:`missing-label`
""".lstrip(),
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--output", "table", "check-links", str(tmp_path / "doc")],
        catch_exceptions=False,
    )

    # Should exit with 1 when broken links are found
    assert result.exit_code == 1
    # The output should contain the table before the SystemExit
    assert "Broken RST Links" in result.output


def test_check_links_no_broken_links(tmp_path: Path):
    """Test check-links when no broken links are found."""
    src = tmp_path / "doc" / "source"

    # Create a file with only valid content
    file_with_valid_content = src / "valid.rst"
    write(
        file_with_valid_content,
        """
Title
=====

Valid content here.
""".lstrip(),
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["check-links", str(tmp_path / "doc")])

    # Should exit with 0 when no broken links
    assert result.exit_code == 0
    # When no broken links, it shows an empty table
    assert "Broken RST Links" in result.output
    assert "File" in result.output
    assert "Line" in result.output
    assert "Link" in result.output


def test_check_links_with_custom_options(tmp_path: Path):
    """Test check-links with custom timeout, max-workers, and user-agent options."""
    src = tmp_path / "doc" / "source"

    # Create a file with broken links
    file_with_broken_links = src / "broken.rst"
    write(
        file_with_broken_links,
        """
Title
=====

Bad link: https://definitely.invalid.tld/abc
""".lstrip(),
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--output",
            "json",
            "check-links",
            "--timeout",
            "10",
            "--max-workers",
            "4",
            "--user-agent",
            "custom-agent/1.0",
            "--no-check-robots",
            str(tmp_path / "doc"),
        ],
    )

    assert result.exit_code != 0  # broken links found

    # Check that JSON output is generated
    data = json.loads(result.output)
    assert data


def test_check_links_default_root_path(tmp_path: Path):
    """Test check-links with default root path (doc directory)."""
    src = tmp_path / "doc" / "source"

    # Create a file with broken links
    file_with_broken_links = src / "broken.rst"
    write(
        file_with_broken_links,
        """
Title
=====

Bad link: https://definitely.invalid.tld/abc
""".lstrip(),
    )

    # Change to tmp_path so the default "doc" directory exists

    original_cwd = os.getcwd()  # noqa: PTH109
    os.chdir(tmp_path)

    try:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--output", "json", "check-links"],  # No root argument
        )

        assert result.exit_code != 0  # broken links found

        # Check that JSON output is generated
        data = json.loads(result.output)
        assert data
    finally:
        os.chdir(original_cwd)


def test_check_links_with_new_directives(tmp_path: Path):
    """Test check-links with new directive types."""
    src = tmp_path / "doc" / "source"

    # Create a file with broken links in new directives
    file_with_broken_links = src / "directives.rst"
    write(
        file_with_broken_links,
        """
Title
=====

.. literalinclude:: https://definitely.invalid.tld/sample.py

.. image:: https://definitely.invalid.tld/image.png

.. figure:: https://definitely.invalid.tld/figure.png

.. thumbnail:: https://definitely.invalid.tld/thumb.png

.. literalinclude:: nonexistent/local/file.py

.. image:: missing/image.png
""".lstrip(),
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--output", "json", "check-links", str(tmp_path / "doc")],
        catch_exceptions=False,
    )

    # Should exit with 1 when broken links are found
    assert result.exit_code == 1

    # Parse JSON output
    data = json.loads(result.output)

    # Should find broken links from all new directives
    assert any(k.endswith("directives.rst") for k in data)

    # Check that all expected broken links are found
    directives_file_data = None
    for key, value in data.items():
        if key.endswith("directives.rst"):
            directives_file_data = value
            break

    assert directives_file_data is not None
    # 6 directives with broken links
    assert len(directives_file_data) == 6  # noqa: PLR2004

    # Verify all expected URLs and local paths are present
    links = [item["link"] for item in directives_file_data]
    assert "https://definitely.invalid.tld/sample.py" in links
    assert "https://definitely.invalid.tld/image.png" in links
    assert "https://definitely.invalid.tld/figure.png" in links
    assert "https://definitely.invalid.tld/thumb.png" in links
    assert "nonexistent/local/file.py" in links
    assert "missing/image.png" in links
