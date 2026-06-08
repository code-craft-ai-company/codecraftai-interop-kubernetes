"""
    .. module:: aspectskubernetes
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Provides :class:`AspectsKubernetes` and the
        ``DEFAULT_KUBERNETES_ASPECTS`` instance applied to every public
        method on :class:`KubernetesClient` and the workload primitives.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import logging

from typing import Optional

from ccai.aspects.aspects import Aspects


class AspectsKubernetes(Aspects):
    """
        Kubernetes-specialised :class:`Aspects` carrier.

        The class exists so that callers can write
        ``aspects: AspectsKubernetes`` for clarity at call sites and so
        that Kubernetes-specific behaviour parameters (the request timeout
        forwarded to the SDK, the waiter poll interval, and the structured
        logging level) carry sensible defaults without churning the public
        type signature on every primitive method.

        :ivar timeout_seconds: Per-request timeout forwarded to the SDK.
        :ivar poll_interval: Seconds between iterations of a waiter loop.
        :ivar logging_level: Standard ``logging`` level for structured logs.
    """

    def __init__(
        self,
        *,
        completion_interval: float = 2.0,
        completion_timeout: float = 600.0,
        connection_timeout: float = 30.0,
        max_attempts: int = 1,
        logger_name: Optional[str] = None,
        timeout_seconds: float = 30.0,
        poll_interval: float = 2.0,
        logging_level: int = logging.INFO,
    ) -> None:
        """
            Initialise a Kubernetes-flavoured aspects bundle.

            :param completion_interval: Seconds between completion-poll
                iterations for callers that drive a synchronous wait loop.
            :param completion_timeout: Maximum seconds to wait for
                completion before raising :class:`TimeoutError`.
            :param connection_timeout: Maximum seconds to wait for a single
                network attempt before reclassifying.
            :param max_attempts: Maximum number of attempts a caller is
                allowed to perform when reconciling against a cluster.
            :param logger_name: Optional logger name a caller can route
                logs into.
            :param timeout_seconds: Per-request timeout forwarded to the
                underlying ``kubernetes`` SDK call.
            :param poll_interval: Seconds between iterations of a waiter
                sub-loop.
            :param logging_level: Standard ``logging`` level used for the
                structured logging emitted by primitive methods.

            :returns: ``None``
        """
        super().__init__(
            completion_interval=completion_interval,
            completion_timeout=completion_timeout,
            connection_timeout=connection_timeout,
            max_attempts=max_attempts,
            logger_name=logger_name,
        )
        self.timeout_seconds = timeout_seconds
        self.poll_interval = poll_interval
        self.logging_level = logging_level
        return


DEFAULT_KUBERNETES_ASPECTS = AspectsKubernetes()


__all__ = ["AspectsKubernetes", "DEFAULT_KUBERNETES_ASPECTS"]
