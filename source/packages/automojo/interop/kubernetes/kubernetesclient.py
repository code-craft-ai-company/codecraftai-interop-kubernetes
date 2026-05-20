"""
    .. module:: kubernetesclient
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Provides :class:`KubernetesClient`, the top-level interop
        client wrapping the official ``kubernetes`` Python SDK and
        normalising it to the automojo ``Aspects`` pattern.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import logging
import os

from typing import Dict, Optional

from automojo.errors.exceptions import SemanticError

from automojo.interop.kubernetes.aspectskubernetes import (
    AspectsKubernetes,
    DEFAULT_KUBERNETES_ASPECTS,
)
from automojo.interop.kubernetes.exceptionmapping import reclassify_api_exception
from automojo.interop.kubernetes.exceptions.kuberneteserrors import (
    KubernetesApiError,
    KubernetesResourceNotFoundError,
)
from automojo.interop.kubernetes.kubeconfigloader import KubeConfigLoader
from automojo.interop.kubernetes.kuberneteshealth import KubernetesHealth


DEFAULT_NAMESPACE = "default"


class KubernetesClient:
    """
        Top-level Kubernetes interop client.

        The client wraps the official ``kubernetes`` Python SDK. It owns
        kubeconfig loading, the active context and namespace, exception
        reclassification, the health probe, and the workload primitive
        sub-clients (``jobs``, ``deployments``, ``statefulsets``, ``pvcs``,
        ``services``, ``ingresses``).

        :ivar core_v1_api: The SDK ``CoreV1Api`` bound to the active client.
        :ivar apps_v1_api: The SDK ``AppsV1Api`` bound to the active client.
        :ivar batch_v1_api: The SDK ``BatchV1Api`` bound to the active client.
        :ivar networking_v1_api: The SDK ``NetworkingV1Api`` bound to the
            active client.
        :ivar version_api: The SDK ``VersionApi`` bound to the active client.
    """

    def __init__(
        self,
        *,
        kubeconfig_path: Optional[str] = None,
        kubeconfig_dict: Optional[Dict[str, object]] = None,
        in_cluster: bool = False,
        context: Optional[str] = None,
        namespace: str = DEFAULT_NAMESPACE,
        api_client: Optional[object] = None,
    ) -> None:
        """
            Initialise a :class:`KubernetesClient`.

            Exactly one of ``kubeconfig_path``, ``kubeconfig_dict`` or
            ``in_cluster`` must be supplied. The ``api_client`` parameter is
            a test seam — when supplied the kubeconfig source is still
            validated but the supplied ``ApiClient`` is used directly so
            unit tests can inject a fake SDK client.

            :param kubeconfig_path: Filesystem path of a kubeconfig file.
            :param kubeconfig_dict: An in-memory kubeconfig dict.
            :param in_cluster: When ``True`` use the in-cluster context.
            :param context: The named context to activate.
            :param namespace: The default namespace for subsequent calls.
            :param api_client: Optional pre-built SDK ``ApiClient`` (test
                seam). When ``None`` the client is built from the resolved
                kubeconfig.

            :returns: ``None``
            :raises: SemanticError
        """
        self._loader = KubeConfigLoader(
            kubeconfig_path=kubeconfig_path,
            kubeconfig_dict=kubeconfig_dict,
            in_cluster=in_cluster,
            context=context,
        )
        self._namespace = namespace
        self._context = context

        if api_client is not None:
            self._api_client = api_client
        else:
            self._api_client = self._loader.build_api_client()

        self.core_v1_api = None
        self.apps_v1_api = None
        self.batch_v1_api = None
        self.networking_v1_api = None
        self.version_api = None

        self.jobs = None
        self.deployments = None
        self.statefulsets = None
        self.pvcs = None
        self.services = None
        self.ingresses = None
        self.namespaces = None

        self._bind_apis()
        self._bind_primitives()
        return

    @property
    def namespace(self) -> str:
        """
            The client-wide default namespace applied when a method does not
            receive an explicit ``namespace`` argument.

            :returns: The active default namespace.
        """
        return self._namespace

    @property
    def context(self) -> Optional[str]:
        """
            The active kubeconfig context name.

            :returns: The active context name, or ``None`` for in-cluster.
        """
        return self._context

    @property
    def api_client(self) -> object:
        """
            The underlying SDK ``ApiClient``.

            :returns: The active ``kubernetes.client.ApiClient``.
        """
        return self._api_client

    def _bind_apis(self) -> None:
        """
            Construct the SDK Api facades against the active ``ApiClient``.

            :returns: ``None``
        """
        from kubernetes import client as kubernetes_client

        self.core_v1_api = kubernetes_client.CoreV1Api(self._api_client)
        self.apps_v1_api = kubernetes_client.AppsV1Api(self._api_client)
        self.batch_v1_api = kubernetes_client.BatchV1Api(self._api_client)
        self.networking_v1_api = kubernetes_client.NetworkingV1Api(self._api_client)
        self.version_api = kubernetes_client.VersionApi(self._api_client)
        return

    def _bind_primitives(self) -> None:
        """
            Construct the workload primitive sub-clients bound to this
            client.

            :returns: ``None``
        """
        from automojo.interop.kubernetes.workload.jobprimitive import JobPrimitive
        from automojo.interop.kubernetes.workload.deploymentprimitive import (
            DeploymentPrimitive,
        )
        from automojo.interop.kubernetes.workload.statefulsetprimitive import (
            StatefulSetPrimitive,
        )
        from automojo.interop.kubernetes.workload.pvcprimitive import PvcPrimitive
        from automojo.interop.kubernetes.workload.serviceprimitive import (
            ServicePrimitive,
        )
        from automojo.interop.kubernetes.workload.ingressprimitive import (
            IngressPrimitive,
        )
        from automojo.interop.kubernetes.workload.namespaceprimitive import (
            NamespacePrimitive,
        )

        self.jobs = JobPrimitive(client=self)
        self.deployments = DeploymentPrimitive(client=self)
        self.statefulsets = StatefulSetPrimitive(client=self)
        self.pvcs = PvcPrimitive(client=self)
        self.services = ServicePrimitive(client=self)
        self.ingresses = IngressPrimitive(client=self)
        self.namespaces = NamespacePrimitive(client=self)
        return

    def resolve_namespace(self, namespace: Optional[str]) -> str:
        """
            Resolve a possibly-omitted namespace argument to a concrete
            namespace, falling back to the client-wide default.

            :param namespace: The namespace supplied by the caller, or
                ``None``.

            :returns: The concrete namespace to use.
        """
        if namespace is not None:
            return namespace

        resolved = self._namespace
        return resolved

    def use_namespace(self, namespace: str, *, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> None:
        """
            Update the client-wide default namespace for subsequent calls.

            :param namespace: The namespace to make the new default.
            :param aspects: Behaviour parameters for the call.

            :returns: ``None``
        """
        logger = logging.getLogger(aspects.logger_name)
        logger.log(aspects.logging_level, "Switching default namespace to '%s'.", namespace)

        self._namespace = namespace
        return

    def use_context(self, context: str, *, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> None:
        """
            Switch to the named context in the loaded kubeconfig and rebuild
            the SDK Api facades against the new context.

            :param context: The context name to activate.
            :param aspects: Behaviour parameters for the call.

            :returns: ``None``
            :raises: KubernetesResourceNotFoundError
        """
        logger = logging.getLogger(aspects.logger_name)

        available = self._loader.available_contexts()

        if context not in available:
            err_msg_lines = ["The requested kubeconfig context was not found."]
            err_msg_lines.append("REQUESTED: {}".format(context))
            err_msg_lines.append("AVAILABLE: ({})".format(len(available)))
            for entry_name in available:
                err_msg_lines.append("    {}".format(entry_name))

            err_msg = os.linesep.join(err_msg_lines)
            raise KubernetesResourceNotFoundError(
                err_msg,
                status_code=404,
                detail="context not found",
            ) from None

        logger.log(aspects.logging_level, "Switching kubeconfig context to '%s'.", context)

        self._context = context
        self._loader.context = context
        self._api_client = self._loader.build_api_client()
        self._bind_apis()
        self._bind_primitives()
        return

    def health(self, *, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> KubernetesHealth:
        """
            Probe the API server and report reachability, server version,
            and node count.

            The probe never raises on an unreachable cluster — it reports
            ``KubernetesHealth(reachable=False, version="", node_count=0)``
            so callers can treat the result as data.

            :param aspects: Behaviour parameters for the call.

            :returns: A :class:`KubernetesHealth` snapshot.
        """
        logger = logging.getLogger(aspects.logger_name)

        version = ""
        node_count = 0
        reachable = False

        try:
            version_info = self.version_api.get_code(
                _request_timeout=aspects.timeout_seconds,
            )
            version = getattr(version_info, "git_version", "")
            if version is None:
                version = ""
            reachable = True
        except Exception as probe_error:
            logger.log(
                aspects.logging_level,
                "Kubernetes API server health probe failed: %s",
                probe_error,
            )
            return KubernetesHealth(reachable=False, version="", node_count=0)

        try:
            node_list = self.core_v1_api.list_node(
                _request_timeout=aspects.timeout_seconds,
            )
            items = getattr(node_list, "items", None)
            if items is not None:
                node_count = len(items)
        except Exception as node_error:
            logger.log(
                aspects.logging_level,
                "Kubernetes node enumeration failed (partial health): %s",
                node_error,
            )
            node_count = 0

        result = KubernetesHealth(
            reachable=reachable,
            version=version,
            node_count=node_count,
        )
        return result

    def list_nodes(self, *, label_selector: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> list:
        """
            Enumerate the nodes (the NodePool query surface) of the cluster.

            :param label_selector: An optional label selector restricting
                the returned nodes (for example a CoreWeave node-pool
                label).
            :param aspects: Behaviour parameters for the call.

            :returns: A list of :class:`NodeInfo` DTOs.
            :raises: KubernetesApiError
        """
        from automojo.interop.kubernetes.model.nodeinfo import NodeInfo

        logger = logging.getLogger(aspects.logger_name)
        logger.log(aspects.logging_level, "Listing cluster nodes.")

        try:
            node_list = self.core_v1_api.list_node(
                label_selector=label_selector,
                _request_timeout=aspects.timeout_seconds,
            )
        except Exception as list_error:
            reclassified = reclassify_api_exception(list_error)
            raise reclassified from list_error

        results = []
        items = getattr(node_list, "items", None)

        if items is not None:
            for node_object in items:
                node_info = NodeInfo.from_sdk(node_object)
                results.append(node_info)

        return results


__all__ = ["KubernetesClient", "DEFAULT_NAMESPACE"]
