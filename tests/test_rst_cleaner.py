from __future__ import annotations

from rstbuddy.services.rst_cleaner import RSTCleaner


def test_markdown_headings_converted_levels():
    cleaner = RSTCleaner()
    text = """# Title

## Subtitle

### Third Level

#### Fourth Level
"""
    cleaned, report = cleaner.clean_text(text)
    assert "Title\n=====\n" in cleaned
    assert "Subtitle\n--------\n" in cleaned
    assert "Third Level\n^^^^^^^^^^^\n" in cleaned
    assert "Fourth Level\n~~~~~~~~~~~~\n" in cleaned
    assert report.md_headings_converted == 4  # noqa: PLR2004


def test_code_fence_conversion_and_cleanup():
    cleaner = RSTCleaner()
    text = """```python
print('hi')
```

```
no lang
```
"""
    cleaned, report = cleaner.clean_text(text)
    assert ".. code-block:: python" in cleaned
    assert "    print('hi')" in cleaned
    assert ".. code-block:: text" in cleaned
    assert report.code_blocks_converted == 2  # noqa: PLR2004
    assert report.stray_fences_removed == 0


def test_inline_code_heuristic():
    cleaner = RSTCleaner()
    text = "Use `my_func(x)` in `module.sub` but not `emphasis` please."
    cleaned, report = cleaner.clean_text(text)
    assert "``my_func(x)``" in cleaned
    assert "``module.sub``" in cleaned
    assert report.inline_code_fixed >= 2  # noqa: PLR2004


def test_list_spacing():
    cleaner = RSTCleaner()
    text = """- one
- two
not list
"""
    cleaned, report = cleaner.clean_text(text)
    assert "two\n\nnot list" in cleaned
    assert report.lists_spaced >= 1


def test_do_not_touch_sphinx_roles_and_links():
    cleaner = RSTCleaner()
    text = (
        "See :doc:`installing` and also :ref:`sec-label`. "
        "This is a link `inline <https://example.com>`_ and `ref`_."
    )
    cleaned, _ = cleaner.clean_text(text)
    assert ":doc:`installing`" in cleaned
    assert ":ref:`sec-label`" in cleaned
    assert "`inline <https://example.com>`_" in cleaned
    assert "`ref`_" in cleaned


def test_do_not_modify_inside_directives():
    cleaner = RSTCleaner()
    text = ".. code-block:: python\n\n    # do not touch this\n    print('x')\n\n"
    cleaned, _ = cleaner.clean_text(text)
    # code-block content preserved
    assert "# do not touch this" in cleaned
    assert "print('x')" in cleaned


def test_empty_sphinx_comment_preserved():
    cleaner = RSTCleaner()
    text = "..\n\nTitle\n-----\n"
    cleaned, _ = cleaner.clean_text(text)
    # First line should remain exactly ".."
    assert cleaned.splitlines()[0] == ".."


def test_no_blank_line_before_summary_and_between_code_blocks():
    cleaner = RSTCleaner()
    text = (
        "- item\n"
        "text\n\n"
        ".. code-block:: bash\n\n"
        "    echo 1\n"
        ".. code-block:: bash\n\n"
        "    echo 2\n\n"
    )
    cleaned, _ = cleaner.clean_text(text)
    lines = cleaned.splitlines()
    # Ensure a blank line was inserted between consecutive code-block directives
    idx1 = lines.index(".. code-block:: bash")
    assert lines[idx1 + 1].strip() == ""  # blank line
    assert lines[idx1 + 2].startswith("    echo 1") or lines[idx1 + 2].startswith(
        ".. code-block:: bash"
    )
