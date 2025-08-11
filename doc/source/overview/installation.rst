Installation
============

This guide covers how to install the ``rstbuddy`` package and its dependencies.

Prerequisites
-------------

Before installing ``rstbuddy``, ensure you have:

- Python 3.10 or higher
- `uv <https://docs.astral.sh/uv/>`_, `pip <https://pip.pypa.io/en/stable/>`_, or `pipx <https://pipx.pypa.io/stable/>`_

Installation Methods
--------------------

From PyPI with ``pip``
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    pip install rstbuddy
    rstbuddy --help


From PyPI with ``uv``
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    sh -c "$(curl -fsSL https://astral.sh/uv/install)"
    uv tool install rstbuddy
    # Ensure you have ./local/bin in your PATH, since that's where uv puts the
    # executable
    rstbuddy --help

From PyPI with ``pipx``
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    pipx install rstbuddy
    rstbuddy --help


From Source
^^^^^^^^^^^

If you want to install from the latest development version:

.. code-block:: bash

    git clone https://github.com/caltechads/rstbuddy.git
    sh -c "$(curl -fsSL https://astral.sh/uv/install)"
    cd rstbuddy
    uv tool install .

Verification
------------

After installation, verify that ``rstbuddy`` is properly installed:

.. code-block:: shell

    rstbuddy --help


Configuration
-------------

After installation, you may want to configure ``rstbuddy`` for your specific
environment.  See :doc:`configuration` for detailed configuration options.

Getting Help
------------

If you encounter issues during installation:

1. Check the `GitHub issues <https://github.com/caltechads/rstbuddy/issues>`_
2. Review the troubleshooting section above
3. Ensure your Python environment meets the prerequisites
4. Try installing in a virtual environment to isolate dependencies