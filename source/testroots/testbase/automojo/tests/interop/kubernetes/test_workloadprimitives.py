"""
    .. module:: test_workloadprimitives
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: CRUD, idempotency, adoption-prevention and spec-validation
        tests for the workload primitives.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import unittest

from automojo.errors.exceptions import SemanticError

from automojo.interop.kubernetes.exceptions.kuberneteserrors import (
    KubernetesConflictError,
    KubernetesResourceNotFoundError,
)
from automojo.interop.kubernetes.specs.workloadspecs import (
    DeploymentSpec,
    IngressSpec,
    JobSpec,
    PvcSpec,
    ServiceSpec,
    StatefulSetSpec,
)
from automojo.interop.kubernetes.workload import MANAGED_LABEL_KEY, SPEC_NAME_LABEL_KEY

from automojo.tests.interop.kubernetes.fakeclient import build_fake_client


class JobPrimitiveTests(unittest.TestCase):
    """
        CRUD, idempotency, adoption-prevention for the Job primitive.
    """

    def test_apply_creates(self):
        """
            apply creates an absent Job and attaches managed labels.
        """
        client, facades = build_fake_client()
        spec = JobSpec(name="trainer", image="busybox:latest")
        info = client.jobs.apply(spec=spec)
        self.assertEqual(info.name, "trainer")
        self.assertEqual(facades["job"].api.store.create_calls, [("default", "trainer")])
        stored = facades["job"].api.store.items[("default", "trainer")]
        labels = stored["metadata"]["labels"]
        self.assertEqual(labels[MANAGED_LABEL_KEY], "true")
        self.assertEqual(labels[SPEC_NAME_LABEL_KEY], "trainer")
        return

    def test_apply_twice_is_idempotent(self):
        """
            A second apply patches rather than re-creating.
        """
        client, facades = build_fake_client()
        spec = JobSpec(name="trainer", image="busybox:latest")
        client.jobs.apply(spec=spec)
        client.jobs.apply(spec=spec)
        store = facades["job"].api.store
        self.assertEqual(len(store.create_calls), 1)
        self.assertEqual(len(store.patch_calls), 1)
        return

    def test_apply_against_unmanaged_raises(self):
        """
            apply against a foreign resource raises KubernetesConflictError.
        """
        client, facades = build_fake_client()
        facades["job"].api.store.items[("default", "foreign")] = {
            "metadata": {"name": "foreign", "labels": {"owner": "someone-else"}}
        }
        spec = JobSpec(name="foreign", image="busybox:latest")
        with self.assertRaises(KubernetesConflictError):
            client.jobs.apply(spec=spec)
        return

    def test_get_missing_raises_not_found(self):
        """
            get of an absent Job raises KubernetesResourceNotFoundError.
        """
        client, facades = build_fake_client()
        with self.assertRaises(KubernetesResourceNotFoundError):
            client.jobs.get(name="absent")
        return

    def test_delete_is_idempotent(self):
        """
            delete of an absent Job returns without raising.
        """
        client, facades = build_fake_client()
        client.jobs.delete(name="absent")
        return

    def test_list_returns_typed_dtos(self):
        """
            list returns the typed JobInfo DTOs.
        """
        client, facades = build_fake_client()
        client.jobs.apply(spec=JobSpec(name="a", image="busybox"))
        client.jobs.apply(spec=JobSpec(name="b", image="busybox"))
        listing = client.jobs.list()
        names = sorted([item.name for item in listing])
        self.assertEqual(names, ["a", "b"])
        return


class DeploymentPrimitiveTests(unittest.TestCase):
    """
        CRUD and adoption-prevention for the Deployment primitive.
    """

    def test_apply_creates_and_patches(self):
        """
            apply creates then patches a Deployment.
        """
        client, facades = build_fake_client()
        spec = DeploymentSpec(name="api", image="nginx", replicas=2)
        client.deployments.apply(spec=spec)
        client.deployments.apply(spec=spec)
        store = facades["deployment"].api.store
        self.assertEqual(len(store.create_calls), 1)
        self.assertEqual(len(store.patch_calls), 1)
        return

    def test_apply_against_unmanaged_raises(self):
        """
            apply against a foreign Deployment raises KubernetesConflictError.
        """
        client, facades = build_fake_client()
        facades["deployment"].api.store.items[("default", "api")] = {
            "metadata": {"name": "api", "labels": {}}
        }
        with self.assertRaises(KubernetesConflictError):
            client.deployments.apply(spec=DeploymentSpec(name="api", image="nginx"))
        return


class StatefulSetPrimitiveTests(unittest.TestCase):
    """
        CRUD for the StatefulSet primitive.
    """

    def test_apply_and_get(self):
        """
            apply then get returns the typed StatefulSetInfo.
        """
        client, facades = build_fake_client()
        spec = StatefulSetSpec(name="db", image="postgres", service_name="db-svc")
        client.statefulsets.apply(spec=spec)
        info = client.statefulsets.get(name="db")
        self.assertEqual(info.name, "db")
        return


class PvcPrimitiveTests(unittest.TestCase):
    """
        CRUD for the PVC primitive.
    """

    def test_apply_and_list(self):
        """
            apply then list returns the typed PvcInfo.
        """
        client, facades = build_fake_client()
        spec = PvcSpec(name="data", storage_request="50Gi")
        client.pvcs.apply(spec=spec)
        listing = client.pvcs.list()
        self.assertEqual(len(listing), 1)
        self.assertEqual(listing[0].name, "data")
        return


class ServicePrimitiveTests(unittest.TestCase):
    """
        CRUD for the Service primitive.
    """

    def test_apply_and_delete(self):
        """
            apply then delete leaves no Service stored.
        """
        client, facades = build_fake_client()
        spec = ServiceSpec(name="web", ports=[80, 443])
        client.services.apply(spec=spec)
        client.services.delete(name="web")
        self.assertEqual(len(facades["service"].api.store.items), 0)
        return


class IngressPrimitiveTests(unittest.TestCase):
    """
        CRUD for the Ingress primitive.
    """

    def test_apply_and_get(self):
        """
            apply then get returns the typed IngressInfo with the host.
        """
        client, facades = build_fake_client()
        spec = IngressSpec(
            name="edge",
            host="app.example.com",
            service_name="web",
            service_port=80,
        )
        client.ingresses.apply(spec=spec)
        info = client.ingresses.get(name="edge")
        self.assertEqual(info.name, "edge")
        self.assertIn("app.example.com", info.hosts)
        return


class SpecValidationTests(unittest.TestCase):
    """
        Missing-required-field validation raises SemanticError.
    """

    def test_job_spec_missing_image_raises(self):
        """
            A JobSpec missing its image raises SemanticError on apply.
        """
        client, facades = build_fake_client()
        spec = JobSpec(name="x", image="busybox")
        spec.image = None
        with self.assertRaises(SemanticError):
            client.jobs.apply(spec=spec)
        return

    def test_pvc_spec_missing_storage_raises(self):
        """
            A PvcSpec missing its storage request raises SemanticError.
        """
        client, facades = build_fake_client()
        spec = PvcSpec(name="x", storage_request="10Gi")
        spec.storage_request = None
        with self.assertRaises(SemanticError):
            client.pvcs.apply(spec=spec)
        return


if __name__ == "__main__":
    unittest.main()
