"""
    .. module:: statefulsetprimitive
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Provides :class:`StatefulSetPrimitive`, the typed helper for
        Kubernetes StatefulSets (``AppsV1Api``).

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
from ccai.interop.kubernetes.model.workloadinfo import StatefulSetInfo
from ccai.interop.kubernetes.specs.workloadspecs import StatefulSetSpec
from ccai.interop.kubernetes.workload.jobprimitive import _attr
from ccai.interop.kubernetes.workload.workloadprimitive import WorkloadPrimitive


def _statefulset_info_from_sdk(statefulset_object: object) -> StatefulSetInfo:
    """
        Build a :class:`StatefulSetInfo` from an SDK StatefulSet object.

        :param statefulset_object: The SDK ``V1StatefulSet`` or equivalent
            dict.

        :returns: A populated :class:`StatefulSetInfo`.
    """
    metadata = _attr(statefulset_object, "metadata")
    name = _attr(metadata, "name") or ""
    namespace = _attr(metadata, "namespace") or ""
    labels = _attr(metadata, "labels") or {}

    spec = _attr(statefulset_object, "spec")
    replicas = _attr(spec, "replicas") or 0

    status = _attr(statefulset_object, "status")
    ready = _attr(status, "ready_replicas") or 0
    current = _attr(status, "current_replicas") or 0

    statefulset_info = StatefulSetInfo(
        name=name,
        namespace=namespace,
        replicas=replicas,
        ready_replicas=ready,
        current_replicas=current,
        labels=dict(labels),
    )
    return statefulset_info


class StatefulSetPrimitive(WorkloadPrimitive):
    """
        Typed helper for Kubernetes StatefulSets.

        Exposes ``apply`` / ``delete`` / ``get`` / ``list`` and the
        :meth:`wait_for_ready` waiter.
    """

    KIND = "StatefulSet"

    def apply(self, *, spec: StatefulSetSpec, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> StatefulSetInfo:
        """
            Create or patch the StatefulSet (read-before-create idempotent
            apply) with the codecraftai-managed labels attached.

            :param spec: The :class:`StatefulSetSpec` request payload.
            :param namespace: The target namespace.
            :param aspects: Behaviour parameters for the call.

            :returns: A :class:`StatefulSetInfo`.
            :raises: SemanticError, KubernetesApiError
        """
        spec.validate()

        resolved_namespace = self.client.resolve_namespace(namespace)
        logger = self._logger(aspects)

        labels = self.managed_labels(spec_name=spec.name, extra=spec.labels)

        env_list = []
        for env_key in sorted(spec.env.keys()):
            env_list.append({"name": env_key, "value": spec.env[env_key]})

        container: Dict[str, object] = {"name": spec.name, "image": spec.image}

        if spec.container_port is not None:
            container["ports"] = [{"containerPort": spec.container_port}]

        if len(env_list) > 0:
            container["env"] = env_list

        if len(spec.resources) > 0:
            container["resources"] = spec.resources

        pod_spec: Dict[str, object] = {"containers": [container]}
        if len(spec.node_selector) > 0:
            pod_spec["nodeSelector"] = spec.node_selector

        body: Dict[str, object] = {
            "apiVersion": "apps/v1",
            "kind": "StatefulSet",
            "metadata": {"name": spec.name, "labels": labels},
            "spec": {
                "replicas": spec.replicas,
                "serviceName": spec.service_name,
                "selector": {"matchLabels": labels},
                "template": {
                    "metadata": {"labels": labels},
                    "spec": pod_spec,
                },
            },
        }

        existing = self.get_existing_or_none(
            getter=lambda: self.client.apps_v1_api.read_namespaced_stateful_set(
                name=spec.name,
                namespace=resolved_namespace,
                timeout_seconds=aspects.timeout_seconds,
            ),
        )

        if existing is None:
            logger.log(aspects.logging_level, "Creating StatefulSet '%s'.", spec.name)
            created = self.call_sdk(
                lambda: self.client.apps_v1_api.create_namespaced_stateful_set(
                    namespace=resolved_namespace,
                    body=body,
                    timeout_seconds=aspects.timeout_seconds,
                ),
                description="create StatefulSet",
            )
            result = _statefulset_info_from_sdk(created)
            return result

        existing_labels = _attr(_attr(existing, "metadata"), "labels")
        self.assert_adoptable(name=spec.name, existing_labels=existing_labels)

        logger.log(aspects.logging_level, "Patching StatefulSet '%s'.", spec.name)
        patched = self.call_sdk(
            lambda: self.client.apps_v1_api.patch_namespaced_stateful_set(
                name=spec.name,
                namespace=resolved_namespace,
                body=body,
                timeout_seconds=aspects.timeout_seconds,
            ),
            description="patch StatefulSet",
        )
        result = _statefulset_info_from_sdk(patched)
        return result

    def delete(self, *, name: str, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> None:
        """
            Delete the StatefulSet. An absent StatefulSet is success.

            :param name: The StatefulSet name.
            :param namespace: The target namespace.
            :param aspects: Behaviour parameters for the call.

            :returns: ``None``
            :raises: KubernetesApiError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)
        logger = self._logger(aspects)
        logger.log(aspects.logging_level, "Deleting StatefulSet '%s'.", name)

        self.get_existing_or_none(
            getter=lambda: self.client.apps_v1_api.delete_namespaced_stateful_set(
                name=name,
                namespace=resolved_namespace,
                timeout_seconds=aspects.timeout_seconds,
            ),
        )
        return

    def get(self, *, name: str, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> StatefulSetInfo:
        """
            Read the StatefulSet and return its typed DTO.

            :param name: The StatefulSet name.
            :param namespace: The target namespace.
            :param aspects: Behaviour parameters for the call.

            :returns: A :class:`StatefulSetInfo`.
            :raises: KubernetesResourceNotFoundError, KubernetesApiError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)

        statefulset_object = self.call_sdk(
            lambda: self.client.apps_v1_api.read_namespaced_stateful_set(
                name=name,
                namespace=resolved_namespace,
                timeout_seconds=aspects.timeout_seconds,
            ),
            description="read StatefulSet",
        )
        result = _statefulset_info_from_sdk(statefulset_object)
        return result

    def list(self, *, namespace: Optional[str] = None, label_selector: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> List[StatefulSetInfo]:
        """
            List the StatefulSets in a namespace.

            :param namespace: The target namespace.
            :param label_selector: An optional label selector.
            :param aspects: Behaviour parameters for the call.

            :returns: A list of :class:`StatefulSetInfo`.
            :raises: KubernetesApiError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)

        effective_selector = label_selector
        if effective_selector is None:
            effective_selector = ""

        statefulset_list = self.call_sdk(
            lambda: self.client.apps_v1_api.list_namespaced_stateful_set(
                namespace=resolved_namespace,
                label_selector=effective_selector,
                timeout_seconds=aspects.timeout_seconds,
            ),
            description="list StatefulSets",
        )

        results: List[StatefulSetInfo] = []
        items = _attr(statefulset_list, "items")
        if items is not None:
            for statefulset_object in items:
                results.append(_statefulset_info_from_sdk(statefulset_object))

        return results

    def wait_for_ready(self, *, name: str, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> StatefulSetInfo:
        """
            Block until ``status.readyReplicas == spec.replicas``.

            :param name: The StatefulSet name.
            :param namespace: The target namespace.
            :param aspects: Behaviour parameters for the call.

            :returns: The :class:`StatefulSetInfo` observed when ready.
            :raises: KubernetesWaitTimeoutError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)

        def probe():
            info = self.get(
                name=name,
                namespace=resolved_namespace,
                aspects=aspects,
            )
            if info.replicas == 0:
                return (True, False, info)
            if info.ready_replicas >= info.replicas:
                return (True, False, info)
            return (False, False, info)

        result = self.wait_until(
            probe=probe,
            aspects=aspects,
            description="StatefulSet '{}' readiness".format(name),
        )
        return result


__all__ = ["StatefulSetPrimitive"]
