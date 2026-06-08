"""
    .. module:: workloadprimitive
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Provides :class:`WorkloadPrimitive`, the abstract base for the
        typed workload helpers. It owns the cross-cutting machinery shared by
        every primitive: exception reclassification, codecraftai-managed label
        discipline, adoption prevention, the idempotent read-before-create
        apply skeleton, and the bounded waiter loop.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import logging
import os
import time

from typing import Callable, Dict, Optional, Tuple

from ccai.interop.kubernetes.aspectskubernetes import (
    AspectsKubernetes,
    DEFAULT_KUBERNETES_ASPECTS,
)
from ccai.interop.kubernetes.exceptionmapping import (
    is_api_exception,
    reclassify_api_exception,
)
from ccai.interop.kubernetes.exceptions.kuberneteserrors import (
    KubernetesConflictError,
    KubernetesResourceNotFoundError,
    KubernetesWaitTimeoutError,
)
from ccai.interop.kubernetes.workload import (
    MANAGED_LABEL_KEY,
    MANAGED_LABEL_VALUE,
    SPEC_NAME_LABEL_KEY,
)


class WorkloadPrimitive:
    """
        Abstract base for the typed workload helpers.

        Concrete subclasses (``JobPrimitive``, ``DeploymentPrimitive``, ...)
        implement the resource-kind-specific SDK calls. The base supplies the
        cross-cutting behaviour the spec mandates: typed exception
        reclassification, codecraftai-managed labelling, foreign-resource
        adoption prevention and a bounded ``Aspects``-driven waiter.

        :ivar client: The owning :class:`KubernetesClient`.
        :ivar kind: The human readable resource kind name (for messages).
    """

    KIND = "Workload"

    def __init__(self, *, client: object) -> None:
        """
            Initialise a :class:`WorkloadPrimitive`.

            :param client: The owning :class:`KubernetesClient`.

            :returns: ``None``
        """
        self.client = client
        self.kind = self.KIND
        return

    def _logger(self, aspects: AspectsKubernetes) -> logging.Logger:
        """
            Resolve the logger for a call from its aspects.

            :param aspects: The behaviour parameters for the call.

            :returns: The resolved :class:`logging.Logger`.
        """
        logger = logging.getLogger(aspects.logger_name)
        return logger

    def managed_labels(self, *, spec_name: str, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
            Compose the label map that an ``apply`` attaches to a resource.

            The codecraftai-managed labels (``ccai/managed=true`` and
            ``ccai/spec-name=<spec_name>``) are always present so a
            later reconcile can identify codecraftai-managed resources.

            :param spec_name: The name of the spec being applied.
            :param extra: Caller-supplied additional labels.

            :returns: The merged label map.
        """
        labels: Dict[str, str] = {}

        if extra is not None:
            labels.update(extra)

        labels[MANAGED_LABEL_KEY] = MANAGED_LABEL_VALUE
        labels[SPEC_NAME_LABEL_KEY] = spec_name
        return labels

    def assert_adoptable(self, *, name: str, existing_labels: Optional[Dict[str, str]]) -> None:
        """
            Verify an existing resource carries the codecraftai-managed label
            before an ``apply`` patches it, preventing accidental adoption of
            a foreign resource.

            :param name: The resource name being applied.
            :param existing_labels: The label map of the existing resource.

            :returns: ``None``
            :raises: KubernetesConflictError
        """
        carries_label = False

        if existing_labels is not None:
            label_value = existing_labels.get(MANAGED_LABEL_KEY, None)
            if label_value == MANAGED_LABEL_VALUE:
                carries_label = True

        if carries_label is False:
            err_msg_lines = [
                "Refusing to adopt a resource not managed by ccai."
            ]
            err_msg_lines.append("KIND: {}".format(self.kind))
            err_msg_lines.append("NAME: {}".format(name))
            err_msg_lines.append(
                "REASON: the existing resource does not carry the "
                "'{}={}' label.".format(MANAGED_LABEL_KEY, MANAGED_LABEL_VALUE)
            )
            err_msg = os.linesep.join(err_msg_lines)
            raise KubernetesConflictError(
                err_msg,
                status_code=409,
                detail="foreign resource adoption refused",
            ) from None

        return

    def call_sdk(self, operation: Callable, *, description: str) -> object:
        """
            Invoke an SDK operation, reclassifying any ``ApiException`` into
            the ccai typed exception hierarchy.

            :param operation: A zero-argument callable performing the SDK
                call.
            :param description: A short description of the operation, used
                for debuggability in any raised message.

            :returns: Whatever the SDK operation returns.
            :raises: KubernetesApiError
        """
        try:
            result = operation()
        except Exception as sdk_error:
            if is_api_exception(sdk_error) is False:
                raise
            reclassified = reclassify_api_exception(sdk_error)
            raise reclassified from sdk_error

        return result

    def wait_until(
        self,
        *,
        probe: Callable[[], Tuple[bool, bool, object]],
        aspects: AspectsKubernetes,
        description: str,
    ) -> object:
        """
            Drive a bounded ``Aspects``-controlled waiter loop.

            The ``probe`` callable is invoked on each iteration and returns a
            ``(done, failed, observed)`` tuple. The loop returns ``observed``
            when ``done`` is ``True``; it raises when ``failed`` is ``True``
            (the caller chooses the exception by raising inside ``probe``);
            and it raises :class:`KubernetesWaitTimeoutError` when
            ``aspects.completion_timeout`` elapses first.

            :param probe: The per-iteration probe callable returning
                ``(done, failed, observed)``.
            :param aspects: The behaviour parameters controlling the timeout
                and poll interval.
            :param description: A short description for the timeout message.

            :returns: The final observed object once ``done`` is reported.
            :raises: KubernetesWaitTimeoutError
        """
        logger = self._logger(aspects)

        deadline = time.monotonic() + aspects.completion_timeout
        last_observed: object = None

        while True:
            done, failed, observed = probe()
            last_observed = observed

            if done is True:
                return observed

            now = time.monotonic()
            if now >= deadline:
                err_msg_lines = ["Timed out waiting for a workload condition."]
                err_msg_lines.append("KIND: {}".format(self.kind))
                err_msg_lines.append("CONDITION: {}".format(description))
                err_msg_lines.append(
                    "TIMEOUT: {} seconds".format(aspects.completion_timeout)
                )
                err_msg = os.linesep.join(err_msg_lines)
                raise KubernetesWaitTimeoutError(
                    err_msg,
                    observed=last_observed,
                ) from None

            logger.log(
                aspects.logging_level,
                "Waiting for %s '%s'; polling again in %s seconds.",
                self.kind,
                description,
                aspects.poll_interval,
            )
            time.sleep(aspects.poll_interval)

    def get_existing_or_none(
        self,
        *,
        getter: Callable[[], object],
    ) -> Optional[object]:
        """
            Read a resource, returning ``None`` when it is absent rather than
            raising — the read half of read-before-create idempotent apply.

            :param getter: A zero-argument callable performing the SDK read.

            :returns: The SDK object, or ``None`` when absent.
            :raises: KubernetesApiError
        """
        try:
            existing = getter()
        except KubernetesResourceNotFoundError:
            return None
        except Exception as sdk_error:
            if is_api_exception(sdk_error) is False:
                raise
            reclassified = reclassify_api_exception(sdk_error)
            if isinstance(reclassified, KubernetesResourceNotFoundError):
                return None
            raise reclassified from sdk_error

        return existing


__all__ = ["WorkloadPrimitive", "DEFAULT_KUBERNETES_ASPECTS"]
