Configuration: Command Line Tool
================================

This guide covers all configuration options for the
``rstbuddy`` command line tool, including
configuration files, environment variables, and command-line options.

``rstbuddy`` is a Python command-line tool for working with reStructuredText (RST) files.
The default configuration should work for most use cases, but you can customize behavior
through various configuration methods.

Configuration Methods
---------------------

The ``rstbuddy`` command line tool supports multiple configuration methods,
loaded in order of priority:

1. **Command-line options** (highest priority)
2. **Environment variables** in the shell environment
3. **Configuration files**: a cascade of TOML files, most specific wins.
4. **Default values** (lowest priority)

Configuration Files
-------------------

File Locations
^^^^^^^^^^^^^^

Configuration files are searched in this order:

1. **Global configuration**: ``/etc/rstbuddy/.rstbuddy.toml`` (Unix/Linux) or ``C:/ProgramData/.rstbuddy.toml`` (Windows)
2. **User configuration**: ``~/.config/.rstbuddy.toml``
3. **Local configuration**: ``./.rstbuddy.toml`` (current directory)
4. **Environment variables**: via the ``RSTBUDDY_CONFIG_FILE`` environment variable
5. **Explicit configuration**: Path specified with ``--config-file`` option

File Format
^^^^^^^^^^^

Configuration files use TOML format:

.. code-block:: toml

    # Documentation directory
    documentation_dir = "doc/source"

    # OpenAI Configuration (for AI summarization)
    openai_api_key = "your-api-key-here"

    # RST Cleaning Settings
    clean_rst_extra_protected_regexes = [
        "\\bprotected_pattern\\b",
        "\\bdo_not_modify\\b"
    ]

    # RST Link Checking Settings
    check_rst_links_skip_domains = [
        "example.com",
        "test.local"
    ]
    check_rst_links_extra_skip_directives = [
        "custom_code",
        "protected_block"
    ]

    # Output settings
    default_output_format = "table"
    enable_colors = true
    quiet_mode = false

    # Logging settings
    log_level = "INFO"
    log_file = "/var/log/rstbuddy.log"

Configuration Options
^^^^^^^^^^^^^^^^^^^^^

**Application Settings**
    - **app_name**: Application name (default: ``rstbuddy``, readonly)
    - **app_version**: Application version (default: ``0.2.2``, readonly)

**Documentation Settings**
    - **documentation_dir**: Top-level directory for RST files to be processed (default: ``doc/source``)

**OpenAI Configuration**
    - **openai_api_key**: OpenAI API key for AI summarization feature (default: empty string)

**RST Cleaning Settings**
    - **clean_rst_extra_protected_regexes**: List of regex patterns; if a line matches any, rstbuddy will not modify that line (default: empty list)

**RST Link Checking Settings**
    - **check_rst_links_skip_domains**: List of domain substrings to skip during external link validation (default: empty list)
    - **check_rst_links_extra_skip_directives**: Additional directive names whose content should be ignored when scanning links (default: empty list)

**Output Settings**
    - **default_output_format**: Default output format - ``table``, ``json``, or ``text`` (default: ``table``)
    - **enable_colors**: Enable colored output (default: ``true``)
    - **quiet_mode**: Enable quiet mode (default: ``false``)

**Logging Settings**
    - **log_level**: Logging level - ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR`` (default: ``INFO``)
    - **log_file**: Log file path (default: ``None``)

Environment Variables
---------------------

You can set configuration using environment variables. Environment variables
follow the pattern ``RSTBUDDY_<SETTING_NAME>``:

.. code-block:: bash

    # Set documentation directory
    export RSTBUDDY_DOCUMENTATION_DIR="/path/to/docs"

    # Set OpenAI API key
    export RSTBUDDY_OPENAI_API_KEY="your-api-key-here"

    # Set output format
    export RSTBUDDY_DEFAULT_OUTPUT_FORMAT="json"

    # Set log level
    export RSTBUDDY_LOG_LEVEL="DEBUG"

Environment Variable Mapping
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ``RSTBUDDY_DOCUMENTATION_DIR`` → ``documentation_dir``
- ``RSTBUDDY_OPENAI_API_KEY`` → ``openai_api_key``
- ``RSTBUDDY_CLEAN_RST_EXTRA_PROTECTED_REGEXES`` → ``clean_rst_extra_protected_regexes``
- ``RSTBUDDY_CHECK_RST_LINKS_SKIP_DOMAINS`` → ``check_rst_links_skip_domains``
- ``RSTBUDDY_CHECK_RST_LINKS_EXTRA_SKIP_DIRECTIVES`` → ``check_rst_links_extra_skip_directives``
- ``RSTBUDDY_DEFAULT_OUTPUT_FORMAT`` → ``default_output_format``
- ``RSTBUDDY_ENABLE_COLORS`` → ``enable_colors``
- ``RSTBUDDY_QUIET_MODE`` → ``quiet_mode``
- ``RSTBUDDY_LOG_LEVEL`` → ``log_level``
- ``RSTBUDDY_LOG_FILE`` → ``log_file``

Command-Line Options
--------------------

Global Options
^^^^^^^^^^^^^^

All commands support these global options:

.. code-block:: bash

    # Enable verbose output
    rstbuddy --verbose command

    # Suppress all output except errors
    rstbuddy --quiet command

    # Specify custom configuration file
    rstbuddy --config-file /path/to/config.toml command

    # Choose output format
    rstbuddy --output json command
    rstbuddy --output table command
    rstbuddy --output text command

Option Reference
^^^^^^^^^^^^^^^^

**--verbose, -v**
    Enable verbose output with detailed logging.

    Example:
    .. code-block:: bash

        rstbuddy --verbose check-links

**--quiet, -q**
    Suppress all output except errors.

    Example:
    .. code-block:: bash

        rstbuddy --quiet fix file.rst

**--config-file**
    Specify a custom configuration file path.

    Example:
    .. code-block:: bash

        rstbuddy --config-file ./custom-config.toml check-links

**--output**
    Choose output format: ``json``, ``table``, or ``text``.

    Default: ``table``

    Example:
    .. code-block:: bash

        rstbuddy --output json check-links

Configuration Examples
----------------------

Basic Setup
^^^^^^^^^^^

For basic usage with defaults:

.. code-block:: toml

    # ~/.config/.rstbuddy.toml
    # No configuration file needed - defaults work for most cases

Development Environment
^^^^^^^^^^^^^^^^^^^^^^^

For development and testing:

.. code-block:: toml

    # ~/.config/.rstbuddy.toml
    documentation_dir = "docs"
    default_output_format = "json"
    enable_colors = true
    log_level = "DEBUG"

    # Skip test domains during link checking
    check_rst_links_skip_domains = [
        "test.example.com",
        "localhost"
    ]

Production Environment
^^^^^^^^^^^^^^^^^^^^

For production systems:

.. code-block:: toml

    # /etc/rstbuddy/.rstbuddy.toml
    documentation_dir = "/var/www/docs"
    default_output_format = "table"
    enable_colors = false
    log_level = "WARNING"
    log_file = "/var/log/rstbuddy.log"

    # Protect specific patterns from modification
    clean_rst_extra_protected_regexes = [
        "\\bPRODUCTION_ONLY\\b",
        "\\bDO_NOT_MODIFY\\b"
    ]

AI Summarization Setup
^^^^^^^^^^^^^^^^^^^^^^

To enable AI-powered summarization:

.. code-block:: toml

    # ~/.config/.rstbuddy.toml
    # OpenAI API key for AI summarization
    openai_api_key = "sk-..."

    # Other settings as needed
    documentation_dir = "docs"
    default_output_format = "table"

Link Checking Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^

For projects with specific link checking needs:

.. code-block:: toml

    # ~/.config/.rstbuddy.toml
    # Skip specific domains that often give false positives
    check_rst_links_skip_domains = [
        "cloudflare.com",
        "waf.example.com"
    ]

    # Skip custom directives that contain code
    check_rst_links_extra_skip_directives = [
        "custom_code_block",
        "protected_section"
    ]

Scripting Configuration
^^^^^^^^^^^^^^^^^^^^^^^

For automation and scripting:

.. code-block:: toml

    # ~/.config/.rstbuddy.toml
    default_output_format = "json"
    enable_colors = false
    quiet_mode = true
    log_level = "ERROR"
    log_file = "/dev/stdout"

Security Considerations
-----------------------

Configuration File Security
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Protect your configuration files:

.. code-block:: bash

    # Set proper permissions for user configuration
    chmod 600 ~/.config/.rstbuddy.toml

    # For system-wide configuration
    chmod 640 /etc/rstbuddy/.rstbuddy.toml
    chown root:root /etc/rstbuddy/.rstbuddy.toml

Environment Variable Security
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Secure environment variable usage:

.. code-block:: bash

    # Set sensitive data as environment variables
    export RSTBUDDY_OPENAI_API_KEY="your-secret-key"

    # Clear sensitive environment variables after use
    unset RSTBUDDY_OPENAI_API_KEY

OpenAI API Key Security
^^^^^^^^^^^^^^^^^^^^^^^

When using AI summarization:

.. code-block:: bash

    # Store API key securely
    export RSTBUDDY_OPENAI_API_KEY="sk-..."

    # Use in scripts
    rstbuddy summarize document.rst

    # Clear after use
    unset RSTBUDDY_OPENAI_API_KEY

Common Issues
^^^^^^^^^^^^^

**Configuration Not Loaded**
    - Check file permissions
    - Verify file format (TOML syntax)
    - Ensure file is in correct location
    - Check for syntax errors in TOML file

**Configuration Not Valid**
    - Verify TOML syntax is correct
    - Check that setting names match expected values
    - Ensure boolean values are ``true``/``false``, not ``True``/``False``

**Environment Variables Not Recognized**
    - Check variable names (must start with ``RSTBUDDY_``)
    - Restart terminal session
    - Verify variable values

**Command-Line Options Override**
    - Command-line options take highest priority
    - Check for conflicting options
    - Use ``--help`` to see current options

Configuration Validation
------------------------

Validation Rules
^^^^^^^^^^^^^^^^

The library validates configuration:

- **default_output_format**: Must be one of ``table``, ``json``, or ``text``
- **log_level**: Must be one of ``DEBUG``, ``INFO``, ``WARNING``, or ``ERROR``
- **enable_colors**: Must be a boolean value
- **quiet_mode**: Must be a boolean value
- **documentation_dir**: Must be a valid directory path

Error Messages
^^^^^^^^^^^^^^

Common validation errors:

.. code-block:: bash

    # Invalid output format
    Error: Invalid default_output_format value

    # Invalid log level
    Error: log_level must be one of DEBUG, INFO, WARNING, ERROR

    # Invalid documentation directory
    Error: Documentation dir 'invalid/path' does not exist

Best Practices
--------------

Configuration Management
^^^^^^^^^^^^^^^^^^^^^^^^^

1. **Use configuration files for defaults**

   - Set common settings in ``~/.config/.rstbuddy.toml``
   - Use environment variables for overrides
   - Use command-line options for one-time changes

2. **Separate environments**

   - Use different config files for different environments
   - Use environment variables for sensitive data
   - Document configuration requirements

3. **Version control**

   - Don't commit sensitive configuration
   - Use templates for configuration files
   - Document configuration changes

4. **Security**

   - Protect configuration files with proper permissions
   - Use environment variables for credentials
   - Clear sensitive environment variables

5. **Testing**

   - Test configuration settings for your environment
   - Verify output formats work for your use case
   - Test logging configuration

Configuration Templates
-----------------------

Basic Template
^^^^^^^^^^^^^^

.. code-block:: toml

    # .rstbuddy.toml.template
    # Documentation settings
    documentation_dir = "doc/source"

    # Output settings
    default_output_format = "table"
    enable_colors = true
    quiet_mode = false

    # Logging settings
    log_level = "INFO"
    log_file = null

AI Summarization Template
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: toml

    # ai-summarization.toml
    # OpenAI API key (required for AI summarization)
    openai_api_key = "sk-your-api-key-here"

    # Documentation settings
    documentation_dir = "docs"

    # Output settings
    default_output_format = "table"
    enable_colors = true

    # Logging settings
    log_level = "INFO"