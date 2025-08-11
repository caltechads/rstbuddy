Quickstart Guide
================

This guide will get you up and running with ``rstbuddy`` quickly, showing both
the Python client and command-line interface.

Prerequisites
-------------

- Python 3.10 or higher
- Follow the :doc:`/overview/installation` instructions to install ``rstbuddy``
- Other prerequisites here

Configuration
-------------

Typically the defaults that ship with ``rstbuddy``
will work. If you need to change those defaults, you can create a configuration
file at ``~/.rstbuddy.conf``:

You can configure ``rstbuddy`` using configuration
files or environment variables. See :doc:`/overview/configuration` for more
details.

Basic Usage
-----------

Get Help
^^^^^^^^

.. code-block:: bash

    # Show main help
    rstbuddy --help

    # Show help for specific command groups
    rstbuddy group1 --help
    rstbuddy group2 --help
    rstbuddy group3 --help
    rstbuddy settings --help

Feature 1 Usage
^^^^^^^^^^^^^^^

.. code-block:: bash

    # List all features
    rstbuddy group1 feature1

    # Filter services by pattern
    rstbuddy group1 feature1 --arg "foo" --arg "bar"


Feature 2 Usage
^^^^^^^^^^^^^^^

.. code-block:: bash

    # List all features
    rstbuddy group2 feature2

    # Filter services by pattern
    rstbuddy group2 feature2 --arg "foo" --arg "bar"

Output Formats
^^^^^^^^^^^^^^

.. code-block:: bash

    # Use table format (default) for human reading
    rstbuddy group1 feature1 --output table

    # Use JSON format for scripting
    rstbuddy group1 feature1 --output json

    # Use text format for simple output
    rstbuddy group1 feature1 --output text

    # Use text format for settings
    rstbuddy group1 feature1 --output text settings

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