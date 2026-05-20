"""
    .. module:: nodeinfo
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Provides :class:`NodeInfo`, the typed DTO describing a single
        cluster node returned by :meth:`KubernetesClient.list_nodes`.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from dataclasses import dataclass, field
from typing import Dict


@dataclass
class NodeInfo:
    """
        Typed description of a single Kubernetes cluster node.

        :param name: The node name.
        :param ready: ``True`` when the node reports a ``Ready`` condition.
        :param labels: The label map attached to the node.
        :param allocatable: The allocatable resource map (cpu, memory, gpu).
        :param unschedulable: ``True`` when the node is cordoned.
    """
    name: str
    ready: bool
    labels: Dict[str, str] = field(default_factory=dict)
    allocatable: Dict[str, str] = field(default_factory=dict)
    unschedulable: bool = False

    @classmethod
    def from_sdk(cls, node_object: object) -> "NodeInfo":
        """
            Build a :class:`NodeInfo` from an SDK ``V1Node`` object.

            :param node_object: The SDK ``V1Node`` instance.

            :returns: A populated :class:`NodeInfo`.
        """
        metadata = getattr(node_object, "metadata", None)
        node_name = ""
        node_labels: Dict[str, str] = {}

        if metadata is not None:
            node_name = getattr(metadata, "name", "") or ""
            metadata_labels = getattr(metadata, "labels", None)
            if metadata_labels is not None:
                node_labels = dict(metadata_labels)

        spec = getattr(node_object, "spec", None)
        unschedulable = False
        if spec is not None:
            spec_unschedulable = getattr(spec, "unschedulable", None)
            if spec_unschedulable is True:
                unschedulable = True

        status = getattr(node_object, "status", None)
        ready = False
        allocatable: Dict[str, str] = {}

        if status is not None:
            status_allocatable = getattr(status, "allocatable", None)
            if status_allocatable is not None:
                allocatable = dict(status_allocatable)

            conditions = getattr(status, "conditions", None)
            if conditions is not None:
                for condition in conditions:
                    condition_type = getattr(condition, "type", None)
                    condition_status = getattr(condition, "status", None)
                    if condition_type == "Ready" and condition_status == "True":
                        ready = True

        node_info = cls(
            name=node_name,
            ready=ready,
            labels=node_labels,
            allocatable=allocatable,
            unschedulable=unschedulable,
        )
        return node_info
