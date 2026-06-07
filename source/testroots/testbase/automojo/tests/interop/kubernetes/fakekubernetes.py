"""
    .. module:: fakekubernetes
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: A ``FakeKubernetesApiClient`` shim and supporting fakes that
        mimic the relevant ``kubernetes`` SDK Api classes so the test suite
        never requires a live cluster.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


class FakeApiException(Exception):
    """
        Mimics ``kubernetes.client.rest.ApiException`` for tests, carrying
        the ``status``, ``reason`` and ``body`` attributes the
        reclassification helper inspects.
    """

    def __init__(self, *, status, reason="", body=""):
        """
            Initialise a :class:`FakeApiException`.

            :param status: The HTTP status code.
            :param reason: The reason string.
            :param body: The response body.

            :returns: ``None``
        """
        super().__init__("FakeApiException status={}".format(status))
        self.status = status
        self.reason = reason
        self.body = body
        return


class FakeResourceStore:
    """
        An in-memory store of namespaced resources keyed by
        ``(namespace, name)``, used to back the fake Api facades.
    """

    def __init__(self):
        """
            Initialise an empty :class:`FakeResourceStore`.

            :returns: ``None``
        """
        self.items = {}
        self.create_calls = []
        self.patch_calls = []
        self.delete_calls = []
        return

    def key(self, namespace, name):
        """
            Compute the store key for a resource.

            :param namespace: The resource namespace.
            :param name: The resource name.

            :returns: The ``(namespace, name)`` tuple key.
        """
        composed = (namespace, name)
        return composed


class FakeNamespacedApi:
    """
        A generic fake of an SDK namespaced Api facade. The verb method names
        are supplied so a single class can stand in for ``BatchV1Api``,
        ``AppsV1Api``, ``CoreV1Api`` and ``NetworkingV1Api`` resources.
    """

    def __init__(self, *, store=None):
        """
            Initialise a :class:`FakeNamespacedApi`.

            :param store: An optional pre-populated :class:`FakeResourceStore`.

            :returns: ``None``
        """
        if store is not None:
            self.store = store
        else:
            self.store = FakeResourceStore()
        return

    def read(self, *, namespace, name):
        """
            Read a stored resource or raise a 404 fake exception.

            :param namespace: The resource namespace.
            :param name: The resource name.

            :returns: The stored resource dict.
            :raises: FakeApiException
        """
        item_key = self.store.key(namespace, name)
        if item_key not in self.store.items:
            raise FakeApiException(status=404, reason="Not Found")
        found = self.store.items[item_key]
        return found

    def create(self, *, namespace, body):
        """
            Store a new resource.

            :param namespace: The target namespace.
            :param body: The resource body dict.

            :returns: The stored resource dict.
        """
        name = body["metadata"]["name"]
        item_key = self.store.key(namespace, name)
        self.store.items[item_key] = body
        self.store.create_calls.append((namespace, name))
        return body

    def patch(self, *, namespace, name, body):
        """
            Patch an existing resource.

            :param namespace: The target namespace.
            :param name: The resource name.
            :param body: The patch body dict.

            :returns: The stored (patched) resource dict.
        """
        item_key = self.store.key(namespace, name)
        self.store.items[item_key] = body
        self.store.patch_calls.append((namespace, name))
        return body

    def delete(self, *, namespace, name):
        """
            Delete an existing resource or raise a 404 fake exception.

            :param namespace: The target namespace.
            :param name: The resource name.

            :returns: A status dict.
            :raises: FakeApiException
        """
        item_key = self.store.key(namespace, name)
        if item_key not in self.store.items:
            raise FakeApiException(status=404, reason="Not Found")
        del self.store.items[item_key]
        self.store.delete_calls.append((namespace, name))
        result = {"status": "Success"}
        return result

    def list(self, *, namespace):
        """
            List the resources stored for a namespace.

            :param namespace: The target namespace.

            :returns: A dict with an ``items`` list.
        """
        results = []
        for (item_namespace, item_name), value in self.store.items.items():
            if item_namespace == namespace:
                results.append(value)
        listing = {"items": results}
        return listing
