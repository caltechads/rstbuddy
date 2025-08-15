Using the Command Line Interface
================================

The ``rstbuddy`` command-line interface provides
comprehensive tools for working with reStructuredText (RST) files. This guide covers all
available commands and options.

Getting Help
------------

Basic Help
^^^^^^^^^^

.. code-block:: bash

    # Show main help
    rstbuddy --help

    # Show help for specific commands
    rstbuddy check-links --help
    rstbuddy gather-links --help
    rstbuddy fix --help
    rstbuddy summarize --help
    rstbuddy settings --help

Command Structure
-----------------

The CLI follows a hierarchical command structure:

.. code-block:: bash

    rstbuddy [global-options] <command> [options] [arguments]

Global Options
--------------

Common options available for all commands:

.. code-block:: bash

    # Enable verbose output
    rstbuddy --verbose command

    # Suppress all output except errors
    rstbuddy --quiet command

    # Specify custom configuration file
    rstbuddy --config-file /path/to/config.toml command

    # Choose output format (json, table, text)
    rstbuddy --output json command
    rstbuddy --output table command
    rstbuddy --output text command

Check Links Command
-------------------

The ``check-links`` command recursively scans RST files for broken links.

Basic Usage
^^^^^^^^^^^

Check links in the default documentation directory:

.. code-block:: bash

    # Check links in default doc/source directory
    rstbuddy check-links

    # Check links in specific directory
    rstbuddy check-links /path/to/docs

    # Use custom timeout and workers
    rstbuddy check-links --timeout 10 --max-workers 16

    # Skip robots.txt checks
    rstbuddy check-links --no-check-robots

    # Use custom user agent
    rstbuddy check-links --user-agent "MyBot/1.0"

Command Options
^^^^^^^^^^^^^^^

**--timeout**
    Per-link network timeout in seconds (default: 5)

**--max-workers**
    Maximum number of concurrent workers for network checks (default: 8)

**--no-check-robots**
    Disable robots.txt checks for external links

**--user-agent**
    User-Agent string for HTTP requests and robots.txt (default: "rstbuddy-linkcheck/1.0")

What Gets Checked
^^^^^^^^^^^^^^^^^

The command validates:

- **External HTTP(S) Links**: URLs that return non-200 status codes or fail to connect
- **Sphinx :ref: Roles**: References to labels that don't exist as explicit ``.. _label:`` declarations
- **Sphinx :doc: Roles**: Document references where target .rst files cannot be resolved
- **Directive Paths**: Include, literalinclude, download, image, figure, and thumbnail directives

Example Output
^^^^^^^^^^^^^^

Table output (default):

.. code-block:: text

    ┌─────────────────────────────────────────────────────────────────┐
    │                        Broken RST Links                         │
    ├─────────────────────────────────────────────────────────────────┤
    │ File                    │ Line │ Link                           │
    ├─────────────────────────────────────────────────────────────────┤
    │ overview/quickstart.rst │ 45   │ https://broken-link.com        │
    │ api/models.rst          │ 12   │ :ref:`nonexistent_label`       │
    │ api/models.rst          │ 23   │ :doc:`missing_document`        │
    └─────────────────────────────────────────────────────────────────┘

JSON output:

.. code-block:: json

    {
      "overview/quickstart.rst": [
        {
          "line": 45,
          "link": "https://broken-link.com",
          "robots_disallowed": null
        }
      ],
      "api/models.rst": [
        {
          "line": 12,
          "link": ":ref:`nonexistent_label`",
          "robots_disallowed": null
        },
        {
          "line": 23,
          "link": ":doc:`missing_document`",
          "robots_disallowed": null
        }
      ]
    }

Gather Links Command
--------------------

The ``gather-links`` command consolidates all external hyperlinks from RST documentation into a centralized ``_links.rst`` file and replaces inline links with references.

Basic Usage
^^^^^^^^^^^

Gather links from the default documentation directory:

.. code-block:: bash

    # Gather links from default doc/source directory
    rstbuddy gather-links

    # Gather links from specific directory
    rstbuddy gather-links /path/to/docs

    # Preview changes without making them
    rstbuddy gather-links --dry-run

    # Show detailed progress
    rstbuddy gather-links --verbose

Arguments
^^^^^^^^^

**ROOT**: Optional path to the documentation directory. If not specified, uses the :py:class:`rstbuddy.config.Settings.documentation_dir` setting.

Command Options
^^^^^^^^^^^^^^^

**--dry-run**
    Show what would be done without making changes

**--verbose**
    Show detailed progress and operations

What It Does
^^^^^^^^^^^^

The command performs the following operations:

1. **Link Discovery**: Recursively scans all ``.rst`` files for external hyperlinks
2. **Label Generation**: Creates unique labels for each URL
3. **File Creation**: Generates or updates ``_links.rst`` with consolidated links
4. **Backup Creation**: Creates timestamped backups of files to be modified
5. **Link Replacement**: Replaces inline links with label references
6. **Configuration Update**: Updates ``conf.py`` with ``rst_epilog`` configuration

Link Detection
^^^^^^^^^^^^^^

The command detects two types of RST hyperlinks:

- **Simple links**: ``<https://example.com>`_``
- **Labeled links**: ``Label <https://example.com>`_``

Links are only processed if they:
- Use HTTP or HTTPS schemes
- Are not relative URLs
- Are not anchor links (starting with #)
- Are not in sections containing "References" (case-insensitive)

Label Generation
^^^^^^^^^^^^^^^^

Labels are generated automatically for URLs without explicit labels:

* **Domain-only URLs**: Convert domain to CamelCase

  * ``https://github.com`` → ``GithubCom``
  * ``https://www.python.org`` → ``PythonOrg``

* **URLs with paths**: Add path components for uniqueness

  * ``https://github.com/user/repo`` → ``GithubComRepo``
  * ``https://docs.python.org/3/library/os.html`` → ``DocsPythonOrgOs``

The system ensures all labels are unique within the ``_links.rst`` file.

Output Files
^^^^^^^^^^^^

``_links.rst``: Contains all external hyperlinks in the format:
``.. _Label: https://example.com``

**Backup files**: Timestamped backups (``filename.YYYYMMDDHHMMSS.bak``) are created before any modifications.

Example Output
^^^^^^^^^^^^^^

.. code-block:: text

    Scanning RST files in /path/to/docs
    Found 15 RST files to process
    Discovered 8 unique external links
    Created/updated _links.rst
    Backed up /path/to/docs/file1.rst to /path/to/docs/file1.rst.20241201120000.bak
    Updated /path/to/docs/file1.rst
    Updated /path/to/docs/file2.rst
    Updated conf.py
    Link gathering completed successfully

Best Practices
^^^^^^^^^^^^^^

* **Use dry-run first**: Always test with ``--dry-run`` before making changes
* **Review backups**: Check that backups were created successfully
* **Test builds**: Verify that Sphinx builds work after link consolidation
* **Version control**: Commit the new ``_links.rst`` file to your repository

Troubleshooting
^^^^^^^^^^^^^^^

Common Issues
~~~~~~~~~~~~~

**Backup failures**: The command halts if any backup operation fails. Check file permissions and disk space.

**Encoding issues**: The command attempts to handle various file encodings automatically.

**Large documentation sets**: Progress indicators show current operation status.

**Conf.py not found**: The command warns if ``conf.py`` is missing but continues processing.

Error Recovery
~~~~~~~~~~~~~~

If the process fails:

1. Check the error messages for specific issues
2. Verify file permissions and disk space
3. Restore from backups if needed
4. Run with ``--dry-run`` to identify problems

Fix Command
-----------

The ``fix`` command cleans and fixes RST files in place.

Basic Usage
^^^^^^^^^^^

Fix a single RST file:

.. code-block:: bash

    # Fix a file with automatic backup
    rstbuddy fix document.rst

    # Preview changes without modifying the file
    rstbuddy fix document.rst --dry-run

What Gets Fixed
^^^^^^^^^^^^^^^

The command applies the following fixes:

- **Markdown Headings**: Converts ``#``, ``##``, ``###`` to RST headings with proper underlines
- **RST Headings**: Normalizes existing heading underlines to match title length exactly
- **Code Blocks**: Converts fenced Markdown code blocks to RST code-block directives
- **Inline Code**: Converts single-backtick spans to RST inline literals
- **List Spacing**: Ensures proper blank lines after list blocks
- **Stray Fences**: Removes orphaned triple backticks

Example Output
^^^^^^^^^^^^^^

.. code-block:: text

    ┌─────────────────────────────────────────────────────────────────┐
    │                        RST Clean Summary                        │
    ├─────────────────────────────────────────────────────────────────┤
    │ File           │ Headings │ MD Headings │ Lists │ Code Blocks   │
    ├─────────────────────────────────────────────────────────────────┤
    │ document.rst   │ 3        │ 5            │ 2     │ 1            │
    └─────────────────────────────────────────────────────────────────┤

Summarize Command
-----------------

The ``summarize`` command generates AI-powered summaries of RST files.

.. important::

    **OpenAI API Key Required**: This feature requires a valid OpenAI API key to be configured.
    See :doc:`/overview/configuration` for setup instructions.

Basic Usage
^^^^^^^^^^^

Generate a summary of an RST file:

.. code-block:: bash

    # Generate summary using OpenAI
    rstbuddy summarize document.rst

    # Use with custom configuration
    rstbuddy --config-file ai-config.toml summarize document.rst

What It Does
^^^^^^^^^^^^

The command:

1. **Reads the RST file** and converts it to Markdown using Pandoc
2. **Generates an AI summary** using OpenAI's API
3. **Displays the summary** in a formatted output

Requirements
^^^^^^^^^^^^

- **Pandoc**: Must be installed and available in PATH
- **OpenAI API Key**: Must be configured via settings or environment variables
- **Internet Connection**: Required for API calls to OpenAI

Example Output
^^^^^^^^^^^^^^

.. code-block:: text

    === Step 1: Reading RST file ===
    Successfully read 15420 characters

    === Step 4: Converting RST to Markdown ===
    Successfully converted content to Markdown

    === Step 3: Generating summary ===
    === Step 4: Displaying summary ===

    ┌─────────────────────────────────────────────────────────────────┐
    │                    AI-Generated Summary                         │
    ├─────────────────────────────────────────────────────────────────┤
    │ This document provides a comprehensive guide to...              │
    │                                                                 │
    │ Key topics covered:                                             │
    │ • Installation and setup                                        │
    │ • Configuration options                                         │
    │ • Usage examples                                                │
    │ • Troubleshooting tips                                          │
    └─────────────────────────────────────────────────────────────────┘

Version Command
---------------

The ``version`` command displays version information.

Basic Usage
^^^^^^^^^^^

.. code-block:: bash

    # Show version information
    rstbuddy version

Example Output
^^^^^^^^^^^^^^

.. code-block:: text

    ┌─────────────────────────────────────────────────────────────────┐
    │                      rstbuddy Version Info                      │
    ├─────────────────────────────────────────────────────────────────┤
    │ Package    │ Version                                            │
    ├─────────────────────────────────────────────────────────────────┤
    │ rstbuddy   │ 0.1.0                                              │
    │ click      │ 8.1.7                                              │
    │ rich       │ 13.7.0                                             │
    └─────────────────────────────────────────────────────────────────┘

Settings Command
----------------

The ``settings`` command displays current configuration settings.

Basic Usage
^^^^^^^^^^^

.. code-block:: bash

    # Show all settings in table format (default)
    rstbuddy settings

    # Show settings in JSON format
    rstbuddy --output json settings

    # Show settings in text format
    rstbuddy --output text settings

Example Output
^^^^^^^^^^^^^^

Table output (default):

.. code-block:: text

    ┌─────────────────────────────────────────────────────────────────┐
    │                            Settings                             │
    ├─────────────────────────────────────────────────────────────────┤
    │ Setting Name                    │ Value                         │
    ├─────────────────────────────────────────────────────────────────┤
    │ app_name                        │ rstbuddy                      │
    │ app_version                     │ 0.1.0                         │
    │ documentation_dir               │ doc/source                    │
    │ openai_api_key                  │                               │
    │ clean_rst_extra_protected_regexes │ []                          │
    │ check_rst_links_skip_domains   │ []                             │
    │ check_rst_links_extra_skip_directives │ []                      │
    │ default_output_format           │ table                         │
    │ enable_colors                   │ True                          │
    │ quiet_mode                      │ False                         │
    │ log_level                       │ INFO                          │
    │ log_file                        │ None                          │
    └─────────────────────────────────────────────────────────────────┘

Output Formats
--------------

Table Format (Default)
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Table output for better readability
    rstbuddy check-links
    rstbuddy fix document.rst
    rstbuddy settings

JSON Format
^^^^^^^^^^^

.. code-block:: bash

    # JSON output for scripting and automation
    rstbuddy --output json check-links > broken_links.json
    rstbuddy --output json settings > settings.json

Text Format
^^^^^^^^^^^

.. code-block:: bash

    # Simple text output
    rstbuddy --output text check-links
    rstbuddy --output text settings

Configuration
-------------

See :doc:`/overview/configuration` for details on how to configure
``rstbuddy`` for your specific environment.

Examples
--------

Basic Usage Examples
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Check all links in documentation
    rstbuddy check-links

    # Fix formatting issues in a file
    rstbuddy fix README.rst

    # Generate AI summary (requires OpenAI API key)
    rstbuddy summarize document.rst

    # Show current settings
    rstbuddy settings

Advanced Usage Examples
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Check links with custom timeout and workers
    rstbuddy check-links --timeout 15 --max-workers 20

    # Fix file with preview (dry run)
    rstbuddy fix document.rst --dry-run

    # Use custom configuration file
    rstbuddy --config-file ./rstbuddy.toml check-links

    # Output in JSON format for scripting
    rstbuddy --output json check-links > report.json

Scripting Examples
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    #!/bin/bash

    echo "Checking RST documentation..."

    # Check for broken links
    if rstbuddy check-links; then
        echo "All links are valid!"
    else
        echo "Found broken links. Check the output above."
        exit 1
    fi

    echo "Fixing RST formatting..."

    # Fix all RST files in current directory
    for file in *.rst; do
        if [ -f "$file" ]; then
            echo "Fixing $file..."
            rstbuddy fix "$file"
        fi
    done

    echo "Documentation maintenance complete."

Error Handling
--------------

Common Error Scenarios
^^^^^^^^^^^^^^^^^^^^^^

**Broken Links Found**

    .. code-block:: bash

        # Error: Broken links detected
        rstbuddy check-links
        # SystemExit: 1 (non-zero exit code)

        # Solution: Review and fix broken links manually
        # Check if links are actually broken or blocked by WAF/Cloudflare

**File Not Found**

    .. code-block:: bash

        # Error: File does not exist
        rstbuddy fix nonexistent.rst
        # Error: [Errno 2] No such file or directory

        # Solution: Ensure the file exists and path is correct
        ls *.rst

**OpenAI API Key Missing**

    .. code-block:: bash

        # Error: OpenAI API key not configured
        rstbuddy summarize document.rst
        # Error: ConfigurationError: OpenAI API key required

        # Solution: Set API key in configuration or environment
        export RSTBUDDY_OPENAI_API_KEY="your-key-here"

Troubleshooting
---------------

Debugging Commands
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Enable verbose output for debugging
    rstbuddy --verbose check-links

    # Use dry run to preview changes
    rstbuddy fix document.rst --dry-run

    # Check current configuration
    rstbuddy settings

Common Issues
~~~~~~~~~~~~~

**False Positive Broken Links**

    - **WAF/Cloudflare Protection**: Some websites block automated tools
    - **Rate Limiting**: Servers may temporarily block requests
    - **User-Agent Filtering**: Some sites reject certain user agents
    - **Solution**: Manually verify links that appear broken

**Pandoc Not Found**

    - **Error**: "pandoc: command not found"
    - **Solution**: Install Pandoc from https://pandoc.org/installing.html
    - **Alternative**: Use other commands that don't require Pandoc

**OpenAI API Errors**

    - **Rate Limiting**: API may throttle requests
    - **Authentication**: Verify API key is correct and has sufficient credits
    - **Network Issues**: Check internet connection and firewall settings

Best Practices
--------------

Output Format Selection
^^^^^^^^^^^^^^^^^^^^^^^

Choose appropriate output formats:

.. code-block:: bash

    # Use table for human reading (default)
    rstbuddy check-links

    # Use JSON for scripting and automation
    rstbuddy --output json check-links > report.json

    # Use text for simple output
    rstbuddy --output text settings

Configuration Management
^^^^^^^^^^^^^^^^^^^^^^^^

Use configuration files when necessary:

.. code-block:: bash

    # Use custom configuration file
    rstbuddy --config-file ./rstbuddy.toml check-links

    # Set environment variables
    export RSTBUDDY_DOCUMENTATION_DIR="./docs"
    rstbuddy check-links

Link Checking Best Practices
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Manual Verification**: Always verify HTTP links manually if they appear broken
- **WAF Awareness**: Be aware that Cloudflare and other WAFs may block automated tools
- **Rate Limiting**: Use appropriate timeouts and worker counts
- **Robots.txt**: Respect robots.txt when checking external links