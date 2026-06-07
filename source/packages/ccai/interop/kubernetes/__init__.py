"""
    .. module:: kubernetes
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: The ``codecraftai-interop-kubernetes`` package — the Kubernetes
        interop client for the ccai suite.

    Transport note
    --------------
    This package wraps the official ``kubernetes`` Python SDK. That SDK is
    the correct, supported transport for the Kubernetes API server, so this
    package is deliberately *not* a ``RestClientBase`` codegen package and
    introduces no parallel REST client. All public APIs normalise the SDK's
    behaviour to the ccai ``Aspects`` pattern — callers control
    timeouts, polling and logging; no ``@retry``-style decorators are used.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.interop.kubernetes.aspectskubernetes import (
    AspectsKubernetes,
    DEFAULT_KUBERNETES_ASPECTS,
)
from ccai.interop.kubernetes.kubernetesclient import (
    KubernetesClient,
    DEFAULT_NAMESPACE,
)
from ccai.interop.kubernetes.kuberneteshealth import KubernetesHealth


__all__ = [
    "AspectsKubernetes",
    "DEFAULT_KUBERNETES_ASPECTS",
    "DEFAULT_NAMESPACE",
    "KubernetesClient",
    "KubernetesHealth",
]
