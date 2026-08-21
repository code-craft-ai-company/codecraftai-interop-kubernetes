"""
    .. module:: test_workloadprimitives
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: CRUD, idempotency, adoption-prevention and spec-validation
        tests for the workload primitives.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai import testbase

from ccai.errors.exceptions import SemanticError

from ccai.interop.kubernetes.exceptions.kuberneteserrors import (
    KubernetesApiError,
    KubernetesConflictError,
    KubernetesResourceNotFoundError,
)
from ccai.interop.kubernetes.specs.workloadspecs import (
    DeploymentSpec,
    IngressSpec,
    JobSpec,
    PvcSpec,
    ServiceSpec,
    StatefulSetSpec,
)
from ccai.interop.kubernetes.workload import MANAGED_LABEL_KEY, SPEC_NAME_LABEL_KEY
from ccai.interop.kubernetes.workload.workloadprimitive import (
    WorkloadPrimitive,
)

from .fakeclient import build_fake_client
from .fakekubernetes import FakeApiException


# ----------------------------------------------------------------------
# JobPrimitiveTests
# ----------------------------------------------------------------------

"""
    CRUD, idempotency, adoption-prevention for the Job primitive.
"""

def test_job_primitive_tests_apply_creates():
    """
        apply creates an absent Job and attaches managed labels.
    """
    client, facades = build_fake_client()
    spec = JobSpec(name="trainer", image="busybox:latest")
    info = client.jobs.apply(spec=spec)
    testbase.assert_equal(info.name, "trainer")
    testbase.assert_equal(facades["job"].api.store.create_calls, [("default", "trainer")])
    stored = facades["job"].api.store.items[("default", "trainer")]
    labels = stored["metadata"]["labels"]
    testbase.assert_equal(labels[MANAGED_LABEL_KEY], "true")
    testbase.assert_equal(labels[SPEC_NAME_LABEL_KEY], "trainer")
    return

def test_job_primitive_tests_apply_twice_is_idempotent():
    """
        A second apply patches rather than re-creating.
    """
    client, facades = build_fake_client()
    spec = JobSpec(name="trainer", image="busybox:latest")
    client.jobs.apply(spec=spec)
    client.jobs.apply(spec=spec)
    store = facades["job"].api.store
    testbase.assert_equal(len(store.create_calls), 1)
    testbase.assert_equal(len(store.patch_calls), 1)
    return

def test_job_primitive_tests_apply_against_unmanaged_raises():
    """
        apply against a foreign resource raises KubernetesConflictError.
    """
    client, facades = build_fake_client()
    facades["job"].api.store.items[("default", "foreign")] = {
        "metadata": {"name": "foreign", "labels": {"owner": "someone-else"}}
    }
    spec = JobSpec(name="foreign", image="busybox:latest")
    with testbase.raises(KubernetesConflictError):
        client.jobs.apply(spec=spec)
    return

def test_job_primitive_tests_get_missing_raises_not_found():
    """
        get of an absent Job raises KubernetesResourceNotFoundError.
    """
    client, facades = build_fake_client()
    with testbase.raises(KubernetesResourceNotFoundError):
        client.jobs.get(name="absent")
    return

def test_job_primitive_tests_delete_is_idempotent():
    """
        delete of an absent Job returns without raising.
    """
    client, facades = build_fake_client()
    client.jobs.delete(name="absent")
    return

def test_job_primitive_tests_list_returns_typed_dtos():
    """
        list returns the typed JobInfo DTOs.
    """
    client, facades = build_fake_client()
    client.jobs.apply(spec=JobSpec(name="a", image="busybox"))
    client.jobs.apply(spec=JobSpec(name="b", image="busybox"))
    listing = client.jobs.list()
    names = sorted([item.name for item in listing])
    testbase.assert_equal(names, ["a", "b"])
    return


# ----------------------------------------------------------------------
# DeploymentPrimitiveTests
# ----------------------------------------------------------------------

"""
    CRUD and adoption-prevention for the Deployment primitive.
"""

def test_deployment_primitive_tests_apply_creates_and_patches():
    """
        apply creates then patches a Deployment.
    """
    client, facades = build_fake_client()
    spec = DeploymentSpec(name="api", image="nginx", replicas=2)
    client.deployments.apply(spec=spec)
    client.deployments.apply(spec=spec)
    store = facades["deployment"].api.store
    testbase.assert_equal(len(store.create_calls), 1)
    testbase.assert_equal(len(store.patch_calls), 1)
    return

def test_deployment_primitive_tests_apply_against_unmanaged_raises():
    """
        apply against a foreign Deployment raises KubernetesConflictError.
    """
    client, facades = build_fake_client()
    facades["deployment"].api.store.items[("default", "api")] = {
        "metadata": {"name": "api", "labels": {}}
    }
    with testbase.raises(KubernetesConflictError):
        client.deployments.apply(spec=DeploymentSpec(name="api", image="nginx"))
    return


# ----------------------------------------------------------------------
# StatefulSetPrimitiveTests
# ----------------------------------------------------------------------

"""
    CRUD for the StatefulSet primitive.
"""

def test_stateful_set_primitive_tests_apply_and_get():
    """
        apply then get returns the typed StatefulSetInfo.
    """
    client, facades = build_fake_client()
    spec = StatefulSetSpec(name="db", image="postgres", service_name="db-svc")
    client.statefulsets.apply(spec=spec)
    info = client.statefulsets.get(name="db")
    testbase.assert_equal(info.name, "db")
    return


# ----------------------------------------------------------------------
# PvcPrimitiveTests
# ----------------------------------------------------------------------

"""
    CRUD for the PVC primitive.
"""

def test_apply_and_list():
    """
        apply then list returns the typed PvcInfo.
    """
    client, facades = build_fake_client()
    spec = PvcSpec(name="data", storage_request="50Gi")
    client.pvcs.apply(spec=spec)
    listing = client.pvcs.list()
    testbase.assert_equal(len(listing), 1)
    testbase.assert_equal(listing[0].name, "data")
    return


# ----------------------------------------------------------------------
# ServicePrimitiveTests
# ----------------------------------------------------------------------

"""
    CRUD for the Service primitive.
"""

def test_apply_and_delete():
    """
        apply then delete leaves no Service stored.
    """
    client, facades = build_fake_client()
    spec = ServiceSpec(name="web", ports=[80, 443])
    client.services.apply(spec=spec)
    client.services.delete(name="web")
    testbase.assert_equal(len(facades["service"].api.store.items), 0)
    return


# ----------------------------------------------------------------------
# IngressPrimitiveTests
# ----------------------------------------------------------------------

"""
    CRUD for the Ingress primitive.
"""

def test_ingress_primitive_tests_apply_and_get():
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
    testbase.assert_equal(info.name, "edge")
    testbase.assert_true("app.example.com" in info.hosts)
    return


# ----------------------------------------------------------------------
# SpecValidationTests
# ----------------------------------------------------------------------

"""
    Missing-required-field validation raises SemanticError.
"""

def test_job_spec_missing_image_raises():
    """
        A JobSpec missing its image raises SemanticError on apply.
    """
    client, facades = build_fake_client()
    spec = JobSpec(name="x", image="busybox")
    spec.image = None
    with testbase.raises(SemanticError):
        client.jobs.apply(spec=spec)
    return

def test_pvc_spec_missing_storage_raises():
    """
        A PvcSpec missing its storage request raises SemanticError.
    """
    client, facades = build_fake_client()
    spec = PvcSpec(name="x", storage_request="10Gi")
    spec.storage_request = None
    with testbase.raises(SemanticError):
        client.pvcs.apply(spec=spec)
    return


# ----------------------------------------------------------------------
# CallSdkExceptionDisciplineTests
# ----------------------------------------------------------------------

"""
    Regression for NR-H3 / NR-H4: ``call_sdk`` and
    ``get_existing_or_none`` must only reclassify genuine SDK
    ``ApiException`` instances. ``SemanticError``, ``TypeError`` and
    other programming-defect errors must bubble untouched.
"""

def test_call_sdk_reclassifies_api_exception():
    """
        A genuine ApiException is reclassified into KubernetesApiError.
    """
    primitive = WorkloadPrimitive(client=object())

    def _operation():
        raise FakeApiException(status=500, reason="boom")

    with testbase.raises(KubernetesApiError):
        primitive.call_sdk(_operation, description="op")
    return

def test_call_sdk_lets_semantic_error_bubble():
    """
        A SemanticError must NOT be reclassified by call_sdk.
    """
    primitive = WorkloadPrimitive(client=object())

    def _operation():
        raise SemanticError("misused API")

    with testbase.raises(SemanticError):
        primitive.call_sdk(_operation, description="op")
    return

def test_call_sdk_lets_type_error_bubble():
    """
        An ordinary TypeError bug must NOT become a KubernetesApiError.
    """
    primitive = WorkloadPrimitive(client=object())

    def _operation():
        raise TypeError("programming defect")

    with testbase.raises(TypeError):
        primitive.call_sdk(_operation, description="op")
    return

def test_get_existing_or_none_lets_semantic_error_bubble():
    """
        get_existing_or_none must not swallow a SemanticError as absent.
    """
    primitive = WorkloadPrimitive(client=object())

    def _getter():
        raise SemanticError("misused API")

    with testbase.raises(SemanticError):
        primitive.get_existing_or_none(getter=_getter)
    return

def test_get_existing_or_none_lets_type_error_bubble():
    """
        get_existing_or_none must not turn a TypeError into "absent".
    """
    primitive = WorkloadPrimitive(client=object())

    def _getter():
        raise TypeError("programming defect")

    with testbase.raises(TypeError):
        primitive.get_existing_or_none(getter=_getter)
    return

def test_get_existing_or_none_returns_none_on_api_not_found():
    """
        A 404 ApiException is still mapped to None (resource absent).
    """
    primitive = WorkloadPrimitive(client=object())

    def _getter():
        raise FakeApiException(status=404, reason="Not Found")

    result = primitive.get_existing_or_none(getter=_getter)
    testbase.assert_true(result is None)
    return
