"""
    .. module:: kuberneteshealth
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Provides :class:`KubernetesHealth`, the dataclass returned by
        :meth:`KubernetesClient.health` describing cluster reachability.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from dataclasses import dataclass


@dataclass
class KubernetesHealth:
    """
        Snapshot of Kubernetes API server reachability.

        :param reachable: ``True`` when the API server responded to the
            health probe.
        :param version: The reported Kubernetes server version string, or an
            empty string when the server is unreachable.
        :param node_count: The number of nodes reported by the cluster, or
            ``0`` when the server is unreachable or the caller lacks the
            permission to list nodes.
    """
    reachable: bool
    version: str
    node_count: int
