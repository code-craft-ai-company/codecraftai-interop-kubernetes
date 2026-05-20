"""
    .. module:: test_kubeconfigloader
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for :class:`KubeConfigLoader` covering path, in-memory
        dict and in-cluster sources, source validation, and context
        enumeration.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import os
import tempfile
import unittest

from automojo.errors.exceptions import SemanticError

from automojo.interop.kubernetes.kubeconfigloader import KubeConfigLoader


_KUBECONFIG_DICT = {
    "apiVersion": "v1",
    "kind": "Config",
    "current-context": "ctx-alpha",
    "clusters": [
        {
            "name": "cluster-alpha",
            "cluster": {"server": "https://10.0.0.1:6443",
                        "insecure-skip-tls-verify": True},
        },
    ],
    "users": [
        {"name": "user-alpha", "user": {"token": "fake-token"}},
    ],
    "contexts": [
        {"name": "ctx-alpha",
         "context": {"cluster": "cluster-alpha", "user": "user-alpha"}},
        {"name": "ctx-beta",
         "context": {"cluster": "cluster-alpha", "user": "user-alpha"}},
    ],
}


class SourceValidationTests(unittest.TestCase):
    """
        Source validation — zero and multiple sources raise SemanticError.
    """

    def test_no_source_raises(self):
        """
            Supplying no source raises SemanticError.
        """
        with self.assertRaises(SemanticError):
            KubeConfigLoader()
        return

    def test_multiple_sources_raise(self):
        """
            Supplying multiple sources raises SemanticError.
        """
        with self.assertRaises(SemanticError):
            KubeConfigLoader(
                kubeconfig_path="/tmp/x",
                kubeconfig_dict=_KUBECONFIG_DICT,
            )
        return


class DictSourceTests(unittest.TestCase):
    """
        In-memory dict source — context enumeration and api client build.
    """

    def test_available_contexts_from_dict(self):
        """
            A dict-source loader enumerates its contexts.
        """
        loader = KubeConfigLoader(kubeconfig_dict=_KUBECONFIG_DICT)
        contexts = loader.available_contexts()
        self.assertEqual(sorted(contexts), ["ctx-alpha", "ctx-beta"])
        return

    def test_build_api_client_from_dict(self):
        """
            A dict-source loader builds a usable ApiClient.
        """
        loader = KubeConfigLoader(kubeconfig_dict=_KUBECONFIG_DICT)
        api_client = loader.build_api_client()
        self.assertIsNotNone(api_client)
        return


class PathSourceTests(unittest.TestCase):
    """
        Kubeconfig path source — context enumeration and api client build.
    """

    def test_available_contexts_from_path(self):
        """
            A path-source loader enumerates its contexts from disk.
        """
        import yaml

        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        )
        try:
            yaml.safe_dump(_KUBECONFIG_DICT, handle)
            handle.close()
            loader = KubeConfigLoader(kubeconfig_path=handle.name)
            contexts = loader.available_contexts()
            self.assertEqual(sorted(contexts), ["ctx-alpha", "ctx-beta"])
        finally:
            os.unlink(handle.name)
        return

    def test_build_api_client_from_path(self):
        """
            A path-source loader builds a usable ApiClient from disk.
        """
        import yaml

        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        )
        try:
            yaml.safe_dump(_KUBECONFIG_DICT, handle)
            handle.close()
            loader = KubeConfigLoader(kubeconfig_path=handle.name)
            api_client = loader.build_api_client()
            self.assertIsNotNone(api_client)
        finally:
            os.unlink(handle.name)
        return


class InClusterSourceTests(unittest.TestCase):
    """
        In-cluster source — context enumeration yields an empty list.
    """

    def test_in_cluster_has_no_contexts(self):
        """
            An in-cluster loader reports no contexts.
        """
        loader = KubeConfigLoader(in_cluster=True)
        self.assertEqual(loader.available_contexts(), [])
        return


if __name__ == "__main__":
    unittest.main()
