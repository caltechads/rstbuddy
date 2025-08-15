# rstbuddy

A Python command-line tool for working with reStructuredText (RST) files. Provides comprehensive link validation, RST file cleaning and fixing, and optional AI-powered summarization capabilities.

## Related packages

- [restructuredtext-lint](https://pypi.org/project/restructuredtext-lint/): This seems to be for when you want to write your README in RestructuredText, and want to ensure that PyPI will process it properly for you without errors.  So it has a bunch of thing in it that we don't need for uploading to [readthedocs](https://readthedocs.org), but definitely check it out.  Note that it is a **linter**, not a **fixer** like this package is.

## Core Features

### RST Link Checking

- External HTTP(S) links with concurrent checking and robots.txt support
- Sphinx cross-references (`:ref:`, `:doc:`)
- Directive paths (include, literalinclude, download, image, figure, thumbnail)
- Smart scanning that ignores code blocks while preserving admonitions

### RST File Cleaning & Fixing

- Markdown to RST conversion (headings, code blocks, inline code)
- Heading normalization and list spacing fixes
- Code block and directive formatting
- Stray Markdown fence removal

### AI-Powered Summarization (Optional)

- RST to Markdown conversion using Pandoc
- AI summary generation with OpenAI API
- Requires OpenAI API key configuration

## Quick Start

## Requirements

- Python 3.11 or later
- Pandoc (optional, for AI summarization)
- OpenAI API key (optional, for AI summarization)

### Installation

```bash
# Install
pip install rstbuddy

# With uv
uv tool -p 3.13 install rstbuddy
```

### Usage

```bash
# Check all links in default doc/source directory
rstbuddy check-links

# Fix formatting issues in an RST file
rstbuddy fix document.rst

# Generate AI summary (requires OpenAI API key)
rstbuddy summarize document.rst

# Show help
rstbuddy --help
```

## Commands

- **`check-links`**: Validate external URLs, internal references, and file paths
- **`fix`**: Clean and fix RST formatting issues, convert Markdown constructs
- **`summarize`**: Generate AI-powered summaries (requires OpenAI API key)
- **`settings`**: Display current configuration settings
- **`version`**: Display version info for important packages used by `rstbuddy` (for bug reports)

## Common Use Cases

- **Documentation Maintenance**: Validate links and fix formatting before publishing
- **Quality Assurance**: Check for broken references and maintain consistent RST formatting
- **Content Migration**: Convert Markdown to RST and fix common formatting issues

## Documentation

For detailed usage, configuration, and troubleshooting, see the [full documentation](https://rstbuddy.readthedocs.org).
