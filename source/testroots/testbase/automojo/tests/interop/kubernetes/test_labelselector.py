"""
    .. module:: test_labelselector
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit and Hypothesis property tests for the label-selector
        composition helpers.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import unittest

from hypothesis import given, strategies

from ccai.interop.kubernetes.workload.labelselector import (
    compose_label_selector,
    managed_selector,
    merge_selectors,
)


_LABEL_KEYS = strategies.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=1,
    max_size=8,
)
_LABEL_VALUES = strategies.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
    min_size=1,
    max_size=8,
)
_LABEL_MAPS = strategies.dictionaries(
    keys=_LABEL_KEYS,
    values=_LABEL_VALUES,
    max_size=6,
)


class LabelSelectorUnitTests(unittest.TestCase):
    """
        Concrete unit tests for label-selector composition.
    """

    def test_empty_map_yields_empty_selector(self):
        """
            An empty or None label map yields an empty selector.
        """
        self.assertEqual(compose_label_selector({}), "")
        self.assertEqual(compose_label_selector(None), "")
        return

    def test_compose_is_sorted(self):
        """
            The composed selector is sorted by key for determinism.
        """
        selector = compose_label_selector({"zeta": "1", "alpha": "2"})
        self.assertEqual(selector, "alpha=2,zeta=1")
        return

    def test_merge_drops_empty_operands(self):
        """
            Merging drops empty operands so no stray commas appear.
        """
        self.assertEqual(merge_selectors("a=1", ""), "a=1")
        self.assertEqual(merge_selectors("", "b=2"), "b=2")
        self.assertEqual(merge_selectors("a=1", "b=2"), "a=1,b=2")
        self.assertEqual(merge_selectors("", ""), "")
        return

    def test_managed_selector(self):
        """
            The managed selector matches codecraftai-managed resources.
        """
        self.assertEqual(managed_selector(), "ccai/managed=true")
        return


class LabelSelectorPropertyTests(unittest.TestCase):
    """
        Hypothesis property tests over label-selector composition.
    """

    @given(labels=_LABEL_MAPS)
    def test_compose_is_deterministic(self, labels):
        """
            Composition is deterministic for a given label map regardless
            of dict ordering.
        """
        reordered = dict(reversed(list(labels.items())))
        self.assertEqual(
            compose_label_selector(labels),
            compose_label_selector(reordered),
        )
        return

    @given(labels=_LABEL_MAPS)
    def test_compose_term_count(self, labels):
        """
            The composed selector carries exactly one term per label.
        """
        selector = compose_label_selector(labels)
        if len(labels) == 0:
            self.assertEqual(selector, "")
        else:
            self.assertEqual(len(selector.split(",")), len(labels))
        return

    @given(first=_LABEL_MAPS, second=_LABEL_MAPS)
    def test_merge_never_has_stray_comma(self, first, second):
        """
            A merged selector never starts or ends with a comma and never
            contains an empty term.
        """
        merged = merge_selectors(
            compose_label_selector(first),
            compose_label_selector(second),
        )
        if len(merged) > 0:
            self.assertFalse(merged.startswith(","))
            self.assertFalse(merged.endswith(","))
            for term in merged.split(","):
                self.assertGreater(len(term), 0)
        return


if __name__ == "__main__":
    unittest.main()
