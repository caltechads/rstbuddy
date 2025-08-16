========
rstbuddy
========

.. toctree::
   :maxdepth: 2
   :caption: Getting Started
   :hidden:

   overview/installation
   overview/quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide
   :hidden:

   overview/usage
   overview/configuration
   overview/faq

.. toctree::
   :maxdepth: 2
   :caption: Development
   :hidden:

   runbook/contributing
   runbook/coding_standards

.. toctree::
   :maxdepth: 2
   :caption: Reference
   :hidden:

   changelog
   reference/convert-outline

Current version is |release|.

``rstbuddy`` is a Python command-line tool for working with reStructuredText (RST) files.
It provides comprehensive link validation, RST file cleaning and fixing, and optional AI-powered
summarization capabilities.

Related packages
----------------

- `restructuredtext-lint <https://pypi.org/project/restructuredtext-lint/>`_:
   This seems to be for when you want to write your README in RestructuredText, and
   want to ensure that PyPI will process it properly for you without errors.  So it
   has a bunch of thing in it that we don't need or want necessarily since we're primarily concerned
   with fixing AI assistant errors in generated or modified .rst files before uploading to
   [readthedocs](https://readthedocs.org), but definitely check it out.  Note that
   it is a **linter**, not a **fixer** like this package is.


Core Features
-------------

rstbuddy provides the following key features:

**RST Link Checking**
    - **External HTTP(S) Links**: Validate external URLs with concurrent checking and robots.txt support
    - **Sphinx :ref: Roles**: Verify that referenced labels exist as explicit ``.. _label:`` declarations
    - **Sphinx :doc: Roles**: Resolve document references and validate target file existence
    - **Directive Paths**: Check include, literalinclude, download, image, figure, and thumbnail directives
    - **Smart Scanning**: Ignores links inside code blocks and code-like directives while preserving admonitions

**RST File Cleaning & Fixing**
    - **Markdown Conversion**: Convert Markdown constructs (sometimes left by AI assistants) (``#``, ``##``, ``###``) to RST format
    - **Heading Normalization**: Fix RST heading underlines to match title length exactly
    - **Code Block Conversion**: Transform fenced Markdown code blocks to RST code-block directives
    - **Inline Code Spans**: Convert single-backtick spans to RST inline literals
    - **List Spacing**: Ensure proper blank lines after list blocks
    - **Stray Markdown Fence Removal**: Clean up orphaned triple backticks

**Outline Conversion**
    - **Markdown to RST Structure**: Convert well-structured markdown outlines into complete RST documentation projects
    - **Automatic File Generation**: Create chapter directories, index files, and section files with proper Sphinx toctree entries
    - **Content Validation**: Validate outline structure and heading hierarchy before conversion
    - **Smart Content Handling**: Distinguish between numbered sections and content headings
    - **Pandoc Integration**: Use Pandoc for high-quality markdown-to-RST content conversion

**AI-Powered Summarization** (Optional)
    - **RST to Markdown Conversion**: Convert RST files to Markdown using Pandoc
    - **AI Summary Generation**: Generate intelligent summaries using OpenAI's API
    - **Requires OpenAI API Key**: Must be configured separately to enable this feature

Getting Started
---------------

To get started with rstbuddy:

1. **Installation**: Follow the :doc:`/overview/installation` guide
2. **Quick Start**: See the :doc:`/overview/quickstart` guide for basic usage
3. **Usage Guide**: Learn about commands and options in :doc:`/overview/usage`
4. **Configuration**: Learn about configuration options in :doc:`/overview/configuration`
5. **FAQ**: Check the :doc:`/overview/faq` section for common questions and troubleshooting

For developers, see the :doc:`/runbook/contributing` and :doc:`/runbook/coding_standards` guides.

Supported RST Constructs
------------------------

rstbuddy helps you maintain your RST documentation by:

**Checking Links for valid paths/references/URLs**
    - External HTTP(S) URLs
    - Sphinx cross-references (``:ref:`label```)
    - Document references (``:doc:`path```)
    - Include directives (``.. include:: file``)
    - Code inclusion (``.. literalinclude:: file``)
    - Download links (``.. download:: file``)
    - Image references (``.. image:: file``)
    - Figure directives (``.. figure:: file``)
    - Thumbnail directives (``.. thumbnail:: file``)

**Fixing Improperly Formatted RST Elements**
    - Section headings with underlines
    - Code blocks and inline code
    - Lists (bulleted and numbered)
    - Admonitions (note, warning, important, etc.)
    - Directives and their content

**Converting inline Markdown to RST**

    AI generated RST will sometimes contain markdown constructs that need to be converted to RST.
    rstbuddy will convert the following markdown constructs to RST:

    - ATX headings (``#``, ``##``, ``###``) → RST headings
    - Markdown fenced code blocks → RST code-block directives
    - Inline code → RST inline literals

Requirements
------------

- Python 3.11 or later
- (optional) Pandoc (for AI summarization feature)
- (optional) OpenAI API key (for AI summarization feature)

Common Use Cases
----------------

**Documentation Maintenance**
    - Validate all links in RST documentation before publishing
    - Fix formatting issues in existing RST files
    - Convert Markdown files to RST format
    - Ensure consistent heading structure

**Quality Assurance**
    - Check for broken internal references
    - Validate external links are accessible
    - Maintain consistent RST formatting
    - Generate documentation summaries

**Content Migration**
    - Convert Markdown documentation to RST
    - Fix common RST formatting issues
    - Normalize heading structures
    - Clean up code block formatting