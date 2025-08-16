Convert Outline Command Reference
=================================

This document provides detailed specifications for the ``rstbuddy outline-to-rst`` command,
including the exact markdown structure requirements, validation rules, and implementation details.

Command Overview
----------------

The ``outline-to-rst`` command converts a well-structured markdown outline into a complete
RST documentation project with proper Sphinx formatting, directory structure, and toctree entries.

.. code-block:: bash

    rstbuddy outline-to-rst <markdown_file> [options]

Required Arguments
------------------

**MARKDOWN_FILE**
    Path to the markdown file containing the document outline. The file must exist and be readable.

Command Options
---------------

**--output-dir PATH**
    Custom output directory for generated RST files. If not specified, uses the value of
    ``RSTBUDDY_DOCUMENTATION_DIR`` environment variable or the default documentation directory.

**--force**
    Force overwrite existing files. When specified, existing files are backed up with
    timestamped names (e.g., ``filename.20241201120000.bak``) before being overwritten.

**--dry-run**
    Preview what would be created without actually creating any files. Shows the planned
    directory structure and file operations.

Markdown Structure Requirements
-------------------------------

The markdown file must follow a strict hierarchical structure to be successfully converted.

Heading Hierarchy
^^^^^^^^^^^^^^^^^

The document must contain exactly three levels of headings:

1. **Level 1 (H1)**: Document title (must be the first heading)
2. **Level 2 (H2)**: Chapter headings
3. **Level 3 (H3)**: Section headings or content headings

Document Title (H1)
^^^^^^^^^^^^^^^^^^^

- **Must be the first heading** in the document
- **Must be level 1** (single # or equivalent)
- **Cannot be empty** or contain only whitespace
- **Used as the main title** in the generated top-level ``index.rst``

Example:
.. code-block:: markdown

    # My Documentation Project

Not recommended
^^^^^^^^^^^^^^^

- Don't use horizontal rules (``---``) in the outline at all, they confuse the parser.

Chapter Headings (H2)
^^^^^^^^^^^^^^^^^^^^^

Chapter headings must follow specific patterns and appear at level 2 (## or equivalent).

Valid Chapter Patterns
~~~~~~~~~~~~~~~~~~~~~~

**Prologue**
    Special chapter type for introductory content before the main chapters.

    - Pattern: ``## Prologue: Title``
    - Folder name: ``prologue``
    - RST title: ``Prologue: Title`` (prefix preserved)

**Introduction**
    Special chapter type for project introduction.

    - Pattern: ``## Introduction: Title``
    - Folder name: ``introduction``
    - RST title: ``Introduction: Title`` (prefix preserved)

**Numbered Chapters**
    Standard chapters with sequential numbering.

    - Pattern: ``## Chapter X: Title``
    - Folder name: ``chapterX`` (where X is the chapter number)
    - RST title: ``Title`` (number prefix removed)

**Appendix Chapters**
    Reference chapters with letter-based numbering.

    - Pattern: ``## Appendix X: Title``
    - Folder name: ``appendixX`` (where X is the appendix letter)
    - RST title: ``Title`` (appendix prefix removed)

Examples:
.. code-block:: markdown

    ## Prologue: Getting Started
    ## Introduction: How to use this book
    ## Chapter 1: Getting Started
    ## Chapter 2: Advanced Features
    ## Appendix A: Configuration Reference
    ## Appendix B: Troubleshooting Guide

Invalid Chapter Patterns
~~~~~~~~~~~~~~~~~~~~~~~~

The following patterns are **not allowed** and will cause validation errors:

- ``## Chapter`` (missing number and title)
- ``## Chapter 1`` (missing colon and title)
- ``## Chapter 1 Getting Started`` (missing colon)
- ``## Chapter A: Title`` (letters not allowed for numbered chapters)
- ``## Appendix 1: Title`` (numbers not allowed for appendix chapters)

Chapter-specific Content
^^^^^^^^^^^^^^^^^^^^^^^^

Sections live in chapters and appendices.

If you want to add content to the chapter page itself, do not use headings,
because it will screw up the Table of Contents, interspersing your bare headings
with the section headings.  Sphinx is very particular about how to order things
in the table of contents, and non-section headings (of any level H3 or below)
before Section titles (which are also H3s) will cause havoc in the top level
Table of Contents.

.. important::

    The only exception to this is if you have no sections in the chapter.  In that case,
    you can use headings in the chapter page itself.

Instead, to add content at the chapter level, just do it without headings:

.. code-block:: markdown

    ## Chapter 1: Getting Started

    This is the chapter content. This will appear in the chapter's `index.rst` file.

    **Subsection of Chapter 1 that is not a heading**

    - This is the subsection content. This will appear in the chapter's `index.rst` file.

    ### 1.1 Installation

    This is the installation **section**. This will be in its own file, `chapter1/installation.rst`.

    #### Subsection of Installation

    This is the subsection content. This will appear in the `chapter1/installation.rst` file.

    ### 1.1 Installation

    This is the installation **section**. This will be in its own file, `chapter1/installation.rst`.

    #### Subsection of Installation

    This is the subsection content. This will appear in the `chapter1/installation.rst` file.

Section Headings (H3)
^^^^^^^^^^^^^^^^^^^^^

Section headings appear at level 3 (### or equivalent) and can be either:

1. **Numbered Sections**: Get their own RST files
2. **Content Headings**: Treated as content within the parent chapter, if there are no numbered sections in the chapter.

**Important**: Section numbering is limited to a maximum of two levels for both chapters and appendices.

Numbered Sections
~~~~~~~~~~~~~~~~~

Numbered sections follow specific patterns and are converted to individual RST files.

**Regular Numbered Sections**

    - Pattern: ``### X.Y Title`` (where X and Y are numbers)
    - Filename: ``section-title.rst`` (sanitized)
    - RST title: ``Title`` (number prefix removed)
    - **Maximum nesting**: Two levels only (e.g., 1.1, 2.3, not 1.1.1)

**Appendix Numbered Sections**

    - Pattern: ``### D.1 Title`` (where D is a letter and 1 is a number)
    - Filename: ``section-title.rst`` (sanitized)
    - RST title: ``Title`` (letter and number prefix removed)
    - **Maximum nesting**: Two levels only (e.g., A.1, B.2, not A.1.1)

Examples:
.. code-block:: markdown

    ### 1.1 Installation
    ### 1.2 Configuration
    ### 2.1 Basic Usage
    ### 2.2 Advanced Features
    ### D.1 Environment Setup
    ### A.2 Troubleshooting

**Invalid Section Patterns** (will cause validation errors):

.. code-block:: markdown

    ### 1.1.1 Deep Subsection     # Too many levels
    ### 2.3.4.1 Very Deep         # Too many levels
    ### A.1.1 Deep Appendix       # Too many levels
    ### B.2.3.1 Very Deep         # Too many levels

Content Headings
~~~~~~~~~~~~~~~~

Content headings are H3 headings that don't follow the numbered section patterns.
These are treated as content within the parent chapter and do not get their own files.

.. important::

    If you have no numbered sections in the chapter, you can use content headings.
    **DO NOT USE THEM IF YOU HAVE SECTIONS**


Examples:
.. code-block:: markdown

    ### Summary
    ### Learning Objectives
    ### Key Points
    ### Example Types

Content Organization
--------------------

Content between headings is organized based on the heading hierarchy:

**Document Introduction**
    Content between the document title (H1) and the first chapter (H2) is placed
    in the top-level ``index.rst`` file before the table of contents.

**Chapter Content**
    Content between a chapter heading (H2) and the next heading of the same or higher level
    is placed in the chapter's ``index.rst`` file.

**Section Content**
    Content between a numbered section heading (H3) and the next heading of the same or higher level
    is placed in the individual section RST file.

**Content Heading Content**
    Content under content headings (non-numbered H3) is included in the parent chapter's
    ``index.rst`` file.

Example Structure
^^^^^^^^^^^^^^^^^

.. code-block:: markdown

    # My Project Documentation

    This is the introduction content that goes in the top-level index.rst.

    ### Summary

    This content goes in index.rst (not a separate file).

    ## Chapter 1: Getting Started

    This content goes in chapter1/index.rst.

    ### Summary

    This content goes in chapter1/index.rst (not a separate file).

    ### 1.1 Installation

    This content goes in chapter1/installation.rst.

    #### Summary

    This content goes in chapter1/installation.rst (not a separate file).

    ### 1.2 Configuration

    This content goes in chapter1/configuration.rst.

    ## Chapter 2: Advanced Features

    This content goes in chapter2/index.rst.


Generated RST Structure
-----------------------

The command generates a complete RST documentation structure:

Top-Level Files
^^^^^^^^^^^^^^^

**``index.rst``**

    - Document title (from H1 heading)
    - Introduction content (between H1 and first H2)
    - Table of contents with links to all chapters
    - Uses ``.. toctree::`` directive with ``:hidden:`` option
    - Separate ``.. toctree::`` for appendices with ``:caption: Appendices``

The top-level index.rst file creates a clean separation between front matter, chapters, and appendices:

.. code-block:: rst

    .. toctree::
       :caption: Front Matter
       :hidden:

       prologue/index
       introduction/index

    .. toctree::
       :caption: Chapters
       :hidden:

       chapter1/index
       chapter2/index

    .. toctree::
       :caption: Appendices
       :hidden:

       appendixA/index
       appendixB/index

This structure provides better organization and makes it easier for readers to navigate between:
- **Front Matter**: Introduction and Prologue sections
- **Chapters**: Main numbered chapters
- **Appendices**: Reference materials and additional resources

**Important**: Toctree entries are only created when there are actually chapters of those types. For example:
- A book with only chapters will have just one toctree with `:caption: Chapters`
- A book with only front matter will have just one toctree with `:caption: Front Matter`
- A book with only appendices will have just one toctree with `:caption: Appendices`
- A book with all three types will have three separate toctrees

Chapter Files
^^^^^^^^^^^^^

**``chapterX/index.rst``** (for each chapter)

    - Chapter title (cleaned, without prefix)
    - Chapter content (between H2 and next H2/H1)
    - Table of contents for numbered sections
    - Uses ``.. toctree::`` directive with ``:hidden:`` option

**``appendixX/index.rst``** (for each appendix)

    - Appendix title (cleaned, without prefix)
    - Appendix content (between H2 and next H2/H1)
    - Table of contents for numbered sections
    - Uses ``.. toctree::`` directive with ``:hidden:`` option

Section Files
^^^^^^^^^^^^^

**``section-title.rst``** (for each numbered section)

    - Section title (cleaned, without number prefix)
    - Section content (between H3 and next H3/H2/H1)

Content Processing
------------------

Content Conversion
^^^^^^^^^^^^^^^^^^

All markdown content is converted to RST using Pandoc:

1. **Temporary Files**: Content is written to temporary markdown files
2. **Pandoc Conversion**: Pandoc converts markdown to RST format
3. **Content Caching**: Results are cached to ensure consistent output
4. **Error Handling**: If Pandoc fails, the command exits with helpful error messages

Content Filtering
^^^^^^^^^^^^^^^^^

To avoid duplicate headings, the original markdown headings are filtered out:

1. **Chapter Headings**: Removed from chapter content to prevent duplication
2. **Section Headings**: Removed from section content to prevent duplication
3. **Smart Matching**: Handles various heading formats and partial matches

Filename Sanitization
^^^^^^^^^^^^^^^^^^^^^

Section titles are converted to safe filenames:

1. **Character Replacement**: Special characters are replaced or removed
2. **Extension Addition**: ``.rst`` extension is added
3. **Uniqueness**: Ensures no filename conflicts within a chapter

Validation Rules
----------------

The command performs comprehensive validation before conversion:

Structure Validation
^^^^^^^^^^^^^^^^^^^^

1. **Document Title**: Must have exactly one H1 heading at the beginning
2. **Heading Hierarchy**: No skipping of heading levels allowed
3. **Chapter Patterns**: All H2 headings must match valid chapter patterns
4. **Section Patterns**: All H3 headings must either be numbered sections or content headings
5. **Nesting Limitation**: Section numbering is limited to maximum of two levels (e.g., 1.1, A.1, not 1.1.1, A.1.1)

Content Validation
^^^^^^^^^^^^^^^^^^

1. **Markdown Syntax**: Basic markdown syntax is validated
2. **Deep Nesting Detection**: Scans for section numbering with more than two levels
3. **File Accessibility**: Input file must be readable
4. **Output Directory**: Output directory must be writable (if not using --dry-run)

Error Handling
--------------

The command provides clear error messages for common issues:

**Pandoc Not Found**

    - Error: "Pandoc is not installed or not found in PATH"
    - Solution: Install Pandoc from https://pandoc.org/installing.html
    - Includes OS-specific installation instructions

**Invalid Structure**

    - Error: "Invalid chapter heading: 'Invalid Heading'"
    - Solution: Fix heading format to match required patterns

**Deep Nesting Violations**

    - Error: "Section numbering '1.1.1' exceeds maximum of two levels. Use format 'X.Y' instead of 'X.Y.Z'"
    - Error: "Appendix section numbering 'A.1.1' exceeds maximum of two levels. Use format 'X.Y' instead of 'X.Y.Z'"
    - Solution: Restructure sections to use only two levels (e.g., 1.1, 2.3, A.1, B.2)
    - Alternative: Convert deep subsections to content headings (e.g., ### Deep Subsection)

**File Permission Issues**

    - Error: "Failed to create temporary file: Permission denied"
    - Solution: Check file and directory permissions

**Existing Directory Conflicts**

    - Error: "Output directory already exists. Use --force to overwrite"
    - Solution: Use --force flag or choose different output directory

Backup Strategy
---------------

When ``--force`` is specified, the command implements a smart backup strategy:

1. **File-Level Backups**: Only backs up files that will be modified
2. **Timestamped Names**: Backup files use format: ``filename.YYYYMMDD_HHMMSS.bak``
3. **Content Comparison**: Only writes files if content has actually changed
4. **Preservation**: Existing files are preserved with backup copies

Example Backup Names:
- ``index.rst.20241201_143022.bak``
- ``chapter1.rst.20241201_143023.bak``

Performance Considerations
--------------------------

1. **Content Caching**: Pandoc conversion results are cached in memory
2. **Smart File Writing**: Files are only written if content differs
3. **Efficient Parsing**: Single-pass parsing of markdown content
4. **Minimal I/O**: Temporary files are used only when necessary

Limitations
-----------

1. **Pandoc Dependency**: Requires Pandoc to be installed and accessible
2. **Structure Requirements**: Markdown must follow strict heading hierarchy
3. **Content Conversion**: Complex markdown constructs may not convert perfectly
4. **File System**: Requires write access to output directory

Best Practices
--------------

1. **Use --dry-run first**: Always preview the structure before conversion
2. **Validate structure**: Ensure your markdown follows the required patterns
3. **Test builds**: Verify that generated RST builds correctly with Sphinx
4. **Backup existing**: Use --force to create backups of existing content
5. **Review output**: Check generated files for accuracy and completeness

Troubleshooting
---------------

Common Issues and Solutions:

**"Invalid chapter heading" errors**

    - Check that all H2 headings follow the required patterns
    - Ensure proper spacing around colons in "Chapter X: Title" format

**"Pandoc conversion failed" errors**

    - Verify Pandoc is installed and in PATH
    - Check that markdown content is valid
    - Ensure sufficient disk space for temporary files

**"Output directory already exists" errors**

    - Use --force flag to overwrite with backups
    - Choose different output directory with --output-dir
    - Manually remove or rename existing directory

**Generated files missing content**

    - Check that content headings (non-numbered H3) are properly formatted
    - Ensure content is placed between appropriate headings
    - Verify that numbered sections have proper number prefixes
