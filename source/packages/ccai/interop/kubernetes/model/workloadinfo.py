"""
    .. module:: workloadinfo
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Provides the typed ``*Info`` response DTOs for the workload
        primitives (Job, Deployment, StatefulSet, PVC, Service, Ingress,
        Namespace). Each DTO carries the runtime status fields needed by
        waiters and by inventory consumers.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class JobInfo:
    """
        Runtime status of a Kubernetes Job.

        :param name: The Job name.
        :param namespace: The namespace the Job lives in.
        :param phase: A derived phase string: ``Running``, ``Succeeded`` or
            ``Failed``.
        :param succeeded: The count of succeeded pods.
        :param failed: The count of failed pods.
        :param active: The count of active pods.
        :param start_time: The Job start time, when reported.
        :param completion_time: The Job completion time, when reported.
        :param labels: The label map attached to the Job.
    """
    name: str
    namespace: str
    phase: str
    succeeded: int
    failed: int
    active: int
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class DeploymentInfo:
    """
        Runtime status of a Kubernetes Deployment.

        :param name: The Deployment name.
        :param namespace: The namespace the Deployment lives in.
        :param replicas: The desired replica count.
        :param available_replicas: The available replica count.
        :param ready_replicas: The ready replica count.
        :param updated_replicas: The updated replica count.
        :param labels: The label map attached to the Deployment.
    """
    name: str
    namespace: str
    replicas: int
    available_replicas: int
    ready_replicas: int
    updated_replicas: int
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class StatefulSetInfo:
    """
        Runtime status of a Kubernetes StatefulSet.

        :param name: The StatefulSet name.
        :param namespace: The namespace the StatefulSet lives in.
        :param replicas: The desired replica count.
        :param ready_replicas: The ready replica count.
        :param current_replicas: The current replica count.
        :param labels: The label map attached to the StatefulSet.
    """
    name: str
    namespace: str
    replicas: int
    ready_replicas: int
    current_replicas: int
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class PvcInfo:
    """
        Runtime status of a Kubernetes PersistentVolumeClaim.

        :param name: The PVC name.
        :param namespace: The namespace the PVC lives in.
        :param phase: The PVC phase: ``Pending``, ``Bound`` or ``Lost``.
        :param capacity: The bound capacity string, when reported.
        :param storage_class: The storage class name, when reported.
        :param labels: The label map attached to the PVC.
    """
    name: str
    namespace: str
    phase: str
    capacity: str = ""
    storage_class: str = ""
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class ServiceInfo:
    """
        Runtime status of a Kubernetes Service.

        :param name: The Service name.
        :param namespace: The namespace the Service lives in.
        :param service_type: The Service type.
        :param cluster_ip: The cluster IP allocated to the Service.
        :param ports: The list of exposed port numbers.
        :param labels: The label map attached to the Service.
    """
    name: str
    namespace: str
    service_type: str
    cluster_ip: str = ""
    ports: List[int] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class IngressInfo:
    """
        Runtime status of a Kubernetes Ingress.

        :param name: The Ingress name.
        :param namespace: The namespace the Ingress lives in.
        :param hosts: The list of host rules attached to the Ingress.
        :param load_balancer_addresses: The list of load balancer addresses.
        :param labels: The label map attached to the Ingress.
    """
    name: str
    namespace: str
    hosts: List[str] = field(default_factory=list)
    load_balancer_addresses: List[str] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class NamespaceInfo:
    """
        Runtime status of a Kubernetes Namespace.

        :param name: The Namespace name.
        :param phase: The Namespace phase: ``Active`` or ``Terminating``.
        :param labels: The label map attached to the Namespace.
    """
    name: str
    phase: str
    labels: Dict[str, str] = field(default_factory=dict)


__all__ = [
    "JobInfo",
    "DeploymentInfo",
    "StatefulSetInfo",
    "PvcInfo",
    "ServiceInfo",
    "IngressInfo",
    "NamespaceInfo",
]
