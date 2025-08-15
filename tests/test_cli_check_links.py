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
    src.mkdir(parents=True, exist_ok=True)
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
    src = tmp_path / "doc" / "doc" / "source"

    # Create a file with broken links
    file_with_broken_links = src / "broken.rst"
    src.mkdir(parents=True, exist_ok=True)
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
    src.mkdir(parents=True, exist_ok=True)
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


def test_check_links_custom_labels_valid(tmp_path: Path):
    """
    Test that custom label definitions with invalid URLs are reported as broken links.
    """
    src = tmp_path / "doc" / "source"

    # File with custom label definitions
    file_with_definitions = src / "definitions.rst"
    write(
        file_with_definitions,
        """
.. My Label: https://invalid.example.com/page1
.. Another Label: https://invalid.example.org/page2
.. Label with Spaces: https://invalid.test.com/page3
.. Label-With-Dashes: https://invalid.demo.net/page4
.. Label_With_Underscores: https://invalid.sample.io/page5

Content here.
""".lstrip(),
    )

    # File with valid custom label references
    file_with_references = src / "references.rst"
    write(
        file_with_references,
        """
Title
=====

Valid references:
- `My Label`_
- `Another Label`_
- `Label with Spaces`_
- `Label-With-Dashes`_
- `Label_With_Underscores`_

Content here.
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
            "5",
            "--max-workers",
            "10",
            str(tmp_path / "doc"),
        ],
    )

    # Should fail validation because the URLs in custom label definitions are invalid
    assert result.exit_code != 0

    # Parse the output to verify the broken links
    data = json.loads(result.output)

    # Should have entries for the invalid URLs
    invalid_urls_found = False
    for items in data.values():
        for item in items:
            if (
                "invalid.example.com" in item["link"]
                or "invalid.example.org" in item["link"]
            ):
                invalid_urls_found = True
                break
        if invalid_urls_found:
            break

    assert invalid_urls_found, (
        "Invalid URLs in custom label definitions should be reported as broken links"
    )


def test_check_links_custom_labels_missing(tmp_path: Path):
    """Test that missing custom label definitions are reported as broken links."""
    src = tmp_path / "doc" / "source"

    # File with custom label definitions (missing some)
    file_with_definitions = src / "definitions.rst"
    write(
        file_with_definitions,
        """
.. My Label: https://invalid.example.com/page1
.. Another Label: https://invalid.example.org/page2

Content here.
""".lstrip(),
    )

    # File with some missing custom label references
    file_with_references = src / "references.rst"
    write(
        file_with_references,
        """
Title
=====

Valid references:
- `My Label`_
- `Another Label`_

Missing references:
- `Missing Label`_
- `Another Missing Label`_

Content here.
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
            "5",
            "--max-workers",
            "1",
            str(tmp_path / "doc"),
        ],
    )

    # Should fail validation (broken links found)
    assert result.exit_code != 0

    data = json.loads(result.output)

    # Should have entries for the missing labels
    missing_labels_found = False
    for items in data.values():
        for item in items:
            if (
                "Missing Label" in item["link"]
                or "Another Missing Label" in item["link"]
            ):
                missing_labels_found = True
                break
        if missing_labels_found:
            break

    assert missing_labels_found, (
        "Missing custom labels should be reported as broken links"
    )


def test_check_links_custom_labels_case_sensitive(tmp_path: Path):
    """Test that custom label matching is case-sensitive."""
    src = tmp_path / "doc" / "source"

    # File with custom label definition (lowercase)
    file_with_definitions = src / "definitions.rst"
    write(
        file_with_definitions,
        """
.. my label: https://invalid.example.com/page1

Content here.
""".lstrip(),
    )

    # File with case-mismatched custom label reference (uppercase)
    file_with_references = src / "references.rst"
    write(
        file_with_references,
        """
Title
=====

Case-mismatched reference:
- `My Label`_

Content here.
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
            "5",
            "--max-workers",
            "1",
            str(tmp_path / "doc"),
        ],
    )

    # Should fail validation (case-sensitive matching)
    assert result.exit_code != 0

    data = json.loads(result.output)

    # Should have entry for the case-mismatched label
    case_mismatch_found = False
    for items in data.values():
        for item in items:
            if "My Label" in item["link"]:
                case_mismatch_found = True
                break
        if case_mismatch_found:
            break

    assert case_mismatch_found, (
        "Case-mismatched custom labels should be reported as broken links"
    )


def test_check_links_custom_labels_ignored_in_code_blocks(tmp_path: Path):
    """Test that custom label references inside code blocks are ignored."""
    src = tmp_path / "doc" / "source"

    # File with custom label definition
    file_with_definitions = src / "definitions.rst"
    write(
        file_with_definitions,
        """
.. My Label: https://invalid.example.com/page1

Content here.
""".lstrip(),
    )

    # File with custom label reference inside code block
    file_with_references = src / "references.rst"
    write(
        file_with_references,
        """
Title
=====

Valid reference:
- `My Label`_

Code block with ignored reference:
.. code-block:: rst

   This is a code block with `My Label`_ that should be ignored

Content here.
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
            "5",
            "--max-workers",
            "1",
            str(tmp_path / "doc"),
        ],
    )

    # Should fail validation because the URL in the custom label definition is invalid
    assert result.exit_code != 0

    # Parse the output to verify the broken link
    data = json.loads(result.output)

    # Should have entry for the invalid URL
    invalid_url_found = False
    for items in data.values():
        for item in items:
            if "invalid.example.com" in item["link"]:
                invalid_url_found = True
                break
        if invalid_url_found:
            break

    assert invalid_url_found, (
        "Invalid URL in custom label definition should be reported as broken link"
    )


def test_check_links_custom_labels_mixed_with_other_links(tmp_path: Path):
    """Test that custom label checking works alongside other link types."""
    src = tmp_path / "doc" / "source"

    # File with various definitions
    file_with_definitions = src / "definitions.rst"
    write(
        file_with_definitions,
        """
.. _good-label:

.. My Label: https://invalid.example.com/page1

Section
=======

Content here.
""".lstrip(),
    )

    # File with mixed link types
    file_with_references = src / "references.rst"
    write(
        file_with_references,
        """
Title
=====

External link: https://example.invalid.domain.tld/this-should-fail

Ref good: :ref:`good-label`
Ref bad: :ref:`missing-label`

Custom label good: `My Label`_
Custom label bad: `Missing Label`_

Content here.
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
            "5",
            "--max-workers",
            "1",
            str(tmp_path / "doc"),
        ],
    )

    # Should fail validation (broken links found)
    assert result.exit_code != 0

    data = json.loads(result.output)

    # Should have entries for various broken link types
    broken_external = False
    broken_ref = False
    broken_custom = False

    for items in data.values():
        for item in items:
            if "example.invalid.domain.tld" in item["link"]:
                broken_external = True
            elif "missing-label" in item["link"]:
                broken_ref = True
            elif "Missing Label" in item["link"]:
                broken_custom = True

    assert broken_external, "Broken external link should be reported"
    assert broken_ref, "Broken :ref: link should be reported"
    assert broken_custom, "Broken custom label should be reported"
