"""
    .. module:: test_namespace_and_nodes
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for the cluster-scoped Namespace primitive and the
        NodePool / Node query surface on :class:`KubernetesClient`.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai import testbase

from unittest.mock import MagicMock

from ccai.interop.kubernetes.exceptions.kuberneteserrors import (
    KubernetesConflictError,
)
from ccai.interop.kubernetes.model.nodeinfo import NodeInfo
from ccai.interop.kubernetes.specs.workloadspecs import NamespaceSpec
from ccai.interop.kubernetes.workload import MANAGED_LABEL_KEY

from .fakeclient import build_fake_client


def _fake_node(*, name, ready, labels):
    """
        Build a fake SDK V1Node-like object.

        :param name: The node name.
        :param ready: Whether the node reports Ready.
        :param labels: The node label map.

        :returns: A MagicMock standing in for a V1Node.
    """
    node = MagicMock()
    node.metadata = MagicMock()
    node.metadata.name = name
    node.metadata.labels = labels
    node.spec = MagicMock()
    node.spec.unschedulable = False
    node.status = MagicMock()
    node.status.allocatable = {"cpu": "8", "nvidia.com/gpu": "1"}
    condition = MagicMock()
    condition.type = "Ready"
    condition.status = "True" if ready else "False"
    node.status.conditions = [condition]
    return node


# ----------------------------------------------------------------------
# NamespacePrimitiveTests
# ----------------------------------------------------------------------

"""
    Namespace primitive apply / get / list / delete / adoption.
"""

def _bind_namespace_store(client):
    """
        Bind an in-memory namespace store onto the client's core api.

        :param client: The KubernetesClient under test.

        :returns: The backing store dict.
    """
    store = {}

    def do_read(*, name, **kwargs):
        from .fakekubernetes import (
            FakeApiException,
        )
        if name not in store:
            raise FakeApiException(status=404, reason="Not Found")
        return store[name]

    def do_create(*, body, **kwargs):
        store[body["metadata"]["name"]] = body
        return body

    def do_patch(*, name, body, **kwargs):
        store[name] = body
        return body

    def do_delete(*, name, **kwargs):
        from .fakekubernetes import (
            FakeApiException,
        )
        if name not in store:
            raise FakeApiException(status=404, reason="Not Found")
        del store[name]
        return {"status": "Success"}

    def do_list(**kwargs):
        return {"items": list(store.values())}

    client.core_v1_api.read_namespace = MagicMock(side_effect=do_read)
    client.core_v1_api.create_namespace = MagicMock(side_effect=do_create)
    client.core_v1_api.patch_namespace = MagicMock(side_effect=do_patch)
    client.core_v1_api.delete_namespace = MagicMock(side_effect=do_delete)
    client.core_v1_api.list_namespace = MagicMock(side_effect=do_list)
    return store

def test_apply_creates_namespace():
    """
        apply creates an absent Namespace with managed labels.
    """
    client, facades = build_fake_client()
    store = _bind_namespace_store(client)
    info = client.namespaces.apply(spec=NamespaceSpec(name="team-ml"))
    testbase.assert_equal(info.name, "team-ml")
    labels = store["team-ml"]["metadata"]["labels"]
    testbase.assert_equal(labels[MANAGED_LABEL_KEY], "true")
    return

def test_apply_twice_is_idempotent():
    """
        A second Namespace apply patches rather than re-creating.
    """
    client, facades = build_fake_client()
    _bind_namespace_store(client)
    client.namespaces.apply(spec=NamespaceSpec(name="team-ml"))
    client.namespaces.apply(spec=NamespaceSpec(name="team-ml"))
    testbase.assert_equal(client.core_v1_api.create_namespace.call_count, 1)
    testbase.assert_equal(client.core_v1_api.patch_namespace.call_count, 1)
    return

def test_apply_against_unmanaged_raises():
    """
        apply against a foreign Namespace raises KubernetesConflictError.
    """
    client, facades = build_fake_client()
    store = _bind_namespace_store(client)
    store["kube-system"] = {"metadata": {"name": "kube-system", "labels": {}}}
    with testbase.raises(KubernetesConflictError):
        client.namespaces.apply(spec=NamespaceSpec(name="kube-system"))
    return


# ----------------------------------------------------------------------
# NodeQueryTests
# ----------------------------------------------------------------------

"""
    NodePool / Node query surface on the client.
"""

def test_list_nodes_returns_typed_dtos():
    """
        list_nodes returns typed NodeInfo DTOs.
    """
    client, facades = build_fake_client()
    node_list = MagicMock()
    node_list.items = [
        _fake_node(name="gpu-1", ready=True, labels={"pool": "h100"}),
        _fake_node(name="gpu-2", ready=False, labels={"pool": "h100"}),
    ]
    client.core_v1_api.list_node = MagicMock(return_value=node_list)
    nodes = client.list_nodes(label_selector="pool=h100")
    testbase.assert_equal(len(nodes), 2)
    testbase.assert_true(isinstance(nodes[0], NodeInfo))
    ready_states = sorted([node.ready for node in nodes])
    testbase.assert_equal(ready_states, [False, True])
    return

def test_list_nodes_forwards_label_selector():
    """
        list_nodes forwards the label selector to the SDK.
    """
    client, facades = build_fake_client()
    node_list = MagicMock()
    node_list.items = []
    client.core_v1_api.list_node = MagicMock(return_value=node_list)
    client.list_nodes(label_selector="pool=h100")
    call_kwargs = client.core_v1_api.list_node.call_args.kwargs
    testbase.assert_equal(call_kwargs["label_selector"], "pool=h100")
    return
