"""
    .. module:: pvcprimitive
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Provides :class:`PvcPrimitive`, the typed helper for
        Kubernetes PersistentVolumeClaims (``CoreV1Api``).

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
from ccai.interop.kubernetes.model.workloadinfo import PvcInfo
from ccai.interop.kubernetes.specs.workloadspecs import PvcSpec
from ccai.interop.kubernetes.workload.jobprimitive import _attr
from ccai.interop.kubernetes.workload.workloadprimitive import WorkloadPrimitive


def _pvc_info_from_sdk(pvc_object: object) -> PvcInfo:
    """
        Build a :class:`PvcInfo` from an SDK PVC object.

        :param pvc_object: The SDK ``V1PersistentVolumeClaim`` or equivalent
            dict.

        :returns: A populated :class:`PvcInfo`.
    """
    metadata = _attr(pvc_object, "metadata")
    name = _attr(metadata, "name") or ""
    namespace = _attr(metadata, "namespace") or ""
    labels = _attr(metadata, "labels") or {}

    spec = _attr(pvc_object, "spec")
    storage_class = _attr(spec, "storage_class_name") or ""

    status = _attr(pvc_object, "status")
    phase = _attr(status, "phase") or "Pending"
    capacity_map = _attr(status, "capacity") or {}
    capacity = ""
    if isinstance(capacity_map, dict):
        capacity = capacity_map.get("storage", "") or ""

    pvc_info = PvcInfo(
        name=name,
        namespace=namespace,
        phase=phase,
        capacity=capacity,
        storage_class=storage_class,
        labels=dict(labels),
    )
    return pvc_info


class PvcPrimitive(WorkloadPrimitive):
    """
        Typed helper for Kubernetes PersistentVolumeClaims.

        Exposes ``apply`` / ``delete`` / ``get`` / ``list`` and the
        :meth:`wait_for_bound` waiter.
    """

    KIND = "PersistentVolumeClaim"

    def apply(self, *, spec: PvcSpec, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> PvcInfo:
        """
            Create or patch the PVC (read-before-create idempotent apply)
            with the codecraftai-managed labels attached.

            :param spec: The :class:`PvcSpec` request payload.
            :param namespace: The target namespace.
            :param aspects: Behaviour parameters for the call.

            :returns: A :class:`PvcInfo`.
            :raises: SemanticError, KubernetesApiError
        """
        spec.validate()

        resolved_namespace = self.client.resolve_namespace(namespace)
        logger = self._logger(aspects)

        labels = self.managed_labels(spec_name=spec.name, extra=spec.labels)

        pvc_spec: Dict[str, object] = {
            "accessModes": list(spec.access_modes),
            "resources": {"requests": {"storage": spec.storage_request}},
        }

        if spec.storage_class is not None:
            pvc_spec["storageClassName"] = spec.storage_class

        body: Dict[str, object] = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"name": spec.name, "labels": labels},
            "spec": pvc_spec,
        }

        existing = self.get_existing_or_none(
            getter=lambda: self.client.core_v1_api.read_namespaced_persistent_volume_claim(
                name=spec.name,
                namespace=resolved_namespace,
                _request_timeout=aspects.timeout_seconds,
            ),
        )

        if existing is None:
            logger.log(aspects.logging_level, "Creating PVC '%s'.", spec.name)
            created = self.call_sdk(
                lambda: self.client.core_v1_api.create_namespaced_persistent_volume_claim(
                    namespace=resolved_namespace,
                    body=body,
                    _request_timeout=aspects.timeout_seconds,
                ),
                description="create PVC",
            )
            result = _pvc_info_from_sdk(created)
            return result

        existing_labels = _attr(_attr(existing, "metadata"), "labels")
        self.assert_adoptable(name=spec.name, existing_labels=existing_labels)

        logger.log(aspects.logging_level, "Patching PVC '%s'.", spec.name)
        patch_body: Dict[str, object] = {
            "metadata": {"labels": labels},
        }
        patched = self.call_sdk(
            lambda: self.client.core_v1_api.patch_namespaced_persistent_volume_claim(
                name=spec.name,
                namespace=resolved_namespace,
                body=patch_body,
                _request_timeout=aspects.timeout_seconds,
            ),
            description="patch PVC",
        )
        result = _pvc_info_from_sdk(patched)
        return result

    def delete(self, *, name: str, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> None:
        """
            Delete the PVC. An absent PVC is success.

            :param name: The PVC name.
            :param namespace: The target namespace.
            :param aspects: Behaviour parameters for the call.

            :returns: ``None``
            :raises: KubernetesApiError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)
        logger = self._logger(aspects)
        logger.log(aspects.logging_level, "Deleting PVC '%s'.", name)

        self.get_existing_or_none(
            getter=lambda: self.client.core_v1_api.delete_namespaced_persistent_volume_claim(
                name=name,
                namespace=resolved_namespace,
                _request_timeout=aspects.timeout_seconds,
            ),
        )
        return

    def get(self, *, name: str, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> PvcInfo:
        """
            Read the PVC and return its typed DTO.

            :param name: The PVC name.
            :param namespace: The target namespace.
            :param aspects: Behaviour parameters for the call.

            :returns: A :class:`PvcInfo`.
            :raises: KubernetesResourceNotFoundError, KubernetesApiError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)

        pvc_object = self.call_sdk(
            lambda: self.client.core_v1_api.read_namespaced_persistent_volume_claim(
                name=name,
                namespace=resolved_namespace,
                _request_timeout=aspects.timeout_seconds,
            ),
            description="read PVC",
        )
        result = _pvc_info_from_sdk(pvc_object)
        return result

    def list(self, *, namespace: Optional[str] = None, label_selector: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> List[PvcInfo]:
        """
            List the PVCs in a namespace.

            :param namespace: The target namespace.
            :param label_selector: An optional label selector.
            :param aspects: Behaviour parameters for the call.

            :returns: A list of :class:`PvcInfo`.
            :raises: KubernetesApiError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)

        effective_selector = label_selector
        if effective_selector is None:
            effective_selector = ""

        pvc_list = self.call_sdk(
            lambda: self.client.core_v1_api.list_namespaced_persistent_volume_claim(
                namespace=resolved_namespace,
                label_selector=effective_selector,
                _request_timeout=aspects.timeout_seconds,
            ),
            description="list PVCs",
        )

        results: List[PvcInfo] = []
        items = _attr(pvc_list, "items")
        if items is not None:
            for pvc_object in items:
                results.append(_pvc_info_from_sdk(pvc_object))

        return results

    def wait_for_bound(self, *, name: str, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> PvcInfo:
        """
            Block until the PVC reports ``phase == Bound``.

            :param name: The PVC name.
            :param namespace: The target namespace.
            :param aspects: Behaviour parameters for the call.

            :returns: The :class:`PvcInfo` observed when bound.
            :raises: KubernetesWaitTimeoutError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)

        def probe():
            info = self.get(
                name=name,
                namespace=resolved_namespace,
                aspects=aspects,
            )
            if info.phase == "Bound":
                return (True, False, info)
            return (False, False, info)

        result = self.wait_until(
            probe=probe,
            aspects=aspects,
            description="PVC '{}' bound".format(name),
        )
        return result


__all__ = ["PvcPrimitive"]
