Coding Standards
================

This guide outlines the coding standards and best practices for contributing to the rstbuddy project.

Code Style
----------

**Python Code Style**
    - Follow PEP 8 style guidelines
    - Use 4 spaces for indentation (no tabs)
    - Maximum line length of 88 characters (Black formatter)
    - Use descriptive variable and function names
    - Include type hints for all function parameters and return values

**Import Organization**
    - Group imports: standard library, third-party, local
    - Use absolute imports for local modules
    - Avoid wildcard imports
    - Sort imports alphabetically within groups

**Documentation**
    - Use Google-style docstrings for all public functions and classes
    - Include type information in docstrings
    - Provide examples for complex functions
    - Document exceptions that may be raised

Example Code Style
^^^^^^^^^^^^^^^^^^

.. code-block:: python

    """Convert Markdown headings to RST format.

    Args:
        lines: List of input lines to process.

    Returns:
        Tuple of (processed_lines, conversion_count).

    Raises:
        ValueError: If heading format is invalid.
    """
    def convert_markdown_headings(lines: list[str]) -> tuple[list[str], int]:
        """Convert Markdown ATX headings to RST headings."""
        processed_lines = []
        conversion_count = 0

        for line in lines:
            if line.startswith('#'):
                # Process heading
                processed_line = _process_heading(line)
                processed_lines.append(processed_line)
                conversion_count += 1
            else:
                processed_lines.append(line)

        return processed_lines, conversion_count

Testing Standards
-----------------

**Test Coverage**
    - Aim for 90%+ code coverage
    - Test both success and failure cases
    - Include edge cases and boundary conditions
    - Mock external dependencies (HTTP requests, file system)

**Test Organization**
    - Use descriptive test method names
    - Group related tests in test classes
    - Use fixtures for common test data
    - Clean up test artifacts after each test

**Test Examples**
    - Test with realistic input data
    - Include both positive and negative test cases
    - Test error handling and edge cases
    - Verify output format and content

Example Test Structure
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    """Test RST link checking functionality."""

    import pytest
    from pathlib import Path
    from rstbuddy.services.rst_link_checker import RSTLinkChecker

    class TestRSTLinkChecker:
        """Test cases for RST link checker."""

        @pytest.fixture
        def temp_rst_file(self, tmp_path):
            """Create temporary RST file for testing."""
            rst_file = tmp_path / "test.rst"
            rst_file.write_text("Test content with :ref:`label`")
            return rst_file

        def test_check_links_finds_broken_refs(self, temp_rst_file):
            """Test that broken :ref: links are detected."""
            checker = RSTLinkChecker(temp_rst_file.parent)
            broken_links = checker.check()

            assert len(broken_links) == 1
            assert ":ref:`label`" in broken_links[0].link_text

Error Handling
--------------

**Exception Types**
    - Use specific exception types for different error conditions
    - Inherit from appropriate base exception classes
    - Include meaningful error messages
    - Provide context information when possible

**Error Messages**
    - Use clear, actionable error messages
    - Include relevant context (file paths, line numbers)
    - Suggest solutions when possible
    - Use consistent error message formatting

**Logging**
    - Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
    - Include relevant context in log messages
    - Use structured logging for complex data
    - Avoid logging sensitive information

Example Error Handling
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    """Handle configuration errors gracefully."""

    class ConfigurationError(Exception):
        """Raised when configuration is invalid or missing."""

        def __init__(self, message: str, config_file: Path | None = None):
            self.message = message
            self.config_file = config_file
            super().__init__(self._format_message())

        def _format_message(self) -> str:
            """Format error message with context."""
            if self.config_file:
                return f"Configuration error in {self.config_file}: {self.message}"
            return f"Configuration error: {self.message}"

Performance Considerations
--------------------------

**Efficiency**
    - Use appropriate data structures for the task
    - Avoid unnecessary object creation
    - Use generators for large datasets
    - Profile code for performance bottlenecks

**Memory Usage**
    - Process files line by line when possible
    - Use context managers for resource management
    - Avoid keeping large objects in memory
    - Use weak references when appropriate

**Concurrency**
    - Use ThreadPoolExecutor for I/O-bound operations
    - Implement proper error handling in concurrent code
    - Use appropriate worker counts for your environment
    - Consider async/await for complex I/O operations

Example Performance Optimization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    """Process files efficiently with generators."""

    def process_rst_files(directory: Path):
        """Process RST files without loading all content into memory."""
        for rst_file in directory.rglob("*.rst"):
            try:
                with rst_file.open(encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        yield process_line(line, rst_file, line_num)
            except OSError as e:
                logger.warning(f"Could not read {rst_file}: {e}")

Security Considerations
-----------------------

**Input Validation**
    - Validate all user input and file content
    - Sanitize file paths to prevent directory traversal
    - Use parameterized queries for database operations
    - Implement proper access controls

**File Operations**
    - Use safe file operations (avoid shell injection)
    - Validate file permissions before operations
    - Use temporary files for sensitive operations
    - Clean up temporary files after use

**API Security**
    - Never log or expose API keys
    - Use environment variables for sensitive configuration
    - Implement rate limiting for external API calls
    - Validate and sanitize all external data

Example Security Implementation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    """Safely handle file operations."""

    import tempfile
    import shutil
    from pathlib import Path

    def safe_file_operation(file_path: Path, operation_func):
        """Perform file operation with proper security checks."""
        # Validate file path
        if not file_path.is_file():
            raise ValueError(f"Invalid file path: {file_path}")

        # Use temporary file for operations
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            try:
                result = operation_func(file_path, temp_file.name)
                # Only replace original if operation succeeds
                shutil.move(temp_file.name, file_path)
                return result
            finally:
                # Clean up temp file
                if Path(temp_file.name).exists():
                    Path(temp_file.name).unlink()

Documentation Standards
-----------------------

**Code Documentation**
    - Document all public APIs
    - Include usage examples
    - Document exceptions and error conditions
    - Keep documentation up to date with code changes

**User Documentation**
    - Write clear, concise user guides
    - Include practical examples
    - Document common use cases
    - Provide troubleshooting information

**API Documentation**
    - Use consistent formatting for all API docs
    - Include parameter descriptions and types
    - Document return values and exceptions
    - Provide code examples for complex operations

Example API Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    """RST link checker service.

    This service provides comprehensive link validation for RST files,
    including external HTTP(S) links, Sphinx roles, and directive paths.

    Example:
        >>> checker = RSTLinkChecker(Path("docs"))
        >>> broken_links = checker.check()
        >>> for link in broken_links:
        ...     print(f"Broken link in {link.file_path}:{link.line_number}")
    """

    class RSTLinkChecker:
        """Scan RST files for broken links and validate them.

        Args:
            root: Directory to recursively scan for RST files.

        Attributes:
            root: Root directory for scanning.
            settings: Configuration settings.
        """

Commit Standards
----------------

**Commit Messages**
    - Use clear, descriptive commit messages
    - Start with a verb (Add, Fix, Update, Refactor)
    - Include brief description of changes
    - Reference issue numbers when applicable

**Commit Structure**
    - Make atomic commits (one logical change per commit)
    - Test changes before committing
    - Include tests for new functionality
    - Update documentation for API changes

**Branch Naming**
    - Use descriptive branch names
    - Include issue numbers in branch names
    - Use consistent naming conventions
    - Keep branches focused and short-lived

Example Commit Messages
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

    Add support for custom user agents in link checking

    - Add --user-agent command line option
    - Update RSTLinkChecker to use custom user agent
    - Add tests for user agent functionality
    - Update documentation with examples

    Fixes #123

Review Process
--------------

**Code Review Checklist**
    - Code follows style guidelines
    - Tests are included and pass
    - Documentation is updated
    - Error handling is appropriate
    - Performance considerations are addressed
    - Security implications are considered

**Review Comments**
    - Be constructive and specific
    - Suggest improvements when possible
    - Ask questions to understand intent
    - Focus on code quality and maintainability

**Review Process**
    - All code changes require review
    - Address all review comments
    - Request re-review for significant changes
    - Use pull request templates for consistency

Getting Help
------------

If you have questions about coding standards:

1. **Check Existing Code**: Look at similar functions in the codebase
2. **Review Style Guide**: Follow PEP 8 and project-specific guidelines
3. **Ask Questions**: Use GitHub discussions or issues
4. **Request Review**: Get feedback on your code early

**Resources**:
    - `PEP 8 Style Guide <https://peps.python.org/pep-0008/>`_
    - `Google Python Style Guide <https://google.github.io/styleguide/pyguide.html>`_
    - `Black Code Formatter <https://black.readthedocs.io/>`_
    - `MyPy Type Checker <https://mypy.readthedocs.io/>`_