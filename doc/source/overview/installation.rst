Installation Guide
==================

This guide covers installing ``rstbuddy`` on different platforms and systems.

Prerequisites
-------------

**System Requirements**
    - Python 3.10 or higher
    - pip, pipx, or uv package manager
    - Internet connection for package downloads

**Optional Dependencies**
    - **Pandoc**: Required only for AI summarization feature
    - **OpenAI API Key**: Required only for AI summarization feature

Installation Methods
--------------------

Using uv (Recommended)
^^^^^^^^^^^^^^^^^^^^^^

`uv <https://docs.astral.sh/uv/>`_ is a fast Python package installer and resolver.

**Install uv**:
    .. code-block:: bash

        # macOS/Linux
        curl -LsSf https://astral.sh/uv/install.sh | sh

        # Windows
        powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

**Install rstbuddy**:
    .. code-block:: bash

        # Install globally
        uv tool install rstbuddy

        # Verify installation
        rstbuddy --version

Using pipx
^^^^^^^^^^

`pipx <https://pypa.github.io/pipx/>`_ installs Python applications in isolated environments.

**Install pipx**:
    .. code-block:: bash

        # macOS
        brew install pipx
        pipx ensurepath

        # Ubuntu/Debian
        sudo apt update
        sudo apt install pipx
        pipx ensurepath

        # Windows
        python -m pip install --user pipx
        python -m pipx ensurepath

**Install rstbuddy**:
    .. code-block:: bash

        # Install globally
        pipx install rstbuddy

        # Verify installation
        rstbuddy --version

Using pip
^^^^^^^^^

Standard pip installation (not recommended for command-line tools).

**Install rstbuddy**:
    .. code-block:: bash

        # Install globally (requires sudo on Unix-like systems)
        pip install rstbuddy

        # Install for current user only
        pip install --user rstbuddy

        # Verify installation
        rstbuddy --version

From Source
^^^^^^^^^^^

Build and install from the source code.

**Clone and Install**:
    .. code-block:: bash

        # Clone the repository
        git clone https://github.com/your-org/rstbuddy.git
        cd rstbuddy

        # Install in development mode
        uv sync
        uv run pip install -e .

        # Or using pip
        pip install -e .

Verification
------------

After installation, verify that rstbuddy is working correctly:

.. code-block:: bash

    # Check version
    rstbuddy --version

    # Show help
    rstbuddy --help

    # Show settings
    rstbuddy settings

Expected output for version command:

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

Optional Dependencies
---------------------

Pandoc Installation
^^^^^^^^^^^^^^^^^^^

Required only for the AI summarization feature.

**macOS**:
    .. code-block:: bash

        # Using Homebrew
        brew install pandoc

        # Verify installation
        pandoc --version

**Ubuntu/Debian**:
    .. code-block:: bash

        # Using apt
        sudo apt update
        sudo apt install pandoc

        # Verify installation
        pandoc --version

**Windows**:
    - Download installer from https://pandoc.org/installing.html
    - Run the installer and follow the prompts
    - Restart your terminal after installation

**Verify Pandoc**:
    .. code-block:: bash

        # Check if pandoc is available
        pandoc --version

        # Check if it's in PATH
        which pandoc  # Unix-like systems
        where pandoc  # Windows

OpenAI API Key Setup
^^^^^^^^^^^^^^^^^^^^

Required only for the AI summarization feature.

**Get API Key**:
    1. Sign up at https://platform.openai.com/
    2. Navigate to API Keys section
    3. Create a new API key
    4. Copy the key (starts with "sk-")

**Configure API Key**:
    .. code-block:: bash

        # Set as environment variable
        export RSTBUDDY_OPENAI_API_KEY="sk-your-actual-api-key-here"

        # Or add to configuration file
        echo 'openai_api_key = "sk-your-actual-api-key-here"' >> ~/.config/.rstbuddy.toml

**Verify Configuration**:
    .. code-block:: bash

        # Check if API key is loaded
        rstbuddy settings | grep openai_api_key

Platform-Specific Instructions
------------------------------

macOS
^^^^^

**Using Homebrew**:
    .. code-block:: bash

        # Install Python if needed
        brew install python@3.11

        # Install rstbuddy
        brew install rstbuddy

        # Or use uv (recommended)
        curl -LsSf https://astral.sh/uv/install.sh | sh
        uv tool install rstbuddy

**Using MacPorts**:
    .. code-block:: bash

        # Install Python if needed
        sudo port install python311

        # Install rstbuddy
        sudo port install rstbuddy

Linux (Ubuntu/Debian)
^^^^^^^^^^^^^^^^^^^^^

**System Packages**:
    .. code-block:: bash

        # Update package list
        sudo apt update

        # Install Python if needed
        sudo apt install python3 python3-pip python3-venv

        # Install rstbuddy
        pip3 install --user rstbuddy

        # Add to PATH if needed
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        source ~/.bashrc

**Using uv (Recommended)**:
    .. code-block:: bash

        # Install uv
        curl -LsSf https://astral.sh/uv/install.sh | sh

        # Add to PATH
        echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
        source ~/.bashrc

        # Install rstbuddy
        uv tool install rstbuddy

Linux (CentOS/RHEL/Fedora)
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Using dnf/yum**:
    .. code-block:: bash

        # Install Python if needed
        sudo dnf install python3 python3-pip

        # Install rstbuddy
        pip3 install --user rstbuddy

**Using uv (Recommended)**:
    .. code-block:: bash

        # Install uv
        curl -LsSf https://astral.sh/uv/install.sh | sh

        # Install rstbuddy
        uv tool install rstbuddy

Windows
^^^^^^^

**Using pip**:
    .. code-block:: bash

        # Install Python from https://python.org
        # Ensure "Add Python to PATH" is checked during installation

        # Open Command Prompt or PowerShell
        pip install rstbuddy

        # Verify installation
        rstbuddy --version

**Using uv (Recommended)**:
    .. code-block:: powershell

        # Install uv using PowerShell
        irm https://astral.sh/uv/install.ps1 | iex

        # Restart PowerShell, then install rstbuddy
        uv tool install rstbuddy

**Using Chocolatey**:
    .. code-block:: powershell

        # Install Chocolatey first, then:
        choco install rstbuddy

**Using Scoop**:
    .. code-block:: powershell

        # Install Scoop first, then:
        scoop install rstbuddy


Troubleshooting
---------------

Installation Issues
^^^^^^^^^^^^^^^^^^^

**"command not found" after installation**:
    .. code-block:: bash

        # Check if rstbuddy is in PATH
        which rstbuddy

        # Check installation location
        pip show rstbuddy

        # Add to PATH if needed
        export PATH="$HOME/.local/bin:$PATH"

**Permission denied errors**:
    .. code-block:: bash

        # Install for current user only
        pip install --user rstbuddy

        # Or use virtual environment
        python -m venv rstbuddy-env
        source rstbuddy-env/bin/activate
        pip install rstbuddy

**Python version issues**:
    .. code-block:: bash

        # Check Python version
        python3 --version

        # Ensure Python 3.10+ is installed
        # Use pyenv or similar to manage Python versions

**Package conflicts**:
    .. code-block:: bash

        # Use virtual environment
        python -m venv rstbuddy-env
        source rstbuddy-env/bin/activate
        pip install rstbuddy

        # Or use uv for better dependency resolution
        uv tool install rstbuddy

Verification Issues
^^^^^^^^^^^^^^^^^^^

**Version command fails**:
    .. code-block:: bash

        # Check if rstbuddy is properly installed
        pip list | grep rstbuddy

        # Try running with Python module syntax
        python -m rstbuddy --version

        # Check for import errors
        python -c "import rstbuddy; print(rstbuddy.__version__)"

**Settings command fails**:
    .. code-block:: bash

        # Check configuration file permissions
        ls -la ~/.config/.rstbuddy.toml

        # Try with verbose output
        rstbuddy --verbose settings

        # Check for configuration errors
        rstbuddy --config-file /dev/null settings

Getting Help
------------

If you encounter installation issues:

1. **Check Prerequisites**: Ensure Python 3.10+ is installed
2. **Verify PATH**: Ensure installation directory is in your PATH
3. **Check Permissions**: Ensure you have write permissions for installation
4. **Use Virtual Environment**: Isolate dependencies to avoid conflicts
5. **Try Alternative Methods**: Use uv or pipx instead of pip
6. **Report Issues**: Open an issue on GitHub with detailed error information

**Useful Commands**:
    .. code-block:: bash

        # Check Python version
        python3 --version

        # Check pip version
        pip --version

        # Check PATH
        echo $PATH

        # Check installation location
        pip show rstbuddy

        # Check for conflicts
        pip check