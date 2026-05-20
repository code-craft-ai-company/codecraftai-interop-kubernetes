"""
    .. module:: deploymentprimitive
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Provides :class:`DeploymentPrimitive`, the typed helper for
        Kubernetes Deployments (``AppsV1Api``).

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
from automojo.interop.kubernetes.model.workloadinfo import DeploymentInfo
from automojo.interop.kubernetes.specs.workloadspecs import DeploymentSpec
from automojo.interop.kubernetes.workload.jobprimitive import _attr
from automojo.interop.kubernetes.workload.workloadprimitive import WorkloadPrimitive


def _deployment_info_from_sdk(deployment_object: object) -> DeploymentInfo:
    """
        Build a :class:`DeploymentInfo` from an SDK Deployment object.

        :param deployment_object: The SDK ``V1Deployment`` or equivalent dict.

        :returns: A populated :class:`DeploymentInfo`.
    """
    metadata = _attr(deployment_object, "metadata")
    name = _attr(metadata, "name") or ""
    namespace = _attr(metadata, "namespace") or ""
    labels = _attr(metadata, "labels") or {}

    spec = _attr(deployment_object, "spec")
    replicas = _attr(spec, "replicas") or 0

    status = _attr(deployment_object, "status")
    available = _attr(status, "available_replicas") or 0
    ready = _attr(status, "ready_replicas") or 0
    updated = _attr(status, "updated_replicas") or 0

    deployment_info = DeploymentInfo(
        name=name,
        namespace=namespace,
        replicas=replicas,
        available_replicas=available,
        ready_replicas=ready,
        updated_replicas=updated,
        labels=dict(labels),
    )
    return deployment_info


class DeploymentPrimitive(WorkloadPrimitive):
    """
        Typed helper for Kubernetes Deployments.

        Exposes ``apply`` / ``delete`` / ``get`` / ``list`` and the
        :meth:`wait_for_available` waiter.
    """

    KIND = "Deployment"

    def apply(self, *, spec: DeploymentSpec, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> DeploymentInfo:
        """
            Create or patch the Deployment (read-before-create idempotent
            apply) with the automojo-managed labels attached.

            :param spec: The :class:`DeploymentSpec` request payload.
            :param namespace: The target namespace.
            :param aspects: Behaviour parameters for the call.

            :returns: A :class:`DeploymentInfo`.
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
            "kind": "Deployment",
            "metadata": {"name": spec.name, "labels": labels},
            "spec": {
                "replicas": spec.replicas,
                "selector": {"matchLabels": labels},
                "template": {
                    "metadata": {"labels": labels},
                    "spec": pod_spec,
                },
            },
        }

        existing = self.get_existing_or_none(
            getter=lambda: self.client.apps_v1_api.read_namespaced_deployment(
                name=spec.name,
                namespace=resolved_namespace,
                _request_timeout=aspects.timeout_seconds,
            ),
        )

        if existing is None:
            logger.log(aspects.logging_level, "Creating Deployment '%s'.", spec.name)
            created = self.call_sdk(
                lambda: self.client.apps_v1_api.create_namespaced_deployment(
                    namespace=resolved_namespace,
                    body=body,
                    _request_timeout=aspects.timeout_seconds,
                ),
                description="create Deployment",
            )
            result = _deployment_info_from_sdk(created)
            return result

        existing_labels = _attr(_attr(existing, "metadata"), "labels")
        self.assert_adoptable(name=spec.name, existing_labels=existing_labels)

        logger.log(aspects.logging_level, "Patching Deployment '%s'.", spec.name)
        patched = self.call_sdk(
            lambda: self.client.apps_v1_api.patch_namespaced_deployment(
                name=spec.name,
                namespace=resolved_namespace,
                body=body,
                _request_timeout=aspects.timeout_seconds,
            ),
            description="patch Deployment",
        )
        result = _deployment_info_from_sdk(patched)
        return result

    def delete(self, *, name: str, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> None:
        """
            Delete the Deployment. An absent Deployment is success.

            :param name: The Deployment name.
            :param namespace: The target namespace.
            :param aspects: Behaviour parameters for the call.

            :returns: ``None``
            :raises: KubernetesApiError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)
        logger = self._logger(aspects)
        logger.log(aspects.logging_level, "Deleting Deployment '%s'.", name)

        self.get_existing_or_none(
            getter=lambda: self.client.apps_v1_api.delete_namespaced_deployment(
                name=name,
                namespace=resolved_namespace,
                _request_timeout=aspects.timeout_seconds,
            ),
        )
        return

    def get(self, *, name: str, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> DeploymentInfo:
        """
            Read the Deployment and return its typed DTO.

            :param name: The Deployment name.
            :param namespace: The target namespace.
            :param aspects: Behaviour parameters for the call.

            :returns: A :class:`DeploymentInfo`.
            :raises: KubernetesResourceNotFoundError, KubernetesApiError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)

        deployment_object = self.call_sdk(
            lambda: self.client.apps_v1_api.read_namespaced_deployment(
                name=name,
                namespace=resolved_namespace,
                _request_timeout=aspects.timeout_seconds,
            ),
            description="read Deployment",
        )
        result = _deployment_info_from_sdk(deployment_object)
        return result

    def list(self, *, namespace: Optional[str] = None, label_selector: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> List[DeploymentInfo]:
        """
            List the Deployments in a namespace.

            :param namespace: The target namespace.
            :param label_selector: An optional label selector.
            :param aspects: Behaviour parameters for the call.

            :returns: A list of :class:`DeploymentInfo`.
            :raises: KubernetesApiError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)

        effective_selector = label_selector
        if effective_selector is None:
            effective_selector = ""

        deployment_list = self.call_sdk(
            lambda: self.client.apps_v1_api.list_namespaced_deployment(
                namespace=resolved_namespace,
                label_selector=effective_selector,
                _request_timeout=aspects.timeout_seconds,
            ),
            description="list Deployments",
        )

        results: List[DeploymentInfo] = []
        items = _attr(deployment_list, "items")
        if items is not None:
            for deployment_object in items:
                results.append(_deployment_info_from_sdk(deployment_object))

        return results

    def wait_for_available(self, *, name: str, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> DeploymentInfo:
        """
            Block until ``status.availableReplicas == spec.replicas``.

            :param name: The Deployment name.
            :param namespace: The target namespace.
            :param aspects: Behaviour parameters for the call.

            :returns: The :class:`DeploymentInfo` observed when available.
            :raises: KubernetesWaitTimeoutError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)

        def probe():
            info = self.get(
                name=name,
                namespace=resolved_namespace,
                aspects=aspects,
            )
            if info.available_replicas >= info.replicas and info.replicas > 0:
                return (True, False, info)
            if info.replicas == 0:
                return (True, False, info)
            return (False, False, info)

        result = self.wait_until(
            probe=probe,
            aspects=aspects,
            description="Deployment '{}' availability".format(name),
        )
        return result


__all__ = ["DeploymentPrimitive"]
