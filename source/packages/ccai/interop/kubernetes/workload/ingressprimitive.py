"""
    .. module:: ingressprimitive
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Provides :class:`IngressPrimitive`, the typed helper for
        Kubernetes Ingresses (``NetworkingV1Api``).

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Dict, List, Optional

from ccai.interop.kubernetes.aspectskubernetes import (
    AspectsKubernetes,
    DEFAULT_KUBERNETES_ASPECTS,
)
from ccai.interop.kubernetes.model.workloadinfo import IngressInfo
from ccai.interop.kubernetes.specs.workloadspecs import IngressSpec
from ccai.interop.kubernetes.workload.jobprimitive import _attr
from ccai.interop.kubernetes.workload.workloadprimitive import WorkloadPrimitive


def _ingress_info_from_sdk(ingress_object: object) -> IngressInfo:
    """
        Build an :class:`IngressInfo` from an SDK Ingress object.

        :param ingress_object: The SDK ``V1Ingress`` or equivalent dict.

        :returns: A populated :class:`IngressInfo`.
    """
    metadata = _attr(ingress_object, "metadata")
    name = _attr(metadata, "name") or ""
    namespace = _attr(metadata, "namespace") or ""
    labels = _attr(metadata, "labels") or {}

    spec = _attr(ingress_object, "spec")
    hosts: List[str] = []
    rules = _attr(spec, "rules")
    if rules is not None:
        for rule_entry in rules:
            rule_host = _attr(rule_entry, "host")
            if rule_host is not None:
                hosts.append(rule_host)

    addresses: List[str] = []
    status = _attr(ingress_object, "status")
    load_balancer = _attr(status, "load_balancer")
    ingress_points = _attr(load_balancer, "ingress")
    if ingress_points is not None:
        for ingress_point in ingress_points:
            point_ip = _attr(ingress_point, "ip")
            point_host = _attr(ingress_point, "hostname")
            if point_ip is not None:
                addresses.append(point_ip)
            elif point_host is not None:
                addresses.append(point_host)

    ingress_info = IngressInfo(
        name=name,
        namespace=namespace,
        hosts=hosts,
        load_balancer_addresses=addresses,
        labels=dict(labels),
    )
    return ingress_info


class IngressPrimitive(WorkloadPrimitive):
    """
        Typed helper for Kubernetes Ingresses.

        Exposes ``apply`` / ``delete`` / ``get`` / ``list``.
    """

    KIND = "Ingress"

    def apply(self, *, spec: IngressSpec, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> IngressInfo:
        """
            Create or patch the Ingress (read-before-create idempotent
            apply) with the codecraftai-managed labels attached.

            :param spec: The :class:`IngressSpec` request payload.
            :param namespace: The target namespace.
            :param aspects: Behaviour parameters for the call.

            :returns: An :class:`IngressInfo`.
            :raises: SemanticError, KubernetesApiError
        """
        spec.validate()

        resolved_namespace = self.client.resolve_namespace(namespace)
        logger = self._logger(aspects)

        labels = self.managed_labels(spec_name=spec.name, extra=spec.labels)

        http_path: Dict[str, object] = {
            "path": spec.path,
            "pathType": "Prefix",
            "backend": {
                "service": {
                    "name": spec.service_name,
                    "port": {"number": spec.service_port},
                }
            },
        }

        ingress_spec: Dict[str, object] = {
            "rules": [
                {"host": spec.host, "http": {"paths": [http_path]}}
            ],
        }

        if spec.ingress_class is not None:
            ingress_spec["ingressClassName"] = spec.ingress_class

        body: Dict[str, object] = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {"name": spec.name, "labels": labels},
            "spec": ingress_spec,
        }

        existing = self.get_existing_or_none(
            getter=lambda: self.client.networking_v1_api.read_namespaced_ingress(
                name=spec.name,
                namespace=resolved_namespace,
                _request_timeout=aspects.timeout_seconds,
            ),
        )

        if existing is None:
            logger.log(aspects.logging_level, "Creating Ingress '%s'.", spec.name)
            created = self.call_sdk(
                lambda: self.client.networking_v1_api.create_namespaced_ingress(
                    namespace=resolved_namespace,
                    body=body,
                    _request_timeout=aspects.timeout_seconds,
                ),
                description="create Ingress",
            )
            result = _ingress_info_from_sdk(created)
            return result

        existing_labels = _attr(_attr(existing, "metadata"), "labels")
        self.assert_adoptable(name=spec.name, existing_labels=existing_labels)

        logger.log(aspects.logging_level, "Patching Ingress '%s'.", spec.name)
        patched = self.call_sdk(
            lambda: self.client.networking_v1_api.patch_namespaced_ingress(
                name=spec.name,
                namespace=resolved_namespace,
                body=body,
                _request_timeout=aspects.timeout_seconds,
            ),
            description="patch Ingress",
        )
        result = _ingress_info_from_sdk(patched)
        return result

    def delete(self, *, name: str, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> None:
        """
            Delete the Ingress. An absent Ingress is success.

            :param name: The Ingress name.
            :param namespace: The target namespace.
            :param aspects: Behaviour parameters for the call.

            :returns: ``None``
            :raises: KubernetesApiError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)
        logger = self._logger(aspects)
        logger.log(aspects.logging_level, "Deleting Ingress '%s'.", name)

        self.get_existing_or_none(
            getter=lambda: self.client.networking_v1_api.delete_namespaced_ingress(
                name=name,
                namespace=resolved_namespace,
                _request_timeout=aspects.timeout_seconds,
            ),
        )
        return

    def get(self, *, name: str, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> IngressInfo:
        """
            Read the Ingress and return its typed DTO.

            :param name: The Ingress name.
            :param namespace: The target namespace.
            :param aspects: Behaviour parameters for the call.

            :returns: An :class:`IngressInfo`.
            :raises: KubernetesResourceNotFoundError, KubernetesApiError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)

        ingress_object = self.call_sdk(
            lambda: self.client.networking_v1_api.read_namespaced_ingress(
                name=name,
                namespace=resolved_namespace,
                _request_timeout=aspects.timeout_seconds,
            ),
            description="read Ingress",
        )
        result = _ingress_info_from_sdk(ingress_object)
        return result

    def list(self, *, namespace: Optional[str] = None, label_selector: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> List[IngressInfo]:
        """
            List the Ingresses in a namespace.

            :param namespace: The target namespace.
            :param label_selector: An optional label selector.
            :param aspects: Behaviour parameters for the call.

            :returns: A list of :class:`IngressInfo`.
            :raises: KubernetesApiError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)

        effective_selector = label_selector
        if effective_selector is None:
            effective_selector = ""

        ingress_list = self.call_sdk(
            lambda: self.client.networking_v1_api.list_namespaced_ingress(
                namespace=resolved_namespace,
                label_selector=effective_selector,
                _request_timeout=aspects.timeout_seconds,
            ),
            description="list Ingresses",
        )

        results: List[IngressInfo] = []
        items = _attr(ingress_list, "items")
        if items is not None:
            for ingress_object in items:
                results.append(_ingress_info_from_sdk(ingress_object))

        return results


__all__ = ["IngressPrimitive"]
