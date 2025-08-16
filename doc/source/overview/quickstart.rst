Quickstart Guide
================

This guide will get you up and running with ``rstbuddy`` quickly, showing the
command-line interface for working with reStructuredText (RST) files.

Prerequisites
-------------

- Python 3.11 or higher
- Follow the :doc:`/overview/installation` instructions to install ``rstbuddy``
- Pandoc (optional, required only for AI summarization feature)
- OpenAI API key (optional, required only for AI summarization feature)

Configuration
-------------

Typically the defaults that ship with ``rstbuddy`` will work.

You can configure ``rstbuddy`` using configuration files or environment
variables. See :doc:`/overview/configuration` for more details.

Basic Usage
-----------

Get Help
^^^^^^^^

.. code-block:: bash

    # Show main help
    rstbuddy --help

    # Show help for specific commands
    rstbuddy check-links --help
    rstbuddy fix --help
    rstbuddy gather-links --help
    rstbuddy summarize --help
    rstbuddy outline-to-rst --help
    rstbuddy settings --help

Check Links Usage
^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Check all links in default doc/source directory
    rstbuddy check-links

    # Check links in specific directory
    rstbuddy check-links /path/to/docs

    # Use custom timeout and workers
    rstbuddy check-links --timeout 10 --max-workers 16

    # Skip robots.txt checks
    rstbuddy check-links --no-check-robots

Gather Links Usage
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Gather all hyperlinks from the documentation directory, add them to
    # <documentation_dir>/_links.rst, replace the links in the text with
    # refereces to links in _links.rst and update conf.py to include them in the
    # epilog.
    rstbuddy gather-links

    # Preview changes without modifying the files
    rstbuddy gather-links --dry-run

Fix RST Files Usage
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Fix a single RST file (creates backup automatically)
    rstbuddy fix document.rst

    # Preview changes without modifying the file
    rstbuddy fix document.rst --dry-run

    # Fix multiple files at a time
    find . -name "*.rst" -exec rstbuddy fix {} \;

AI Summarization Usage
^^^^^^^^^^^^^^^^^^^^^^

.. important::

    **OpenAI API Key Required**: This feature requires a valid OpenAI API key.
    See :doc:`/overview/configuration` for setup instructions.

.. code-block:: bash

    # Generate AI summary of an RST file
    rstbuddy summarize document.rst

    # Use with custom configuration
    rstbuddy --config-file ai-config.toml summarize document.rst

Outline Conversion Usage
^^^^^^^^^^^^^^^^^^^^^^^^

.. important::

    **Pandoc Required**: This feature requires Pandoc to be installed.
    See :doc:`/overview/installation` for Pandoc installation instructions.

.. code-block:: bash

    # Convert a markdown outline to RST documentation structure
    rstbuddy outline-to-rst outline.md

    # Convert with custom output directory
    rstbuddy outline-to-rst outline.md --output-dir ./docs

    # Preview what would be created without making changes
    rstbuddy outline-to-rst outline.md --dry-run

    # Force overwrite existing files (creates backups)
    rstbuddy outline-to-rst outline.md --force

Settings Usage
^^^^^^^^^^^^^^

.. code-block:: bash

    # Show all current settings
    rstbuddy settings

    # Show settings in JSON format
    rstbuddy --output json settings

    # Show settings in text format
    rstbuddy --output text settings

Output Formats
^^^^^^^^^^^^^^

.. code-block:: bash

    # Use table format (default) for human reading
    rstbuddy check-links --output table

    # Use JSON format for scripting
    rstbuddy check-links --output json

    # Use text format for simple output
    rstbuddy check-links --output text

Next Steps
----------

Now that you have the basics working:

1. **Usage**: See :doc:`/overview/usage` for more advanced features and detailed examples.
2. **Configuration**: See :doc:`/overview/configuration` for configuration options.
3. **Troubleshooting**: See the troubleshooting sections in each guide for common issues.

Getting Help
------------

- Check the full documentation for detailed examples
- Review the troubleshooting sections in each guide
- Report issues on the GitHub repository

Common Workflows
----------------

Documentation Maintenance
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # 1. Check for broken links
    rstbuddy check-links

    # 2. Fix formatting issues
    rstbuddy fix /path/to/rst_file.rst

    # 3. Verify fixes
    rstbuddy check-links

Content Migration
^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # 1. Fix Markdown-to-RST conversion issues
    rstbuddy fix migrated_document.rst

    # 2. Check that all internal links work
    rstbuddy check-links

    # 3. Generate summary (if AI features enabled)
    rstbuddy summarize migrated_document.rst

Outline Conversion
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # 1. Convert markdown outline to RST structure
    rstbuddy outline-to-rst outline.md --dry-run

    # 2. Review the planned structure
    rstbuddy outline-to-rst outline.md

    # 3. Check that all generated links work
    rstbuddy check-links ./output_directory

Quality Assurance
^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # 1. Validate all documentation links
    rstbuddy check-links /path/to/docs

    # 2. Fix any formatting issues
    find /path/to/docs -name "*.rst" -exec rstbuddy fix {} \;

    # 3. Re-check links to ensure fixes worked
    rstbuddy check-links /path/to/docs