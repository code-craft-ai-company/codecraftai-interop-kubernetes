"""
    .. module:: namespaceprimitive
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Provides :class:`NamespacePrimitive`, the typed helper for
        cluster-scoped Kubernetes Namespaces (``CoreV1Api``).

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
from automojo.interop.kubernetes.model.workloadinfo import NamespaceInfo
from automojo.interop.kubernetes.specs.workloadspecs import NamespaceSpec
from automojo.interop.kubernetes.workload.jobprimitive import _attr
from automojo.interop.kubernetes.workload.workloadprimitive import WorkloadPrimitive


def _namespace_info_from_sdk(namespace_object: object) -> NamespaceInfo:
    """
        Build a :class:`NamespaceInfo` from an SDK Namespace object.

        :param namespace_object: The SDK ``V1Namespace`` or equivalent dict.

        :returns: A populated :class:`NamespaceInfo`.
    """
    metadata = _attr(namespace_object, "metadata")
    name = _attr(metadata, "name") or ""
    labels = _attr(metadata, "labels") or {}

    status = _attr(namespace_object, "status")
    phase = _attr(status, "phase") or "Active"

    namespace_info = NamespaceInfo(
        name=name,
        phase=phase,
        labels=dict(labels),
    )
    return namespace_info


class NamespacePrimitive(WorkloadPrimitive):
    """
        Typed helper for cluster-scoped Kubernetes Namespaces.

        Exposes ``apply`` / ``delete`` / ``get`` / ``list``. Namespaces are
        cluster-scoped, so none of these verbs accept a ``namespace``
        argument.
    """

    KIND = "Namespace"

    def apply(self, *, spec: NamespaceSpec, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> NamespaceInfo:
        """
            Create or patch the Namespace (read-before-create idempotent
            apply) with the automojo-managed labels attached.

            :param spec: The :class:`NamespaceSpec` request payload.
            :param aspects: Behaviour parameters for the call.

            :returns: A :class:`NamespaceInfo`.
            :raises: SemanticError, KubernetesApiError
        """
        spec.validate()

        logger = self._logger(aspects)
        labels = self.managed_labels(spec_name=spec.name, extra=spec.labels)

        body: Dict[str, object] = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {"name": spec.name, "labels": labels},
        }

        existing = self.get_existing_or_none(
            getter=lambda: self.client.core_v1_api.read_namespace(
                name=spec.name,
                _request_timeout=aspects.timeout_seconds,
            ),
        )

        if existing is None:
            logger.log(aspects.logging_level, "Creating Namespace '%s'.", spec.name)
            created = self.call_sdk(
                lambda: self.client.core_v1_api.create_namespace(
                    body=body,
                    _request_timeout=aspects.timeout_seconds,
                ),
                description="create Namespace",
            )
            result = _namespace_info_from_sdk(created)
            return result

        existing_labels = _attr(_attr(existing, "metadata"), "labels")
        self.assert_adoptable(name=spec.name, existing_labels=existing_labels)

        logger.log(aspects.logging_level, "Patching Namespace '%s'.", spec.name)
        patched = self.call_sdk(
            lambda: self.client.core_v1_api.patch_namespace(
                name=spec.name,
                body=body,
                _request_timeout=aspects.timeout_seconds,
            ),
            description="patch Namespace",
        )
        result = _namespace_info_from_sdk(patched)
        return result

    def delete(self, *, name: str, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> None:
        """
            Delete the Namespace. An absent Namespace is success.

            :param name: The Namespace name.
            :param aspects: Behaviour parameters for the call.

            :returns: ``None``
            :raises: KubernetesApiError
        """
        logger = self._logger(aspects)
        logger.log(aspects.logging_level, "Deleting Namespace '%s'.", name)

        self.get_existing_or_none(
            getter=lambda: self.client.core_v1_api.delete_namespace(
                name=name,
                _request_timeout=aspects.timeout_seconds,
            ),
        )
        return

    def get(self, *, name: str, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> NamespaceInfo:
        """
            Read the Namespace and return its typed DTO.

            :param name: The Namespace name.
            :param aspects: Behaviour parameters for the call.

            :returns: A :class:`NamespaceInfo`.
            :raises: KubernetesResourceNotFoundError, KubernetesApiError
        """
        namespace_object = self.call_sdk(
            lambda: self.client.core_v1_api.read_namespace(
                name=name,
                _request_timeout=aspects.timeout_seconds,
            ),
            description="read Namespace",
        )
        result = _namespace_info_from_sdk(namespace_object)
        return result

    def list(self, *, label_selector: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> List[NamespaceInfo]:
        """
            List the Namespaces on the cluster.

            :param label_selector: An optional label selector.
            :param aspects: Behaviour parameters for the call.

            :returns: A list of :class:`NamespaceInfo`.
            :raises: KubernetesApiError
        """
        effective_selector = label_selector
        if effective_selector is None:
            effective_selector = ""

        namespace_list = self.call_sdk(
            lambda: self.client.core_v1_api.list_namespace(
                label_selector=effective_selector,
                _request_timeout=aspects.timeout_seconds,
            ),
            description="list Namespaces",
        )

        results: List[NamespaceInfo] = []
        items = _attr(namespace_list, "items")
        if items is not None:
            for namespace_object in items:
                results.append(_namespace_info_from_sdk(namespace_object))

        return results


__all__ = ["NamespacePrimitive"]
