"""
    .. module:: workloadspecs
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Provides the concrete typed request payload specs for the
        workload primitives: :class:`JobSpec`, :class:`DeploymentSpec`,
        :class:`StatefulSetSpec`, :class:`PvcSpec`, :class:`ServiceSpec`,
        :class:`IngressSpec` and :class:`NamespaceSpec`.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Dict, List, Optional, Tuple

from ccai.interop.kubernetes.specs.workloadspec import WorkloadSpec


class JobSpec(WorkloadSpec):
    """
        Typed request payload for :meth:`JobPrimitive.apply`.
    """

    REQUIRED_FIELDS: Tuple[str, ...] = ("name", "image")

    def __init__(
        self,
        *,
        name: str,
        image: str,
        command: Optional[List[str]] = None,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        resources: Optional[Dict[str, Dict[str, str]]] = None,
        restart_policy: str = "Never",
        backoff_limit: int = 0,
        completions: int = 1,
        parallelism: int = 1,
        node_selector: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
            Initialise a :class:`JobSpec`.

            :param name: The Job name.
            :param image: The container image reference.
            :param command: The container entrypoint command.
            :param args: The container entrypoint arguments.
            :param env: A name -> value environment variable map.
            :param resources: A ``requests`` / ``limits`` resource map.
            :param restart_policy: ``Never`` or ``OnFailure``.
            :param backoff_limit: The Job backoff limit.
            :param completions: The desired completion count.
            :param parallelism: The desired parallelism.
            :param node_selector: A node-selector label map.
            :param labels: Extra labels to attach to the Job.

            :returns: ``None``
        """
        self.name = name
        self.image = image
        self.command = command if command is not None else []
        self.args = args if args is not None else []
        self.env = env if env is not None else {}
        self.resources = resources if resources is not None else {}
        self.restart_policy = restart_policy
        self.backoff_limit = backoff_limit
        self.completions = completions
        self.parallelism = parallelism
        self.node_selector = node_selector if node_selector is not None else {}
        self.labels = labels if labels is not None else {}
        return


class DeploymentSpec(WorkloadSpec):
    """
        Typed request payload for :meth:`DeploymentPrimitive.apply`.
    """

    REQUIRED_FIELDS: Tuple[str, ...] = ("name", "image")

    def __init__(
        self,
        *,
        name: str,
        image: str,
        replicas: int = 1,
        container_port: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
        resources: Optional[Dict[str, Dict[str, str]]] = None,
        labels: Optional[Dict[str, str]] = None,
        node_selector: Optional[Dict[str, str]] = None,
    ) -> None:
        """
            Initialise a :class:`DeploymentSpec`.

            :param name: The Deployment name.
            :param image: The container image reference.
            :param replicas: The desired replica count.
            :param container_port: An optional container port to expose.
            :param env: A name -> value environment variable map.
            :param resources: A ``requests`` / ``limits`` resource map.
            :param labels: Extra labels to attach to the Deployment.
            :param node_selector: A node-selector label map.

            :returns: ``None``
        """
        self.name = name
        self.image = image
        self.replicas = replicas
        self.container_port = container_port
        self.env = env if env is not None else {}
        self.resources = resources if resources is not None else {}
        self.labels = labels if labels is not None else {}
        self.node_selector = node_selector if node_selector is not None else {}
        return


class StatefulSetSpec(WorkloadSpec):
    """
        Typed request payload for :meth:`StatefulSetPrimitive.apply`.
    """

    REQUIRED_FIELDS: Tuple[str, ...] = ("name", "image", "service_name")

    def __init__(
        self,
        *,
        name: str,
        image: str,
        service_name: str,
        replicas: int = 1,
        container_port: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
        resources: Optional[Dict[str, Dict[str, str]]] = None,
        labels: Optional[Dict[str, str]] = None,
        node_selector: Optional[Dict[str, str]] = None,
    ) -> None:
        """
            Initialise a :class:`StatefulSetSpec`.

            :param name: The StatefulSet name.
            :param image: The container image reference.
            :param service_name: The governing headless service name.
            :param replicas: The desired replica count.
            :param container_port: An optional container port to expose.
            :param env: A name -> value environment variable map.
            :param resources: A ``requests`` / ``limits`` resource map.
            :param labels: Extra labels to attach to the StatefulSet.
            :param node_selector: A node-selector label map.

            :returns: ``None``
        """
        self.name = name
        self.image = image
        self.service_name = service_name
        self.replicas = replicas
        self.container_port = container_port
        self.env = env if env is not None else {}
        self.resources = resources if resources is not None else {}
        self.labels = labels if labels is not None else {}
        self.node_selector = node_selector if node_selector is not None else {}
        return


class PvcSpec(WorkloadSpec):
    """
        Typed request payload for :meth:`PvcPrimitive.apply`.
    """

    REQUIRED_FIELDS: Tuple[str, ...] = ("name", "storage_request")

    def __init__(
        self,
        *,
        name: str,
        storage_request: str,
        access_modes: Optional[List[str]] = None,
        storage_class: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
            Initialise a :class:`PvcSpec`.

            :param name: The PVC name.
            :param storage_request: The requested storage size (for example
                ``100Gi``).
            :param access_modes: The list of access modes. Defaults to
                ``["ReadWriteOnce"]``.
            :param storage_class: An optional storage class name.
            :param labels: Extra labels to attach to the PVC.

            :returns: ``None``
        """
        self.name = name
        self.storage_request = storage_request
        if access_modes is not None:
            self.access_modes = access_modes
        else:
            self.access_modes = ["ReadWriteOnce"]
        self.storage_class = storage_class
        self.labels = labels if labels is not None else {}
        return


class ServiceSpec(WorkloadSpec):
    """
        Typed request payload for :meth:`ServicePrimitive.apply`.
    """

    REQUIRED_FIELDS: Tuple[str, ...] = ("name", "ports")

    def __init__(
        self,
        *,
        name: str,
        ports: List[int],
        selector: Optional[Dict[str, str]] = None,
        service_type: str = "ClusterIP",
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
            Initialise a :class:`ServiceSpec`.

            :param name: The Service name.
            :param ports: The list of port numbers to expose.
            :param selector: The pod selector label map.
            :param service_type: The Service type.
            :param labels: Extra labels to attach to the Service.

            :returns: ``None``
        """
        self.name = name
        self.ports = ports
        self.selector = selector if selector is not None else {}
        self.service_type = service_type
        self.labels = labels if labels is not None else {}
        return


class IngressSpec(WorkloadSpec):
    """
        Typed request payload for :meth:`IngressPrimitive.apply`.
    """

    REQUIRED_FIELDS: Tuple[str, ...] = ("name", "host", "service_name", "service_port")

    def __init__(
        self,
        *,
        name: str,
        host: str,
        service_name: str,
        service_port: int,
        path: str = "/",
        ingress_class: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
            Initialise an :class:`IngressSpec`.

            :param name: The Ingress name.
            :param host: The host rule for the Ingress.
            :param service_name: The backend Service name.
            :param service_port: The backend Service port number.
            :param path: The path rule. Defaults to ``/``.
            :param ingress_class: An optional ingress class name.
            :param labels: Extra labels to attach to the Ingress.

            :returns: ``None``
        """
        self.name = name
        self.host = host
        self.service_name = service_name
        self.service_port = service_port
        self.path = path
        self.ingress_class = ingress_class
        self.labels = labels if labels is not None else {}
        return


class NamespaceSpec(WorkloadSpec):
    """
        Typed request payload for :meth:`NamespacePrimitive.apply`.
    """

    REQUIRED_FIELDS: Tuple[str, ...] = ("name",)

    def __init__(
        self,
        *,
        name: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
            Initialise a :class:`NamespaceSpec`.

            :param name: The Namespace name.
            :param labels: Extra labels to attach to the Namespace.

            :returns: ``None``
        """
        self.name = name
        self.labels = labels if labels is not None else {}
        return


__all__ = [
    "JobSpec",
    "DeploymentSpec",
    "StatefulSetSpec",
    "PvcSpec",
    "ServiceSpec",
    "IngressSpec",
    "NamespaceSpec",
]
