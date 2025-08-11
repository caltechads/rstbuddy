from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CleanReport:
    """
    Aggregated metrics for a single RST cleaning operation.

    The counters indicate how many times each transformation was applied and
    how many links were checked/failed. Use this object to render CLI
    summaries or to drive automation.
    """

    #: Number of RST headings whose underline/overline were normalized
    headings_fixed: int = 0
    #: Number of Markdown headings converted to RST headings
    md_headings_converted: int = 0
    #: Number of times a blank line was inserted after a list block
    lists_spaced: int = 0
    #: Number of fenced code blocks converted to RST code-block directives
    code_blocks_converted: int = 0
    #: Number of inline Markdown code spans converted to RST inline literals
    inline_code_fixed: int = 0
    #: Number of stray triple-backtick fence lines removed
    stray_fences_removed: int = 0

    def merge(self, other: CleanReport) -> None:
        """
        Merge another report into this one by summing counters and appending
        broken links.

        Args:
            other: Another report to merge into this instance

        Returns:
            None

        """
        self.headings_fixed += other.headings_fixed
        self.md_headings_converted += other.md_headings_converted
        self.lists_spaced += other.lists_spaced
        self.code_blocks_converted += other.code_blocks_converted
        self.inline_code_fixed += other.inline_code_fixed
        self.stray_fences_removed += other.stray_fences_removed
