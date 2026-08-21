"""
    .. module:: test_waiters
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Waiter tests for the workload primitives — convergence,
        failure-raise, timeout-raise, plus a Hypothesis property test for
        the bounded wait-loop convergence.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai import testbase

from unittest.mock import MagicMock

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.interop.kubernetes.aspectskubernetes import AspectsKubernetes
from ccai.interop.kubernetes.exceptions.kuberneteserrors import (
    KubernetesJobFailedError,
    KubernetesWaitTimeoutError,
)
from ccai.interop.kubernetes.model.workloadinfo import (
    DeploymentInfo,
    JobInfo,
    PvcInfo,
)

from .fakeclient import build_fake_client


def _fast_aspects(*, completion_timeout=5.0):
    """
        Build aspects with a near-zero poll interval for fast tests.

        :param completion_timeout: The overall completion timeout.

        :returns: An :class:`AspectsKubernetes` tuned for tests.
    """
    aspects = AspectsKubernetes(
        completion_timeout=completion_timeout,
        poll_interval=0.0,
    )
    return aspects


# ----------------------------------------------------------------------
# JobWaiterTests
# ----------------------------------------------------------------------

"""
    Job wait_for_completion convergence, failure and timeout.
"""

def test_wait_converges_on_success():
    """
        wait_for_completion returns once the Job reports Succeeded.
    """
    client, facades = build_fake_client()
    sequence = [
        JobInfo(name="j", namespace="default", phase="Running",
                succeeded=0, failed=0, active=1),
        JobInfo(name="j", namespace="default", phase="Running",
                succeeded=0, failed=0, active=1),
        JobInfo(name="j", namespace="default", phase="Succeeded",
                succeeded=1, failed=0, active=0),
    ]
    client.jobs.get = MagicMock(side_effect=sequence)
    result = client.jobs.wait_for_completion(name="j", aspects=_fast_aspects())
    testbase.assert_equal(result.phase, "Succeeded")
    return

def test_wait_raises_on_failure():
    """
        wait_for_completion raises KubernetesJobFailedError on Failed.
    """
    client, facades = build_fake_client()
    failed = JobInfo(name="j", namespace="default", phase="Failed",
                     succeeded=0, failed=1, active=0)
    client.jobs.get = MagicMock(return_value=failed)
    with testbase.raises(KubernetesJobFailedError) as captured:
        client.jobs.wait_for_completion(name="j", aspects=_fast_aspects())
    testbase.assert_equal(captured.exception.info.phase, "Failed")
    return

def test_wait_times_out():
    """
        wait_for_completion raises KubernetesWaitTimeoutError when the
        Job never completes.
    """
    client, facades = build_fake_client()
    running = JobInfo(name="j", namespace="default", phase="Running",
                      succeeded=0, failed=0, active=1)
    client.jobs.get = MagicMock(return_value=running)
    with testbase.raises(KubernetesWaitTimeoutError):
        client.jobs.wait_for_completion(
            name="j",
            aspects=_fast_aspects(completion_timeout=0.05),
        )
    return


# ----------------------------------------------------------------------
# DeploymentWaiterTests
# ----------------------------------------------------------------------

"""
    Deployment wait_for_available convergence and timeout.
"""

def test_wait_converges_on_available():
    """
        wait_for_available returns when availableReplicas reaches
        spec.replicas.
    """
    client, facades = build_fake_client()
    sequence = [
        DeploymentInfo(name="d", namespace="default", replicas=3,
                       available_replicas=1, ready_replicas=1,
                       updated_replicas=1),
        DeploymentInfo(name="d", namespace="default", replicas=3,
                       available_replicas=3, ready_replicas=3,
                       updated_replicas=3),
    ]
    client.deployments.get = MagicMock(side_effect=sequence)
    result = client.deployments.wait_for_available(name="d", aspects=_fast_aspects())
    testbase.assert_equal(result.available_replicas, 3)
    return

def test_wait_times_out_when_not_available():
    """
        wait_for_available times out when the Deployment never settles.
    """
    client, facades = build_fake_client()
    info = DeploymentInfo(name="d", namespace="default", replicas=3,
                          available_replicas=1, ready_replicas=1,
                          updated_replicas=1)
    client.deployments.get = MagicMock(return_value=info)
    with testbase.raises(KubernetesWaitTimeoutError):
        client.deployments.wait_for_available(
            name="d",
            aspects=_fast_aspects(completion_timeout=0.05),
        )
    return


# ----------------------------------------------------------------------
# PvcWaiterTests
# ----------------------------------------------------------------------

"""
    PVC wait_for_bound convergence.
"""

def test_wait_converges_on_bound():
    """
        wait_for_bound returns once the PVC reports Bound.
    """
    client, facades = build_fake_client()
    sequence = [
        PvcInfo(name="p", namespace="default", phase="Pending"),
        PvcInfo(name="p", namespace="default", phase="Bound",
                capacity="50Gi"),
    ]
    client.pvcs.get = MagicMock(side_effect=sequence)
    result = client.pvcs.wait_for_bound(name="p", aspects=_fast_aspects())
    testbase.assert_equal(result.phase, "Bound")
    return


# ----------------------------------------------------------------------
# WaitLoopConvergencePropertyTests
# ----------------------------------------------------------------------

"""
    Hypothesis property test over the bounded wait-loop convergence.
"""

@given(
constraints={"max_examples": 40},
    iterations_until_done=st.integers(min_value=1, max_value=20),
)
def test_loop_converges_after_n_probes(iterations_until_done):
    """
        A wait loop driven by a probe that reports done after N
        iterations converges exactly when the probe does, regardless of
        N, given an ample timeout.
    """
    client, facades = build_fake_client()
    states = []
    for index in range(iterations_until_done):
        is_done = index == (iterations_until_done - 1)
        phase = "Succeeded" if is_done else "Running"
        succeeded = 1 if is_done else 0
        states.append(
            JobInfo(name="j", namespace="default", phase=phase,
                    succeeded=succeeded, failed=0, active=0)
        )
    client.jobs.get = MagicMock(side_effect=states)
    result = client.jobs.wait_for_completion(
        name="j",
        aspects=_fast_aspects(completion_timeout=60.0),
    )
    testbase.assert_equal(result.phase, "Succeeded")
    testbase.assert_equal(client.jobs.get.call_count, iterations_until_done)
    return
