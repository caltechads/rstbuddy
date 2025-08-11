Frequently Asked Questions
==========================

This section answers common questions about tfmate and provides solutions to frequently encountered issues.

General Questions
-----------------

What is rstbuddy?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

rstbuddy is a Python command-line tool designed for __FILL_ME_IN__. It provides capabilities for:

- Feature 1
- Feature 2

Installation Issues
-------------------

How do I install rstbuddy?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

See the :doc:`installation` guide for detailed installation instructions. The recommended methods are:

- Using ``uv tool``: ``uv tool install rstbuddy``
- Using ``pipx``: ``pipx install rstbuddy``
- Using ``pip``: ``pip install rstbuddy``
- From source: Clone the repository and run ``uv sync``

I get a "command not found" error after installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This usually means the installation directory is not in your PATH. Try:

1. Restart your terminal session
2. Check if the installation directory is in your PATH
3. For ``pipx`` installations, ensure ``pipx`` is in your PATH
4. For ``uv tool`` installations, ensure ``uv`` is properly configured

Usage Questions
---------------

How do I use feature 1?
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # List all features
    rstbuddy group1 feature1

    # Filter services by pattern
    rstbuddy group1 feature1 --arg "foo" --arg "bar"

Output and Formatting Issues
----------------------------

How do I change the output format?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the ``--output`` option:

.. code-block:: bash

    # JSON output
    rstbuddy --output json group1 feature1

    # Table output (default)
    rstbuddy --output table group1 feature1

    # Text output
    rstbuddy --output text group1 feature1

The output format applies to all commands in the session.

How do I enable verbose output?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the ``--verbose`` option:

.. code-block:: bash

    # Enable verbose output
    rstbuddy --verbose group1 feature1

    # Verbose output with specific command
    rstbuddy --verbose group1 feature1

Verbose output shows additional details about:

- Details 1
- Details 2

How do I suppress output except errors?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the ``--quiet`` option:

.. code-block:: bash

    # Suppress all output except errors
    rstbuddy --quiet group1 feature1

This is useful in scripts where you only want to see error messages.

Configuration Issues
--------------------

How do I use a custom configuration file?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the ``--config-file`` option:

.. code-block:: bash

    # Use custom configuration file
    rstbuddy --config-file /path/to/config.toml group1 feature1

The configuration file should be in TOML format. See the :doc:`configuration` guide for details.

What configuration options are available?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tfmate supports configuration for:

- Configuration thing 1
- Configuration thing 2

See the :doc:`configuration` guide for a complete list of options.

Troubleshooting
---------------

Problem 1
^^^^^^^^^

This can happen due to:

1. **Network latency**: Feature 1 depends on network speed
3. **Cold Feature 1 requests**: First access to Feature 1 objects may be slower

Solutions:

.. code-block:: bash

    # Use verbose mode to see timing information
    rstbuddy --verbose group1 feature1

Performance and Limitations
---------------------------

What are the performance characteristics?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Feature 1**: Feature 1 depends on network speed
- **Feature 2**: Feature 2 depends on # sloths in Africa

Are there any limitations?
^^^^^^^^^^^^^^^^^^^^^^^^^^

- Limitation 1
- Limitation 2

Can I use rstbuddy in CI/CD pipelines?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes, rstbuddy is designed to work in CI/CD environments:

.. code-block:: yaml

    # Example configuration for various CI/CD providers


Getting Help
------------

Where can I get more help?
^^^^^^^^^^^^^^^^^^^^^^^^^^

1. **Documentation**: Check the other sections of this documentation
2. **Command help**: Use ``rstbuddy --help`` or ``rstbuddy <command> --help``
3. **Verbose mode**: Use ``--verbose`` for detailed error information
4. **GitHub issues**: Report bugs or request features on the project repository

How do I report a bug?
^^^^^^^^^^^^^^^^^^^^^^

When reporting a bug, please include:

1. **Command used**: The exact command that failed
2. **Error message**: The complete error output
3. **Environment**: OS, Python version, tfmate version
6. **Verbose output**: Use ``--verbose`` and include the output

Example bug report:

.. code-block:: text

    Command: rstbuddy group1 feature1 --arg "foo" --arg "bar"
    Error: Feature 1 error
    OS: macOS 14.0
    Python: 3.11.9
    rstbuddy: 0.1.0

    Verbose output:
    [Include verbose output here]