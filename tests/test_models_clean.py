"""
Tests for the clean models.
"""

from __future__ import annotations

from rstbuddy.models.clean import CleanReport


class TestCleanReport:
    """Test the CleanReport dataclass."""

    def test_clean_report_default_values(self):
        """Test that CleanReport has correct default values."""
        report = CleanReport()
        assert report.headings_fixed == 0
        assert report.md_headings_converted == 0
        assert report.lists_spaced == 0
        assert report.code_blocks_converted == 0
        assert report.inline_code_fixed == 0
        assert report.stray_fences_removed == 0

    def test_clean_report_custom_values(self):
        """Test that CleanReport can be initialized with custom values."""
        report = CleanReport(
            headings_fixed=5,
            md_headings_converted=3,
            lists_spaced=2,
            code_blocks_converted=1,
            inline_code_fixed=4,
            stray_fences_removed=6,
        )
        assert report.headings_fixed == 5  # noqa: PLR2004
        assert report.md_headings_converted == 3  # noqa: PLR2004
        assert report.lists_spaced == 2  # noqa: PLR2004
        assert report.code_blocks_converted == 1
        assert report.inline_code_fixed == 4  # noqa: PLR2004
        assert report.stray_fences_removed == 6  # noqa: PLR2004

    def test_clean_report_merge(self):
        """Test merging two CleanReport instances."""
        report1 = CleanReport(
            headings_fixed=1,
            md_headings_converted=2,
            lists_spaced=3,
            code_blocks_converted=4,
            inline_code_fixed=5,
            stray_fences_removed=6,
        )
        report2 = CleanReport(
            headings_fixed=10,
            md_headings_converted=20,
            lists_spaced=30,
            code_blocks_converted=40,
            inline_code_fixed=50,
            stray_fences_removed=60,
        )

        report1.merge(report2)

        assert report1.headings_fixed == 11  # noqa: PLR2004
        assert report1.md_headings_converted == 22  # noqa: PLR2004
        assert report1.lists_spaced == 33  # noqa: PLR2004
        assert report1.code_blocks_converted == 44  # noqa: PLR2004
        assert report1.inline_code_fixed == 55  # noqa: PLR2004
        assert report1.stray_fences_removed == 66  # noqa: PLR2004

    def test_clean_report_merge_zero_values(self):
        """Test merging with zero values."""
        report1 = CleanReport()
        report2 = CleanReport()

        report1.merge(report2)

        assert report1.headings_fixed == 0
        assert report1.md_headings_converted == 0
        assert report1.lists_spaced == 0
        assert report1.code_blocks_converted == 0
        assert report1.inline_code_fixed == 0
        assert report1.stray_fences_removed == 0

    def test_clean_report_merge_negative_values(self):
        """Test merging with negative values."""
        report1 = CleanReport(headings_fixed=5)
        report2 = CleanReport(headings_fixed=-2)

        report1.merge(report2)

        assert report1.headings_fixed == 3  # noqa: PLR2004

    def test_clean_report_merge_multiple_times(self):
        """Test merging multiple times."""
        report = CleanReport()
        report1 = CleanReport(headings_fixed=1)
        report2 = CleanReport(headings_fixed=2)
        report3 = CleanReport(headings_fixed=3)

        report.merge(report1)
        report.merge(report2)
        report.merge(report3)

        assert report.headings_fixed == 6  # noqa: PLR2004

    def test_clean_report_merge_self(self):
        """Test merging a report with itself."""
        report = CleanReport(headings_fixed=5)
        original_headings = report.headings_fixed

        report.merge(report)

        assert report.headings_fixed == original_headings * 2

    def test_clean_report_merge_preserves_other(self):
        """Test that merging doesn't modify the other report."""
        report1 = CleanReport(headings_fixed=5)
        report2 = CleanReport(headings_fixed=3)

        original_report2_headings = report2.headings_fixed
        report1.merge(report2)

        assert report2.headings_fixed == original_report2_headings
        assert report1.headings_fixed == 8  # noqa: PLR2004
