"""
    .. module:: labelselector
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Provides pure label-selector composition helpers used by the
        workload primitives. Kept free of SDK imports so it is trivially
        property-testable.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Dict, Optional

from automojo.interop.kubernetes.workload import (
    MANAGED_LABEL_KEY,
    MANAGED_LABEL_VALUE,
)


def compose_label_selector(labels: Optional[Dict[str, str]]) -> str:
    """
        Compose a Kubernetes equality-based label selector string from a
        label map.

        The keys are sorted so the composed selector is deterministic for a
        given label map regardless of dict insertion order.

        :param labels: A key -> value label map, or ``None``.

        :returns: A comma-joined ``key=value`` selector string, or an empty
            string when ``labels`` is ``None`` or empty.
    """
    if labels is None:
        return ""

    if len(labels) == 0:
        return ""

    terms = []
    for label_key in sorted(labels.keys()):
        label_value = labels[label_key]
        terms.append("{}={}".format(label_key, label_value))

    selector = ",".join(terms)
    return selector


def merge_selectors(first: str, second: str) -> str:
    """
        Merge two equality-based label selector strings into one.

        Empty operands are dropped so the result never carries a stray
        leading or trailing comma.

        :param first: The first selector string.
        :param second: The second selector string.

        :returns: The merged selector string.
    """
    parts = []

    if first is not None and len(first) > 0:
        parts.append(first)

    if second is not None and len(second) > 0:
        parts.append(second)

    merged = ",".join(parts)
    return merged


def managed_selector() -> str:
    """
        Return the equality-based selector matching automojo-managed
        resources.

        :returns: The ``automojo/managed=true`` selector string.
    """
    selector = "{}={}".format(MANAGED_LABEL_KEY, MANAGED_LABEL_VALUE)
    return selector


__all__ = ["compose_label_selector", "merge_selectors", "managed_selector"]
