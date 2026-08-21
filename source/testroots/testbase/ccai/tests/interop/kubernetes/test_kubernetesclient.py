"""
    .. module:: test_kubernetesclient
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Construction, namespace, context and health probe tests for
        :class:`KubernetesClient`.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai import testbase

from unittest.mock import MagicMock

from ccai.errors.exceptions import SemanticError

from ccai.interop.kubernetes.aspectskubernetes import DEFAULT_KUBERNETES_ASPECTS
from ccai.interop.kubernetes.kubernetesclient import KubernetesClient
from ccai.interop.kubernetes.kuberneteshealth import KubernetesHealth
from ccai.interop.kubernetes.exceptions.kuberneteserrors import (
    KubernetesResourceNotFoundError,
)


def _client_with_dict():
    """
        Build a client from an in-memory kubeconfig dict with an injected
        api_client.

        :returns: A constructed :class:`KubernetesClient`.
    """
    built = KubernetesClient(
        kubeconfig_dict={"_fake": True},
        api_client=MagicMock(),
    )
    return built


# ----------------------------------------------------------------------
# ConstructionValidationTests
# ----------------------------------------------------------------------

"""
    Construction validation — three valid paths plus zero and multiple.
"""

def test_construct_from_kubeconfig_dict():
    """
        A kubeconfig dict source constructs successfully.
    """
    client = _client_with_dict()
    testbase.assert_true(isinstance(client, KubernetesClient))
    return

def test_construct_from_kubeconfig_path():
    """
        A kubeconfig path source constructs successfully when an
        api_client is injected (no file is read).
    """
    client = KubernetesClient(
        kubeconfig_path="/tmp/nonexistent-kubeconfig",
        api_client=MagicMock(),
    )
    testbase.assert_true(isinstance(client, KubernetesClient))
    return

def test_construct_in_cluster():
    """
        An in-cluster source constructs successfully when an api_client
        is injected.
    """
    client = KubernetesClient(
        in_cluster=True,
        api_client=MagicMock(),
    )
    testbase.assert_true(isinstance(client, KubernetesClient))
    return

def test_construct_with_no_source_raises():
    """
        Supplying no kubeconfig source raises SemanticError.
    """
    with testbase.raises(SemanticError):
        KubernetesClient(api_client=MagicMock())
    return

def test_construct_with_multiple_sources_raises():
    """
        Supplying multiple kubeconfig sources raises SemanticError.
    """
    with testbase.raises(SemanticError):
        KubernetesClient(
            kubeconfig_dict={"_fake": True},
            in_cluster=True,
            api_client=MagicMock(),
        )
    return


# ----------------------------------------------------------------------
# NamespaceTests
# ----------------------------------------------------------------------

"""
    Namespace defaulting and switching.
"""

def test_default_namespace():
    """
        The client defaults to the 'default' namespace.
    """
    client = _client_with_dict()
    testbase.assert_equal(client.namespace, "default")
    testbase.assert_equal(client.resolve_namespace(None), "default")
    return

def test_resolve_namespace_explicit():
    """
        An explicit namespace argument overrides the default.
    """
    client = _client_with_dict()
    testbase.assert_equal(client.resolve_namespace("teamx"), "teamx")
    return

def test_use_namespace_switches_default():
    """
        use_namespace updates the client-wide default namespace.
    """
    client = _client_with_dict()
    client.use_namespace("workloads")
    testbase.assert_equal(client.namespace, "workloads")
    testbase.assert_equal(client.resolve_namespace(None), "workloads")
    return


# ----------------------------------------------------------------------
# ContextTests
# ----------------------------------------------------------------------

"""
    Context switching, including unknown-context raising.
"""

def test_use_context_unknown_raises():
    """
        Switching to an unknown context raises
        KubernetesResourceNotFoundError.
    """
    client = _client_with_dict()
    client._loader.available_contexts = MagicMock(return_value=["alpha"])
    with testbase.raises(KubernetesResourceNotFoundError):
        client.use_context("does-not-exist")
    return

def test_use_context_known_switches():
    """
        Switching to a known context updates the active context.
    """
    client = _client_with_dict()
    client._loader.available_contexts = MagicMock(return_value=["alpha", "beta"])
    client._loader.build_api_client = MagicMock(return_value=MagicMock())
    client.use_context("beta")
    testbase.assert_equal(client.context, "beta")
    return


# ----------------------------------------------------------------------
# HealthProbeTests
# ----------------------------------------------------------------------

"""
    Health probe — reachable, unreachable, partial info.
"""

def test_health_reachable():
    """
        A reachable cluster reports reachable, version and node count.
    """
    client = _client_with_dict()
    version_info = MagicMock()
    version_info.git_version = "v1.29.3"
    client.version_api = MagicMock()
    client.version_api.get_code = MagicMock(return_value=version_info)

    node_list = MagicMock()
    node_list.items = [MagicMock(), MagicMock(), MagicMock()]
    client.core_v1_api = MagicMock()
    client.core_v1_api.list_node = MagicMock(return_value=node_list)

    health = client.health()
    testbase.assert_true(isinstance(health, KubernetesHealth))
    testbase.assert_true(health.reachable)
    testbase.assert_equal(health.version, "v1.29.3")
    testbase.assert_equal(health.node_count, 3)
    return

def test_health_unreachable():
    """
        An unreachable cluster reports a non-raising negative health.
    """
    client = _client_with_dict()
    client.version_api = MagicMock()
    client.version_api.get_code = MagicMock(side_effect=RuntimeError("boom"))

    health = client.health()
    testbase.assert_false(health.reachable)
    testbase.assert_equal(health.version, "")
    testbase.assert_equal(health.node_count, 0)
    return

def test_health_partial_no_node_permission():
    """
        A reachable cluster where node listing fails reports reachable
        with a zero node count.
    """
    client = _client_with_dict()
    version_info = MagicMock()
    version_info.git_version = "v1.30.0"
    client.version_api = MagicMock()
    client.version_api.get_code = MagicMock(return_value=version_info)
    client.core_v1_api = MagicMock()
    client.core_v1_api.list_node = MagicMock(side_effect=RuntimeError("forbidden"))

    health = client.health()
    testbase.assert_true(health.reachable)
    testbase.assert_equal(health.version, "v1.30.0")
    testbase.assert_equal(health.node_count, 0)
    return


# ----------------------------------------------------------------------
# AspectsForwardingTests
# ----------------------------------------------------------------------

"""
    Aspects forwarding — health forwards the request timeout to the SDK.
"""

def test_health_forwards_timeout():
    """
        health forwards aspects.timeout_seconds as the SDK request
        timeout.
    """
    client = _client_with_dict()
    version_info = MagicMock()
    version_info.git_version = "v1.29.0"
    client.version_api = MagicMock()
    client.version_api.get_code = MagicMock(return_value=version_info)
    node_list = MagicMock()
    node_list.items = []
    client.core_v1_api = MagicMock()
    client.core_v1_api.list_node = MagicMock(return_value=node_list)

    client.health(aspects=DEFAULT_KUBERNETES_ASPECTS)

    call_kwargs = client.version_api.get_code.call_args.kwargs
    # The REST transport names this 'timeout_seconds'; the SDK called it
    # '_request_timeout'.
    testbase.assert_equal(
        call_kwargs["timeout_seconds"],
        DEFAULT_KUBERNETES_ASPECTS.timeout_seconds,
    )
    return
