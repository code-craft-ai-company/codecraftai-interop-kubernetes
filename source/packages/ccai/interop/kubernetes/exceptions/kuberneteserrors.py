"""
    .. module:: kuberneteserrors
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Defines the typed exception hierarchy raised by
        :class:`KubernetesClient` and the workload primitives. The hierarchy
        shields callers from the underlying SDK's ``ApiException`` status
        codes.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Optional


class KubernetesApiError(Exception):
    """
        Base error for every failure reclassified from the underlying
        ``kubernetes`` SDK ``ApiException``.

        :ivar status_code: The HTTP status code reported by the API server.
        :ivar detail: The human readable detail message from the API server.
    """

    def __init__(self, message: str, *, status_code: int, detail: str) -> None:
        """
            Initialise a :class:`KubernetesApiError`.

            :param message: The summary message describing the failure.
            :param status_code: The HTTP status code reported by the API
                server.
            :param detail: The detail message reported by the API server.

            :returns: ``None``
        """
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail
        return


class KubernetesUnauthorizedError(KubernetesApiError):
    """
        Raised when the API server reports a 401 (authentication failure).
    """


class KubernetesForbiddenError(KubernetesApiError):
    """
        Raised when the API server reports a 403 (authorisation failure).
    """


class KubernetesResourceNotFoundError(KubernetesApiError):
    """
        Raised when the API server reports a 404 (resource absent).
    """


class KubernetesConflictError(KubernetesApiError):
    """
        Raised when the API server reports a 409 (resource conflict). Also
        raised by the workload primitives when an ``apply`` would adopt a
        foreign, non-codecraftai-managed resource.
    """


class KubernetesJobFailedError(Exception):
    """
        Raised by :meth:`JobPrimitive.wait_for_completion` when the observed
        Job transitions to a ``Failed`` state.

        :ivar info: The :class:`JobInfo` DTO observed at the time of failure.
    """

    def __init__(self, message: str, *, info: object) -> None:
        """
            Initialise a :class:`KubernetesJobFailedError`.

            :param message: The summary message describing the failure.
            :param info: The :class:`JobInfo` DTO observed at failure time.

            :returns: ``None``
        """
        super().__init__(message)
        self.info = info
        return


class KubernetesWaitTimeoutError(TimeoutError):
    """
        Raised by a workload primitive waiter when the resource does not
        reach the awaited state within ``aspects.completion_timeout``.

        :ivar observed: The last observed DTO or status object, retained for
            debuggability.
    """

    def __init__(self, message: str, *, observed: Optional[object] = None) -> None:
        """
            Initialise a :class:`KubernetesWaitTimeoutError`.

            :param message: The summary message describing the timeout.
            :param observed: The last observed status object.

            :returns: ``None``
        """
        super().__init__(message)
        self.observed = observed
        return


__all__ = [
    "KubernetesApiError",
    "KubernetesConflictError",
    "KubernetesForbiddenError",
    "KubernetesJobFailedError",
    "KubernetesResourceNotFoundError",
    "KubernetesUnauthorizedError",
    "KubernetesWaitTimeoutError",
]
