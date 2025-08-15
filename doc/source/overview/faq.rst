Frequently Asked Questions
==========================

This section addresses common questions and troubleshooting scenarios for ``rstbuddy``.

Link Checking
-------------

Why are some links showing as broken when they work in my browser?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is a common issue caused by several factors:

**Web Application Firewalls (WAF)**

    - **Cloudflare**: Often blocks automated tools and bots
    - **AWS WAF**: May have rate limiting or user-agent filtering
    - **Custom WAFs**: May block requests that don't look like human browsers

**Rate Limiting**

    - Some servers limit requests from the same IP address
    - Multiple concurrent requests may trigger temporary blocks
    - Servers may have different limits for different user agents

**User-Agent Filtering**

    - Some sites reject requests with certain user agents
    - The default user agent ``rstbuddy-linkcheck/1.0`` may be blocked
    - Some sites only allow requests from major browsers

**Solutions**:

    - **Manual Verification**: Always check broken links manually in a browser
    - **Custom User-Agent**: Use ``--user-agent "Mozilla/5.0..."`` to mimic a browser
    - **Rate Limiting**: Increase ``--timeout`` and reduce ``--max-workers``
    - **Skip Domains**: Add problematic domains to ``check_rst_links_skip_domains``

How can I tell if a link is actually broken or just blocked?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Check the Error Details**:

    - **HTTP 403/429**: Usually indicates blocking (WAF, rate limiting)
    - **HTTP 5xx**: Server errors (may be temporary)
    - **Connection Timeout**: Network issues or blocking
    - **DNS Resolution Failure**: Link is actually broken

**Manual Verification Steps**:

    1. Copy the URL and paste it in a browser
    2. Try different browsers (Chrome, Firefox, Safari)
    3. Check if the site has a status page
    4. Try accessing from a different network
    5. Check if the site requires JavaScript or cookies

**Configuration Solutions**:

    - Add problematic domains to your configuration
    - Use longer timeouts for slow-responding sites
    - Skip robots.txt checks for problematic sites

What should I do about robots.txt violations?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Understanding robots.txt**:

    - The ``robots_disallowed`` flag indicates the site's robots.txt blocks your user agent
    - This doesn't necessarily mean the link is broken
    - It means the site doesn't want automated tools to access it

**Handling Options**:

    1. **Respect robots.txt** (default): Skip these links in future runs
    2. **Ignore robots.txt**: Use ``--no-check-robots`` flag
    3. **Custom User-Agent**: Use a user agent that's allowed by robots.txt
    4. **Manual Verification**: Check these links manually in a browser

**Best Practices**:

    - Respect robots.txt for production environments
    - Use ``--no-check-robots`` only for development/testing
    - Consider adding blocked domains to your skip list

RST File Cleaning
-----------------

Why isn't rstbuddy fixing my Markdown headings?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Common Causes**:
    - **Protected Content**: Lines match patterns in ``clean_rst_extra_protected_regexes``
    - **Directive Content**: Headings inside RST directives are protected
    - **Code Blocks**: Content inside fenced code blocks is ignored
    - **Invalid Syntax**: Markdown syntax doesn't match expected patterns

**Troubleshooting**:
    - Use ``--dry-run`` to see what would be changed
    - Check if headings are inside protected directives
    - Verify Markdown syntax is correct
    - Review your protected regex patterns

**Examples of Protected Content**:
    - Headings inside ``.. code-block::`` directives
    - Content matching custom protected patterns
    - Lines inside any RST directive content

How does rstbuddy decide what to fix?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Fix Priority Order**:
    1. **Code Block Conversion**: Convert Markdown fences to RST directives
    2. **Heading Conversion**: Convert Markdown ATX headings to RST
    3. **Heading Normalization**: Fix RST heading underlines
    4. **Inline Code**: Convert backtick spans to RST literals
    5. **List Spacing**: Ensure proper spacing around lists
    6. **Stray Fence Removal**: Clean up orphaned backticks

**Protection Rules**:

    - **Directives**: Content inside RST directives is protected
    - **Code Blocks**: Fenced code blocks are preserved
    - **Custom Patterns**: Lines matching protected regexes are ignored
    - **Admonitions**: Links inside admonitions are preserved

**Safety Features**:

    - Always creates backups before making changes
    - Uses conservative heuristics to avoid breaking content
    - Preserves RST-specific constructs
    - Ignores content that might be intentionally formatted

AI Summarization
----------------

Why do I get "OpenAI API key required" errors?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Common Causes**:

    - **No API Key**: API key not set in configuration or environment
    - **Invalid Key**: API key is malformed or expired
    - **Configuration Not Loaded**: Config file not found or not parsed
    - **Environment Variable**: API key not exported or cleared

**Setup Steps**:
    1. **Get API Key**: Sign up at https://platform.openai.com/
    2. **Set in Config**: Add to your configuration (see :doc:`/overview/configuration`)
    3. **Verify**: Run ``rstbuddy settings`` to check

**Configuration File Example**:
    .. code-block:: toml

        # ~/.config/.rstbuddy.toml
        openai_api_key = "sk-your-actual-api-key-here"

**Environment Variable Example**:
    .. code-block:: bash

        export RSTBUDDY_OPENAI_API_KEY="sk-your-actual-api-key-here"
        rstbuddy summarize document.rst

Why do I get "pandoc: command not found" errors?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Pandoc Requirement**:

    - The ``summarize`` command requires Pandoc to convert RST to Markdown
    - Pandoc is not included with rstbuddy
    - Must be installed separately on your system

**Installation Options**:

    - **macOS**: ``brew install pandoc``
    - **Ubuntu/Debian**: ``sudo apt install pandoc``
    - **Windows**: Download from https://pandoc.org/installing.html

**Verification**:
    .. code-block:: bash

        # Check if pandoc is installed
        pandoc --version

        # Check if it's in PATH
        which pandoc

Performance and Configuration
-----------------------------

Why is link checking so slow?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Common Bottlenecks**:

    - **Network Latency**: Slow response times from external sites
    - **Rate Limiting**: Servers throttling requests
    - **Large Documentation**: Many files or links to check
    - **Default Settings**: Conservative timeout and worker settings

**Optimization Options**:

    - **Increase Workers**: Use ``--max-workers 16`` or higher
    - **Reduce Timeout**: Use ``--timeout 3`` for faster failures
    - **Skip Domains**: Add slow sites to ``check_rst_links_skip_domains``
    - **Parallel Processing**: Link checking is already concurrent

**Performance Tips**:

    - Run during off-peak hours
    - Use appropriate worker counts for your network
    - Skip problematic domains
    - Consider running in CI/CD during quiet periods

How can I customize what gets checked or fixed?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Link Checking Customization**:

    - **Skip Domains**: Add to ``check_rst_links_skip_domains``
    - **Skip Directives**: Add to ``check_rst_links_extra_skip_directives``
    - **Custom User-Agent**: Use ``--user-agent`` flag
    - **Robots.txt**: Control with ``--no-check-robots``

**RST Cleaning Customization**:

    - **Protected Patterns**: Add regexes to ``clean_rst_extra_protected_regexes``
    - **Dry Run**: Use ``--dry-run`` to preview changes
    - **Selective Processing**: Process files individually

**Configuration Examples**:
    .. code-block:: toml

        # Skip problematic domains
        check_rst_links_skip_domains = [
            "cloudflare.com",
            "waf.example.com",
            "rate-limited.site"
        ]

        # Protect custom patterns
        clean_rst_extra_protected_regexes = [
            "\\bPROTECTED\\b",
            "\\bDO_NOT_MODIFY\\b"
        ]

Output and Formatting
---------------------

How can I integrate rstbuddy into my CI/CD pipeline?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Basic Integration**:
    .. code-block:: yaml

        # GitHub Actions example

        - name: Check RST Links

          run: |
            pip install rstbuddy
            rstbuddy check-links

**Advanced Integration**:
    .. code-block:: yaml

        # With custom configuration

        - name: Check RST Links

          run: |
            pip install rstbuddy
            echo "check_rst_links_skip_domains = ['test.example.com']" > .rstbuddy.toml
            rstbuddy check-links --timeout 10 --max-workers 16

**JSON Output for Automation**:
    .. code-block:: yaml

        - name: Check Links and Generate Report

          run: |
            rstbuddy --output json check-links > link_report.json
            # Process JSON report in subsequent steps

**Exit Code Handling**:

    - **Exit 0**: All links are valid
    - **Exit 1**: Broken links found
    - Use exit codes to fail builds when needed

Troubleshooting
---------------

How do I debug configuration issues?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Configuration Debugging**:
    .. code-block:: bash

        # Show current settings
        rstbuddy settings

        # Show with verbose output
        rstbuddy --verbose settings

        # Check config file loading
        rstbuddy --config-file /path/to/config.toml settings

**Common Issues**:

    - **File Not Found**: Check config file paths and permissions
    - **Syntax Errors**: Validate TOML syntax
    - **Environment Variables**: Check variable names and values
    - **File Permissions**: Ensure config files are readable

**Configuration Validation**:

    - Use online TOML validators
    - Check file permissions
    - Verify environment variable names
    - Test with minimal configuration

What should I do if rstbuddy crashes or hangs?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Common Causes**:

    - **Network Issues**: Hanging HTTP requests
    - **Large Files**: Processing very large RST files
    - **Memory Issues**: Insufficient system resources
    - **Infinite Loops**: Complex regex patterns

**Recovery Steps**:

    1. **Kill Process**: Use Ctrl+C or kill command
    2. **Check Logs**: Look for error messages
    3. **Reduce Scope**: Process smaller batches
    4. **Check Resources**: Monitor CPU and memory usage

**Prevention**:

    - Use appropriate timeouts
    - Process files in smaller batches
    - Monitor system resources
    - Test with sample files first

**Debug Mode**:
    .. code-block:: bash

        # Enable verbose output
        rstbuddy --verbose check-links

        # Use dry run for cleaning
        rstbuddy fix document.rst --dry-run

Getting Help
------------

Where can I get more help?
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Documentation**:

    - **Usage Guide**: :doc:`/overview/usage` for detailed command information
    - **Configuration**: :doc:`/overview/configuration` for setup options
    - **Quickstart**: :doc:`/overview/quickstart` for basic examples

**Troubleshooting**:

    - Check this FAQ section
    - Review error messages carefully
    - Use ``--verbose`` flag for debugging
    - Test with minimal examples

**Community Support**:

    - GitHub Issues: Report bugs and request features
    - GitHub Discussions: Ask questions and share solutions
    - Documentation Issues: Report documentation problems

**Best Practices**:

    - Always test with sample files first
    - Use dry-run mode when possible
    - Keep backups of important files
    - Monitor system resources during processing