"""Test :ref: functionality in RSTLinkChecker."""

import pytest
from pathlib import Path
from rstbuddy.services.rst_link_checker import RSTLinkChecker


class TestRefFunctionality:
    """Test :ref: functionality with various scenarios."""

    def test_ref_simple_format(self, tmp_path):
        """Test :ref:`label` format."""
        checker = RSTLinkChecker(tmp_path)

        # Test extraction
        result = checker._extract_ref_label(":ref:`simple-label`")
        assert result == "simple-label"

        # Test with whitespace
        result = checker._extract_ref_label(":ref:`  simple-label  `")
        assert result == "simple-label"

    def test_ref_title_format(self, tmp_path):
        """Test :ref:`Title <label>` format."""
        checker = RSTLinkChecker(tmp_path)

        # Test extraction
        result = checker._extract_ref_label(":ref:`My Title <my-label>`")
        assert result == "my-label"

        # Test with whitespace
        result = checker._extract_ref_label(":ref:`  My Title  <  my-label  >  `")
        assert result == "my-label"

    def test_ref_invalid_formats(self, tmp_path):
        """Test invalid :ref: formats."""
        checker = RSTLinkChecker(tmp_path)

        # Test invalid formats
        assert checker._extract_ref_label(":ref:`invalid format") is None
        assert checker._extract_ref_label(":ref:`Title <label> extra`") is None
        assert checker._extract_ref_label("not a ref") is None

    def test_ref_collection_and_validation(self, tmp_path):
        """Test :ref: collection and validation in a single file."""
        checker = RSTLinkChecker(tmp_path)

        # Create a test file with labels and references
        test_file = tmp_path / "test.rst"
        content = """.. _label1:

Section 1
=========

This references :ref:`label1` which should work.

.. _label2:

Section 2
=========

This references :ref:`label2` which should work.

This references :ref:`missing-label` which should be broken.

This references :ref:`Title <label1>` which should work.

This references :ref:`Another Title <missing-label>` which should be broken.
"""
        test_file.write_text(content, encoding="utf-8")

        # Run the check
        broken = checker.check()

        # Should find 2 broken :ref: links
        ref_broken = [occ for occ in broken if occ.link_text.startswith(":ref:")]
        assert len(ref_broken) == 2

        # Check specific broken links
        broken_texts = [occ.link_text for occ in ref_broken]
        assert ":ref:`missing-label`" in broken_texts
        assert ":ref:`Another Title <missing-label>`" in broken_texts

        # Check that valid links are not broken
        valid_refs = [
            occ
            for occ in broken
            if "label1" in occ.link_text or "label2" in occ.link_text
        ]
        assert len(valid_refs) == 0

    def test_ref_cross_file_references(self, tmp_path):
        """Test :ref: references across different files."""
        checker = RSTLinkChecker(tmp_path)

        # Create first file with labels
        file1 = tmp_path / "file1.rst"
        content1 = """.. _cross-label:

Cross File Label
================

This defines a label that will be referenced from another file.
"""
        file1.write_text(content1, encoding="utf-8")

        # Create second file with references
        file2 = tmp_path / "file2.rst"
        content2 = """Title
=====

This references :ref:`cross-label` from another file.

This references :ref:`missing-cross-label` which should be broken.
"""
        file2.write_text(content2, encoding="utf-8")

        # Run the check
        broken = checker.check()

        # Should find 1 broken :ref: link
        ref_broken = [occ for occ in broken if occ.link_text.startswith(":ref:")]
        assert len(ref_broken) == 1

        # Check that the cross-file reference works
        broken_texts = [occ.link_text for occ in ref_broken]
        assert ":ref:`missing-cross-label`" in broken_texts

        # Check that valid cross-file reference is not broken
        # We need to check if the exact label that exists is being referenced
        valid_refs = []
        for occ in broken:
            extracted_label = checker._extract_ref_label(occ.link_text)
            if extracted_label == "cross-label":
                valid_refs.append(occ)

        assert len(valid_refs) == 0

    def test_ref_forward_references_same_file(self, tmp_path):
        """Test :ref: forward references within the same file."""
        checker = RSTLinkChecker(tmp_path)

        # Create a file with forward references
        test_file = tmp_path / "test.rst"
        content = """Title
=====

This references :ref:`forward-label` before it's defined.

This references :ref:`Title <another-forward-label>` before it's defined.

.. _forward-label:

Forward Label Section
====================

This section defines the forward-label.

.. _another-forward-label:

Another Forward Label Section
============================

This section defines another-forward-label.
"""
        test_file.write_text(content, encoding="utf-8")

        # Run the check
        broken = checker.check()

        # Should find 0 broken :ref: links (forward references should work)
        ref_broken = [occ for occ in broken if occ.link_text.startswith(":ref:")]
        assert len(ref_broken) == 0

    def test_ref_complex_scenarios(self, tmp_path):
        """Test complex :ref: scenarios with mixed valid/invalid references."""
        checker = RSTLinkChecker(tmp_path)

        # Create a test file with complex scenarios
        test_file = tmp_path / "test.rst"
        content = """.. _valid-label:

Valid Section
=============

This references :ref:`valid-label` which should work.

This references :ref:`Valid Title <valid-label>` which should work.

This references :ref:`missing-label` which should be broken.

This references :ref:`Missing Title <missing-label>` which should be broken.

.. _another-valid-label:

Another Valid Section
====================

This references :ref:`another-valid-label` which should work.

This references :ref:`Another Valid Title <another-valid-label>` which should work.

This references :ref:`valid-label` which should work (backward reference).

This references :ref:`forward-label` which should work (forward reference).

.. _forward-label:

Forward Section
==============

This section defines forward-label.
"""
        test_file.write_text(content, encoding="utf-8")

        # Run the check
        broken = checker.check()

        # Should find 2 broken :ref: links
        ref_broken = [occ for occ in broken if occ.link_text.startswith(":ref:")]
        assert len(ref_broken) == 2

        # Check specific broken links
        broken_texts = [occ.link_text for occ in ref_broken]
        assert ":ref:`missing-label`" in broken_texts
        assert ":ref:`Missing Title <missing-label>`" in broken_texts

        # Check that all valid references work
        valid_refs = [
            occ
            for occ in broken
            if "valid-label" in occ.link_text
            or "another-valid-label" in occ.link_text
            or "forward-label" in occ.link_text
        ]
        assert len(valid_refs) == 0

    def test_ref_edge_cases(self, tmp_path):
        """Test edge cases for :ref: parsing."""
        checker = RSTLinkChecker(tmp_path)

        # Test various edge cases
        edge_cases = [
            ":ref:`label-with-dashes`",
            ":ref:`label_with_underscores`",
            ":ref:`label.with.dots`",
            ":ref:`label with spaces`",
            ":ref:`Title with spaces <label-with-dashes>`",
            ":ref:`Complex Title <label_with_underscores>`",
            ":ref:`Title with dots <label.with.dots>`",
        ]

        for case in edge_cases:
            result = checker._extract_ref_label(case)
            assert result is not None, f"Failed to extract label from: {case}"

            # Check that the extracted label doesn't contain the title part
            if "<" in case:
                assert "<" not in result, (
                    f"Title part found in extracted label: {result}"
                )
                assert ">" not in result, (
                    f"Title part found in extracted label: {result}"
                )

    def test_labels_with_spaces(self, tmp_path):
        """Test that labels with spaces are properly indexed and validated."""
        checker = RSTLinkChecker(tmp_path)

        # Create a test file with labels containing spaces
        test_file = tmp_path / "test.rst"
        content = """.. _label with spaces:

Section with Spaces
==================

This references :ref:`label with spaces` which should work.

.. _another label with spaces:

Another Section
==============

This references :ref:`another label with spaces` which should work.

This references :ref:`missing label with spaces` which should be broken.

.. _complex-label:

Complex Section
==============

This references :ref:`Complex Title <complex-label>` which should work.
"""
        test_file.write_text(content, encoding="utf-8")

        # Run the check
        broken = checker.check()

        # Should find 1 broken :ref: link
        ref_broken = [occ for occ in broken if occ.link_text.startswith(":ref:")]
        assert len(ref_broken) == 1

        # Check that the broken link is the missing one
        broken_texts = [occ.link_text for occ in ref_broken]
        assert ":ref:`missing label with spaces`" in broken_texts

        # Check that valid labels with spaces work (they should NOT be in broken links)
        # The broken link should only be the missing one
        # We need to check if the exact labels that exist are being referenced
        valid_labels = ["label with spaces", "another label with spaces"]
        valid_refs_with_spaces = []

        for occ in broken:
            extracted_label = checker._extract_ref_label(occ.link_text)
            if extracted_label in valid_labels:
                valid_refs_with_spaces.append(occ)

        # Only the missing label should be broken, not the valid ones
        assert len(valid_refs_with_spaces) == 0

        # Check that the complex label also works
        complex_refs = [occ for occ in broken if "complex-label" in occ.link_text]
        assert len(complex_refs) == 0
