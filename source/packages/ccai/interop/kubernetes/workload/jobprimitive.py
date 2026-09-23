"""
    .. module:: jobprimitive
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Provides :class:`JobPrimitive`, the typed helper for
        Kubernetes Jobs (``BatchV1Api``).

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import os

from typing import Dict, List, Optional

from ccai.interop.kubernetes.aspectskubernetes import (
    AspectsKubernetes,
    DEFAULT_KUBERNETES_ASPECTS,
)
from ccai.interop.kubernetes.exceptions.kuberneteserrors import (
    KubernetesJobFailedError,
)
from ccai.interop.kubernetes.model.workloadinfo import JobInfo
from ccai.interop.kubernetes.specs.workloadspecs import JobSpec
from ccai.interop.kubernetes.workload.workloadprimitive import WorkloadPrimitive


def _build_container(spec: JobSpec) -> Dict[str, object]:
    """
        Build the container fragment of a Job pod template from a
        :class:`JobSpec`.

        :param spec: The validated :class:`JobSpec`.

        :returns: The container dict.
    """
    env_list = []
    for env_key in sorted(spec.env.keys()):
        env_list.append({"name": env_key, "value": spec.env[env_key]})

    container: Dict[str, object] = {
        "name": spec.name,
        "image": spec.image,
    }

    if len(spec.command) > 0:
        container["command"] = list(spec.command)

    if len(spec.args) > 0:
        container["args"] = list(spec.args)

    if len(env_list) > 0:
        container["env"] = env_list

    if len(spec.resources) > 0:
        container["resources"] = spec.resources

    return container


def _job_info_from_sdk(job_object: object) -> JobInfo:
    """
        Build a :class:`JobInfo` DTO from an SDK Job object (or a dict).

        :param job_object: The SDK ``V1Job`` instance or equivalent dict.

        :returns: A populated :class:`JobInfo`.
    """
    metadata = _attr(job_object, "metadata")
    name = _attr(metadata, "name") or ""
    namespace = _attr(metadata, "namespace") or ""
    labels = _attr(metadata, "labels") or {}

    status = _attr(job_object, "status")
    succeeded = _attr(status, "succeeded") or 0
    failed = _attr(status, "failed") or 0
    active = _attr(status, "active") or 0
    start_time = _attr(status, "start_time")
    completion_time = _attr(status, "completion_time")

    if failed > 0:
        phase = "Failed"
    elif succeeded > 0:
        phase = "Succeeded"
    else:
        phase = "Running"

    job_info = JobInfo(
        name=name,
        namespace=namespace,
        phase=phase,
        succeeded=succeeded,
        failed=failed,
        active=active,
        start_time=start_time,
        completion_time=completion_time,
        labels=dict(labels),
    )
    return job_info


def _attr(source: object, name: str) -> object:
    """
        Read an attribute from an SDK object or a key from a dict.

        :param source: The SDK object or dict.
        :param name: The attribute / key name.

        :returns: The value, or ``None`` when absent.
    """
    if source is None:
        return None

    if isinstance(source, dict):
        return source.get(name, None)

    return getattr(source, name, None)


class JobPrimitive(WorkloadPrimitive):
    """
        Typed helper for Kubernetes Jobs.

        Exposes ``apply`` / ``delete`` / ``get`` / ``list`` and the
        :meth:`wait_for_completion` waiter.
    """

    KIND = "Job"

    def apply(self, *, spec: JobSpec, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> JobInfo:
        """
            Create the Job if absent, or patch it if present (read-before-
            create idempotent apply). The codecraftai-managed labels are always
            attached. An existing Job lacking the managed label triggers a
            :class:`KubernetesConflictError`.

            :param spec: The :class:`JobSpec` request payload.
            :param namespace: The target namespace; defaults to the client
                default.
            :param aspects: Behaviour parameters for the call.

            :returns: A :class:`JobInfo` describing the applied Job.
            :raises: SemanticError, KubernetesApiError
        """
        spec.validate()

        resolved_namespace = self.client.resolve_namespace(namespace)
        logger = self._logger(aspects)

        labels = self.managed_labels(spec_name=spec.name, extra=spec.labels)

        pod_spec: Dict[str, object] = {
            "containers": [_build_container(spec)],
            "restartPolicy": spec.restart_policy,
        }

        if len(spec.node_selector) > 0:
            pod_spec["nodeSelector"] = spec.node_selector

        body: Dict[str, object] = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {"name": spec.name, "labels": labels},
            "spec": {
                "backoffLimit": spec.backoff_limit,
                "completions": spec.completions,
                "parallelism": spec.parallelism,
                "template": {
                    "metadata": {"labels": labels},
                    "spec": pod_spec,
                },
            },
        }

        existing = self.get_existing_or_none(
            getter=lambda: self.client.batch_v1_api.read_namespaced_job(
                name=spec.name,
                namespace=resolved_namespace,
                timeout_seconds=aspects.timeout_seconds,
            ),
        )

        if existing is None:
            logger.log(aspects.logging_level, "Creating Job '%s'.", spec.name)
            created = self.call_sdk(
                lambda: self.client.batch_v1_api.create_namespaced_job(
                    namespace=resolved_namespace,
                    body=body,
                    timeout_seconds=aspects.timeout_seconds,
                ),
                description="create Job",
            )
            result = _job_info_from_sdk(created)
            return result

        existing_labels = _attr(_attr(existing, "metadata"), "labels")
        self.assert_adoptable(name=spec.name, existing_labels=existing_labels)

        logger.log(aspects.logging_level, "Patching existing Job '%s'.", spec.name)
        patched = self.call_sdk(
            lambda: self.client.batch_v1_api.patch_namespaced_job(
                name=spec.name,
                namespace=resolved_namespace,
                body=body,
                timeout_seconds=aspects.timeout_seconds,
            ),
            description="patch Job",
        )
        result = _job_info_from_sdk(patched)
        return result

    def delete(self, *, name: str, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> None:
        """
            Delete the Job. An absent Job is treated as success (idempotent
            delete).

            :param name: The Job name.
            :param namespace: The target namespace.
            :param aspects: Behaviour parameters for the call.

            :returns: ``None``
            :raises: KubernetesApiError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)
        logger = self._logger(aspects)
        logger.log(aspects.logging_level, "Deleting Job '%s'.", name)

        outcome = self.get_existing_or_none(
            getter=lambda: self.client.batch_v1_api.delete_namespaced_job(
                name=name,
                namespace=resolved_namespace,
                timeout_seconds=aspects.timeout_seconds,
            ),
        )

        if outcome is None:
            logger.log(aspects.logging_level, "Job '%s' already absent.", name)

        return

    def get(self, *, name: str, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> JobInfo:
        """
            Read the Job and return its typed DTO.

            :param name: The Job name.
            :param namespace: The target namespace.
            :param aspects: Behaviour parameters for the call.

            :returns: A :class:`JobInfo`.
            :raises: KubernetesResourceNotFoundError, KubernetesApiError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)

        job_object = self.call_sdk(
            lambda: self.client.batch_v1_api.read_namespaced_job(
                name=name,
                namespace=resolved_namespace,
                timeout_seconds=aspects.timeout_seconds,
            ),
            description="read Job",
        )
        result = _job_info_from_sdk(job_object)
        return result

    def list(self, *, namespace: Optional[str] = None, label_selector: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> List[JobInfo]:
        """
            List the Jobs in a namespace.

            :param namespace: The target namespace.
            :param label_selector: An optional label selector.
            :param aspects: Behaviour parameters for the call.

            :returns: A list of :class:`JobInfo`.
            :raises: KubernetesApiError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)

        effective_selector = label_selector
        if effective_selector is None:
            effective_selector = ""

        job_list = self.call_sdk(
            lambda: self.client.batch_v1_api.list_namespaced_job(
                namespace=resolved_namespace,
                label_selector=effective_selector,
                timeout_seconds=aspects.timeout_seconds,
            ),
            description="list Jobs",
        )

        results: List[JobInfo] = []
        items = _attr(job_list, "items")
        if items is not None:
            for job_object in items:
                results.append(_job_info_from_sdk(job_object))

        return results

    def wait_for_completion(self, *, name: str, namespace: Optional[str] = None, aspects: AspectsKubernetes = DEFAULT_KUBERNETES_ASPECTS) -> JobInfo:
        """
            Block until the Job reports ``Succeeded`` or ``Failed``.

            :param name: The Job name.
            :param namespace: The target namespace.
            :param aspects: Behaviour parameters controlling the timeout and
                poll interval.

            :returns: The :class:`JobInfo` observed at completion.
            :raises: KubernetesJobFailedError, KubernetesWaitTimeoutError
        """
        resolved_namespace = self.client.resolve_namespace(namespace)

        def probe():
            job_info = self.get(
                name=name,
                namespace=resolved_namespace,
                aspects=aspects,
            )

            if job_info.phase == "Failed":
                err_msg_lines = ["The Kubernetes Job transitioned to Failed."]
                err_msg_lines.append("JOB: {}".format(name))
                err_msg_lines.append("NAMESPACE: {}".format(resolved_namespace))
                err_msg_lines.append("FAILED PODS: {}".format(job_info.failed))
                err_msg = os.linesep.join(err_msg_lines)
                raise KubernetesJobFailedError(err_msg, info=job_info) from None

            if job_info.phase == "Succeeded":
                return (True, False, job_info)

            return (False, False, job_info)

        result = self.wait_until(
            probe=probe,
            aspects=aspects,
            description="Job '{}' completion".format(name),
        )
        return result


__all__ = ["JobPrimitive"]
