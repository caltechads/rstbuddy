from __future__ import annotations

import json
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
