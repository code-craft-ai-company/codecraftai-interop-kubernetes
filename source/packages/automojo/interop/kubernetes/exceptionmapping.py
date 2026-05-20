"""
    .. module:: exceptionmapping
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Provides the :func:`reclassify_api_exception` helper which
        translates a ``kubernetes`` SDK ``ApiException`` into the automojo
        typed exception hierarchy.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import os

from automojo.interop.kubernetes.exceptions.kuberneteserrors import (
    KubernetesApiError,
    KubernetesConflictError,
    KubernetesForbiddenError,
    KubernetesResourceNotFoundError,
    KubernetesUnauthorizedError,
)


STATUS_TO_EXCEPTION = {
    401: KubernetesUnauthorizedError,
    403: KubernetesForbiddenError,
    404: KubernetesResourceNotFoundError,
    409: KubernetesConflictError,
}


def reclassify_api_exception(api_exception: Exception) -> KubernetesApiError:
    """
        Translate a ``kubernetes`` SDK ``ApiException`` into the matching
        automojo typed exception so callers never have to inspect HTTP
        status codes.

        :param api_exception: The SDK ``ApiException`` instance to translate.

        :returns: A :class:`KubernetesApiError` (or one of its subclasses)
            that should be raised ``from api_exception`` by the caller.
    """
    status_code = getattr(api_exception, "status", None)

    if status_code is None:
        status_code = 0

    detail = getattr(api_exception, "reason", None)

    if detail is None:
        detail = str(api_exception)

    body = getattr(api_exception, "body", None)

    err_msg_lines = ["Kubernetes API request failed."]
    err_msg_lines.append("STATUS: {}".format(status_code))
    err_msg_lines.append("REASON: {}".format(detail))

    if body is not None:
        err_msg_lines.append("BODY:")
        err_msg_lines.append("    {}".format(body))

    err_msg = os.linesep.join(err_msg_lines)

    exception_type = STATUS_TO_EXCEPTION.get(status_code, KubernetesApiError)

    reclassified = exception_type(
        err_msg,
        status_code=status_code,
        detail=str(detail),
    )

    return reclassified


__all__ = ["reclassify_api_exception", "STATUS_TO_EXCEPTION"]
