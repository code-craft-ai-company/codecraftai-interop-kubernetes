"""
    .. module:: fakeclient
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Builds a :class:`KubernetesClient` whose SDK Api facades are
        replaced with :class:`unittest.mock.MagicMock` resource stores. No
        live cluster is ever touched.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from unittest.mock import MagicMock

from automojo.tests.interop.kubernetes.fakekubernetes import (
    FakeApiException,
    FakeNamespacedApi,
)


class ResourceFacade:
    """
        Backs a set of SDK verb method names against a single
        :class:`FakeNamespacedApi` resource store.

        :ivar api: The underlying :class:`FakeNamespacedApi`.
    """

    def __init__(self, *, read_name, create_name, patch_name, delete_name, list_name):
        """
            Initialise a :class:`ResourceFacade`.

            :param read_name: The SDK read method name.
            :param create_name: The SDK create method name.
            :param patch_name: The SDK patch method name.
            :param delete_name: The SDK delete method name.
            :param list_name: The SDK list method name.

            :returns: ``None``
        """
        self.api = FakeNamespacedApi()
        self.read_name = read_name
        self.create_name = create_name
        self.patch_name = patch_name
        self.delete_name = delete_name
        self.list_name = list_name
        return

    def bind(self, target):
        """
            Bind the verb methods onto a ``MagicMock`` SDK Api facade.

            :param target: The ``MagicMock`` to bind the verbs onto.

            :returns: ``None``
        """
        def do_read(*, name, namespace, **kwargs):
            result = self.api.read(namespace=namespace, name=name)
            return result

        def do_create(*, namespace, body, **kwargs):
            result = self.api.create(namespace=namespace, body=body)
            return result

        def do_patch(*, name, namespace, body, **kwargs):
            result = self.api.patch(namespace=namespace, name=name, body=body)
            return result

        def do_delete(*, name, namespace, **kwargs):
            result = self.api.delete(namespace=namespace, name=name)
            return result

        def do_list(*, namespace, **kwargs):
            result = self.api.list(namespace=namespace)
            return result

        setattr(target, self.read_name, MagicMock(side_effect=do_read))
        setattr(target, self.create_name, MagicMock(side_effect=do_create))
        setattr(target, self.patch_name, MagicMock(side_effect=do_patch))
        setattr(target, self.delete_name, MagicMock(side_effect=do_delete))
        setattr(target, self.list_name, MagicMock(side_effect=do_list))
        return


def build_fake_client(*, namespace="default"):
    """
        Construct a :class:`KubernetesClient` with all SDK Api facades
        replaced by fakes.

        :param namespace: The default namespace for the client.

        :returns: A tuple of ``(client, facades)`` where ``facades`` is a
            dict of named :class:`ResourceFacade` objects keyed by resource
            kind.
    """
    from automojo.interop.kubernetes.kubernetesclient import KubernetesClient

    client = KubernetesClient(
        kubeconfig_dict={"_fake": True},
        namespace=namespace,
        api_client=MagicMock(name="api_client"),
    )

    facades = {}

    facades["job"] = ResourceFacade(
        read_name="read_namespaced_job",
        create_name="create_namespaced_job",
        patch_name="patch_namespaced_job",
        delete_name="delete_namespaced_job",
        list_name="list_namespaced_job",
    )
    facades["deployment"] = ResourceFacade(
        read_name="read_namespaced_deployment",
        create_name="create_namespaced_deployment",
        patch_name="patch_namespaced_deployment",
        delete_name="delete_namespaced_deployment",
        list_name="list_namespaced_deployment",
    )
    facades["statefulset"] = ResourceFacade(
        read_name="read_namespaced_stateful_set",
        create_name="create_namespaced_stateful_set",
        patch_name="patch_namespaced_stateful_set",
        delete_name="delete_namespaced_stateful_set",
        list_name="list_namespaced_stateful_set",
    )
    facades["pvc"] = ResourceFacade(
        read_name="read_namespaced_persistent_volume_claim",
        create_name="create_namespaced_persistent_volume_claim",
        patch_name="patch_namespaced_persistent_volume_claim",
        delete_name="delete_namespaced_persistent_volume_claim",
        list_name="list_namespaced_persistent_volume_claim",
    )
    facades["service"] = ResourceFacade(
        read_name="read_namespaced_service",
        create_name="create_namespaced_service",
        patch_name="patch_namespaced_service",
        delete_name="delete_namespaced_service",
        list_name="list_namespaced_service",
    )
    facades["ingress"] = ResourceFacade(
        read_name="read_namespaced_ingress",
        create_name="create_namespaced_ingress",
        patch_name="patch_namespaced_ingress",
        delete_name="delete_namespaced_ingress",
        list_name="list_namespaced_ingress",
    )

    batch_api = MagicMock(name="batch_v1_api")
    apps_api = MagicMock(name="apps_v1_api")
    core_api = MagicMock(name="core_v1_api")
    networking_api = MagicMock(name="networking_v1_api")

    facades["job"].bind(batch_api)
    facades["deployment"].bind(apps_api)
    facades["statefulset"].bind(apps_api)
    facades["pvc"].bind(core_api)
    facades["service"].bind(core_api)
    facades["ingress"].bind(networking_api)

    client.batch_v1_api = batch_api
    client.apps_v1_api = apps_api
    client.core_v1_api = core_api
    client.networking_v1_api = networking_api

    return client, facades


__all__ = ["build_fake_client", "ResourceFacade", "FakeApiException"]
