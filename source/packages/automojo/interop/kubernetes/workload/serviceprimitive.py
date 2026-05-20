"""
    .. module:: serviceprimitive
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Provides :class:`ServicePrimitive`, the typed helper for
        Kubernetes Services (``CoreV1Api``).

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Dict, List, Optional

from automojo.interop.kubernetes.aspectskubernetes import (
    AspectsKubernetes,
    DEFAULT_KUBERNETES_ASPECTS,
)
from automojo.interop.kubernetes.model.workloadinfo import ServiceInfo
from automojo.interop.kubernetes.specs.workloadspecs import ServiceSpec
from automojo.interop.kubernetes.workload.jobprimitive import _attr
from automojo.interop.kubernetes.workload.workloadprimitive import WorkloadPrimitive


def _service_info_from_sdk(service_object: object) -> ServiceInfo:
    """
        Build a :class:`ServiceInfo` from an SDK Service object.

        :param service_object: The SDK ``V1Service`` or equivalent dict.

        :returns: A populated :class:`ServiceInfo`.
    """
    metadata = _attr(service_object, "metadata")
    name = _attr(metadata, "name") or ""
    namespace = _attr(metadata, "namespace") or ""
    labels = _attr(metadata, "labels") or {}

    spec = _attr(service_object, "spec")
    service_type = _attr(spec, "type") or "ClusterIP"
    cluster_ip = _attr(spec, "cluster_ip") or ""

    ports: List[int] = []
    spec_ports = _attr(spec, "ports")
    if spec_ports is not None:
        for port_entry in spec_ports:
            port_number = _attr(port_entry, "port")
            if port_number is not None:
                ports.append(port_number)

    service_info = ServiceInfo(
        name=name,
        namespace=namespace,
        service_type=service_type,
        cluster_ip=cluster_ip,
        ports=ports,
        labels=dict(labels),
    )
    return service_info


class ServicePrimitive(WorkloadPrimitive):
    """
        Typed helper for Kubernetes Services.

        Exposes ``apply`` / ``delete`` / ``get`` / ``list``.
    """

    KIND = "Service"

    def apply(self, *, spec: ServiceSpec, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> ServiceInfo:
        """
            Create or patch the Service (read-before-create idempotent
            apply) with the automojo-managed labels attached.

            :param spec: The :class:`ServiceSpec` request payload.
            :param namespace: The target namespace.
            :param aspects: Behaviour parameters for the call.

            :returns: A :class:`ServiceInfo`.
            :raises: SemanticError, KubernetesApiError
        """
        spec.validate()

        resolved_namespace = self.client.resolve_namespace(namespace)
        logger = self._logger(aspects)

        labels = self.managed_labels(spec_name=spec.name, extra=spec.labels)

        port_entries = []
        for port_number in spec.ports:
            port_entries.append({"port": port_number, "targetPort": port_number})

        service_spec: Dict[str, object] = {
            "type": spec.service_type,
            "ports": port_entries,
        }

        if len(spec.selector) > 0:
            service_spec["selector"] = spec.selector

        body: Dict[str, object] = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": spec.name, "labels": labels},
            "spec": service_spec,
        }

        existing = self.get_existing_or_none(
            getter=lambda: self.client.core_v1_api.read_namespaced_service(
                name=spec.name,
                namespace=resolved_namespace,
                _request_timeout=aspects.timeout_seconds,
            ),
        )

        if existing is None:
            logger.log(aspects.logging_level, "Creating Service '%s'.", spec.name)
            created = self.call_sdk(
                lambda: self.client.core_v1_api.create_namespaced_service(
                    namespace=resolved_namespace,
                    body=body,
                    _request_timeout=aspects.timeout_seconds,
                ),
                description="create Service",
            )
            result = _service_info_from_sdk(created)
            return result

        existing_labels = _attr(_attr(existing, "metadata"), "labels")
        self.assert_adoptable(name=spec.name, existing_labels=existing_labels)

        logger.log(aspects.logging_level, "Patching Service '%s'.", spec.name)
        patched = self.call_sdk(
            lambda: self.client.core_v1_api.patch_namespaced_service(
                name=spec.name,
                namespace=resolved_namespace,
                body=body,
                _request_timeout=aspects.timeout_seconds,
            ),
            description="patch Service",
        )
        result = _service_info_from_sdk(patched)
        return result

    def delete(self, *, name: str, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> None:
        """
            Delete the Service. An absent Service is success.

            :param name: The Service name.
            :param namespace: The target namespace.
            :param aspects: Behaviour parameters for the call.

            :returns: ``None``
            :raises: KubernetesApiError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)
        logger = self._logger(aspects)
        logger.log(aspects.logging_level, "Deleting Service '%s'.", name)

        self.get_existing_or_none(
            getter=lambda: self.client.core_v1_api.delete_namespaced_service(
                name=name,
                namespace=resolved_namespace,
                _request_timeout=aspects.timeout_seconds,
            ),
        )
        return

    def get(self, *, name: str, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> ServiceInfo:
        """
            Read the Service and return its typed DTO.

            :param name: The Service name.
            :param namespace: The target namespace.
            :param aspects: Behaviour parameters for the call.

            :returns: A :class:`ServiceInfo`.
            :raises: KubernetesResourceNotFoundError, KubernetesApiError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)

        service_object = self.call_sdk(
            lambda: self.client.core_v1_api.read_namespaced_service(
                name=name,
                namespace=resolved_namespace,
                _request_timeout=aspects.timeout_seconds,
            ),
            description="read Service",
        )
        result = _service_info_from_sdk(service_object)
        return result

    def list(self, *, namespace: Optional[str] = None, label_selector: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> List[ServiceInfo]:
        """
            List the Services in a namespace.

            :param namespace: The target namespace.
            :param label_selector: An optional label selector.
            :param aspects: Behaviour parameters for the call.

            :returns: A list of :class:`ServiceInfo`.
            :raises: KubernetesApiError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)

        effective_selector = label_selector
        if effective_selector is None:
            effective_selector = ""

        service_list = self.call_sdk(
            lambda: self.client.core_v1_api.list_namespaced_service(
                namespace=resolved_namespace,
                label_selector=effective_selector,
                _request_timeout=aspects.timeout_seconds,
            ),
            description="list Services",
        )

        results: List[ServiceInfo] = []
        items = _attr(service_list, "items")
        if items is not None:
            for service_object in items:
                results.append(_service_info_from_sdk(service_object))

        return results


__all__ = ["ServicePrimitive"]
