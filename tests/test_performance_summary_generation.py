"""
Performance tests for summary generation functionality.

Tests performance requirements including timing, memory usage, and bulk operations.
"""

import os
import threading
import time
from unittest.mock import Mock, patch

import psutil
import pytest

from rstbuddy.services.summary_generation import SummaryGenerationService
from rstbuddy.settings import Settings


class TestSummaryGenerationPerformance:
    """Performance tests for summary generation service."""

    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings(openai_api_key="test-key")

    @pytest.fixture
    def service(self, settings):
        """Create SummaryGenerationService instance."""
        return SummaryGenerationService(settings)

    @pytest.fixture
    def large_rst_content(self):
        """Large RST content for performance testing."""
        # Create a large RST file with realistic content
        content = """Iterative Plan Development
==========================

Markup Conventions
------------------

In this guide,

- lines prefixed with ``[Human]`` are instructions for humans only; AI agents should ignore these lines.
- lines prefixed with ``[AI]`` are instructions for AI agents; humans should ignore these lines.
- lines with no prefix are instructions for both humans and AI agents.
- Parts with the title ``AI Instructions`` are instructions for AI agents only.

AI Instructions
---------------

**STOP. READ THIS FIRST. This workflow is MANDATORY for AI agents.**

You MUST follow this exact sequence for EVERY task, no exceptions:

1. **READ** the human's prompt completely
2. **CREATE** a detailed plan for implementation
3. **ASK** clarifying questions to understand requirements better
4. **WAIT** for human approval of the plan
5. **ONLY THEN** begin implementation

**CRITICAL ENFORCEMENT**: You are FORBIDDEN from using ANY of the following tools until you receive explicit approval:

- `edit_file`
- `search_replace`
- `run_terminal_cmd`
- `delete_file`
- Grepping the codebase for relevant information and web searching for relevant information is allowed.

**VIOLATION CONSEQUENCES**: If you skip this workflow and start implementing immediately, you are:

- Wasting the human's time with potentially incorrect work
- Missing important context that could change the approach
- Creating work that may need to be completely redone
- Failing to follow established best practices
- **VIOLATING MANDATORY WORKFLOW** - This is a critical error

**Failure to follow this workflow will result in incorrect or incomplete work.**

**MANDATORY ACKNOWLEDGMENT**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

[AI] Before proceeding with ANY task, you MUST explicitly acknowledge this workflow by stating:

"I acknowledge that I am supposed to use the following workflow:

1. **READ** the human's prompt completely
2. **CREATE** a detailed plan for implementation
3. **ASK** clarifying questions to understand requirements better
4. **WAIT** for human approval of the plan
5. **ONLY THEN** begin implementation"

☐ I acknowledge the mandatory workflow above

**Failure to follow this workflow will result in incorrect or incomplete work.**

Prompt instructions
-------------------

- [AI] **MANDATORY**: We will use an iterative process to develop a plan to implement the human's prompt.
- [AI] **MANDATORY**: After the user has provided a prompt, the AI agent should first read the prompt and then respond with a plan for how it will implement the prompt. It should not start working on the task until the human has approved the plan.
- [AI] **MANDATORY**: You should restate the general instructions for the recipe in your own words. This is about confirming you know how to help the human.
- [AI] **MANDATORY**: Ask any questions of the human to clarify the prompt, or to suggest improvements to the prompt.
- [Human] Read the plan carefully and make any adjustments to the plan as needed by chatting with the AI agent.
- [Human] At any point, create an empty ``plan.rst`` file and ask the AI agent to write the plan to the file. It will be much easier to read and edit the plan if it is in a file. In Cursor, you can do this by dragging the ``plan.rst`` file into the chat window and saying ``Write the plan to the file in RestructuredText format``. I've found it's a lot more readable than AI generated Markdown, and then you can then include your plan in your own documentation if it helps.
- [Human] Also, eventually your chat session will get too long and Cursor will want to start a new chat session with a summary of the conversatin thus far. Attach your ``plan.rst`` file to the new chat session and ask the AI agent to ``continue``.
- [Human] Once you have made your adjustments, ask the AI agent specifically to ``restate your entire plan with our improvements applied``
- [Human] Once you have made your adjustments, ask the AI agent to ``critique your own plan`` You will very often get a much better implementation than the first one because now the AI agent has much more context to work with.
- [Human] If the plan gets too long or has a lot of repetition, ask the AI agent to ``simplify the plan without changing the core goals or functionality``

**WORKFLOW CHECKLIST FOR AI AGENTS**
------------------------------------

.. [AI] Before starting ANY implementation, confirm you have completed ALL of these steps:

☐ **Step 1**: Read and understood the complete prompt
☐ **Step 2**: Created a detailed implementation plan
☐ **Step 3**: Asked clarifying questions about requirements
☐ **Step 4**: Restated the recipe instructions in your own words
☐ **Step 5**: Received explicit approval from the human to proceed
☐ **Step 6**: Confirmed the plan addresses all requirements
☐ **Step 7**: Acknowledged that implementation tools are now permitted

[AI] **ONLY proceed to implementation after ALL checkboxes are completed.**

**VALIDATION PHRASES**
----------------------

You MUST include one of these phrases in your response to indicate you understand the workflow:

- "I acknowledge the mandatory workflow above"
- "I understand I must wait for approval before implementation"
- "I will not use implementation tools until approved"

**EXAMPLE OF CORRECT WORKFLOW**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

[AI] When you receive a prompt like "Create a documentation file about X", you should respond like this:

"Thank you for the request. Let me create a plan for implementing this documentation file.

## Plan for Creating Documentation File

1. **Structure**: Create a new .rst file with proper Sphinx formatting
2. **Content**: Include sections for [list specific sections]
3. **Format**: Follow the established documentation conventions
4. **Integration**: Add to the appropriate table of contents

Clarifying Questions
--------------------

Before I proceed, I need to understand:

- What specific aspects of X should be covered?
- Who is the target audience for this documentation?
- Are there any existing files I should reference or follow as examples?

## Recipe Confirmation

I understand I should follow the documentation recipe which requires:

- Using proper Sphinx formatting
- Including AI Instructions section
- Following the established heading hierarchy
- Adding appropriate cross-references

Please review this plan and let me know if you'd like any adjustments before I begin implementation."

[AI] **This is the ONLY acceptable way to respond to a new task request.**
"""  # noqa: E501
        # Add more content to make it larger
        for i in range(10):
            content += f"""
Section {i}
==========

This is section {i} with additional content to make the file larger for performance testing.

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

- Item 1: This is a test item for performance testing
- Item 2: Another test item to increase file size
- Item 3: Yet another item for comprehensive testing
- Item 4: Final item in this section

Subsection {i}.1
---------------

This is a subsection with additional content.

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Code Example:
```python
def test_function_{i}():
    \"\"\"Test function for performance testing.\"\"\"
    result = perform_test_operation()
    assert result is not None
    return result
```

"""  # noqa: E501
        return content

    def test_summary_generation_performance_single_file(
        self, service, large_rst_content
    ):
        """
        Test that summary generation completes within 10 seconds for a single
        file.
        """
        with patch("rstbuddy.services.summary_generation.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[
                0
            ].message.content = "This is a test summary for performance testing."
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            start_time = time.time()
            summary = service.generate_summary(large_rst_content)
            end_time = time.time()

            execution_time = end_time - start_time
            assert execution_time < 15.0, (  # noqa: PLR2004
                f"Summary generation took {execution_time:.2f} seconds, "
                "should be under 15 seconds"
            )
            assert "test summary" in summary.lower()

    def test_summary_generation_performance_content_extraction(
        self, service, large_rst_content
    ):
        """Test that content extraction is fast for large files."""
        start_time = time.time()
        content = service._extract_main_content(large_rst_content)  # noqa: SLF001
        end_time = time.time()

        execution_time = end_time - start_time
        assert execution_time < 1.0, (
            f"Content extraction took {execution_time:.2f} seconds, "
            "should be under 1 second"
        )
        assert len(content) > 0

    def test_summary_generation_performance_formatting(self, service):
        """Test that summary formatting is fast."""
        long_summary = (
            "This is a very long summary that should be formatted properly. " * 50
        )

        start_time = time.time()
        formatted = service.format_summary(long_summary)
        end_time = time.time()

        execution_time = end_time - start_time
        assert execution_time < 1.0, (
            f"Summary formatting took {execution_time:.2f} seconds, "
            "should be under 1 second"
        )
        assert "Summary:" in formatted
        assert len(formatted.split("\n")) > 1

    def test_summary_generation_performance_prompt_creation(
        self, service, large_rst_content
    ):
        """Test that prompt creation is fast for large content."""
        start_time = time.time()
        prompt = service._create_summary_prompt(large_rst_content)  # noqa: SLF001
        end_time = time.time()

        execution_time = end_time - start_time
        assert execution_time < 1.0, (
            f"Prompt creation took {execution_time:.2f} seconds, "
            "should be under 1 second"
        )
        assert len(prompt) > 0

    def test_summary_generation_performance_clean_summary(self, service):
        """Test that summary cleaning is fast."""
        raw_summary = (
            '"This rule provides comprehensive testing guidelines for Python projects."'
        )

        start_time = time.time()
        cleaned = service._clean_summary(raw_summary)  # noqa: SLF001
        end_time = time.time()

        execution_time = end_time - start_time
        assert execution_time < 1.0, (
            f"Summary cleaning took {execution_time:.2f} seconds, "
            "should be under 1 second"
        )
        assert "comprehensive testing guidelines" in cleaned

    def test_summary_generation_performance_memory_usage(
        self, service, large_rst_content
    ):
        """Test that summary generation doesn't use excessive memory."""
        try:
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss
        except ImportError:
            pytest.skip("psutil not available for memory testing")

        with patch("rstbuddy.services.summary_generation.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[
                0
            ].message.content = "This is a test summary for memory testing."
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            # Generate summary multiple times to test memory usage
            for _ in range(5):
                summary = service.generate_summary(large_rst_content)
                assert "test summary" in summary.lower()

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 10MB)
        assert memory_increase < 10 * 1024 * 1024, (
            "Memory usage increased by "
            f"{memory_increase / 1024 / 1024:.2f}MB, should be "
            "less than 10MB"
        )

    def test_summary_generation_performance_concurrent_operations(self, service):
        """Test that multiple summary operations can be performed efficiently."""
        results = []
        errors = []

        # Mock the OpenAI client and settings at the test level
        with (
            patch("rstbuddy.services.summary_generation.OpenAI") as mock_openai,
            patch.object(service, "settings") as mock_settings,
        ):
            # Mock the API key to avoid validation errors
            mock_settings.openai_api_key = "test-api-key-12345"

            # Create a mock client that returns different responses for each call
            mock_client = Mock()
            mock_openai.return_value = mock_client

            # Track call count to return different responses
            call_count = 0

            def mock_create(*args, **kwargs):  # noqa: ARG001
                nonlocal call_count
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[
                    0
                ].message.content = f"Summary for thread {call_count % 3}"
                call_count += 1
                return mock_response

            mock_client.chat.completions.create.side_effect = mock_create

            def generate_summary_thread(content, thread_id):
                try:
                    start_time = time.time()
                    summary = service.generate_summary(content)
                    end_time = time.time()

                    results.append((thread_id, end_time - start_time, summary))
                except Exception as e:  # noqa: BLE001
                    errors.append((thread_id, str(e)))

            # Create multiple threads to test concurrent operations
            threads = []
            test_content = "This is test content for concurrent performance testing."

            for i in range(3):
                thread = threading.Thread(
                    target=generate_summary_thread, args=(test_content, i)
                )
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # Check that all operations completed successfully
            assert len(errors) == 0, (
                f"Errors occurred in concurrent operations: {errors}"
            )
            assert len(results) == 3, f"Expected 3 results, got {len(results)}"  # noqa: PLR2004

            # Check that all operations completed within time limit
            for thread_id, execution_time, summary in results:
                assert execution_time < 15.0, (  # noqa: PLR2004
                    f"Thread {thread_id} took {execution_time:.2f} seconds, "
                    "should be under 15 seconds"
                )
                # Check that we got a summary (the exact content may vary due to
                # threading)
                assert "Summary for thread" in summary
