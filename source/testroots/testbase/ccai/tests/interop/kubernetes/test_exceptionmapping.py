"""
    .. module:: test_exceptionmapping
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Table-driven exception reclassification tests for
        :func:`reclassify_api_exception`.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import unittest

from ccai.interop.kubernetes.exceptionmapping import reclassify_api_exception
from ccai.interop.kubernetes.exceptions.kuberneteserrors import (
    KubernetesApiError,
    KubernetesConflictError,
    KubernetesForbiddenError,
    KubernetesResourceNotFoundError,
    KubernetesUnauthorizedError,
)

from ccai.tests.interop.kubernetes.fakekubernetes import FakeApiException


class ExceptionReclassificationTests(unittest.TestCase):
    """
        Table-driven reclassification over the documented status codes.
    """

    def test_status_code_mapping(self):
        """
            Each documented status code reclassifies into its named type.
        """
        cases = [
            (401, KubernetesUnauthorizedError),
            (403, KubernetesForbiddenError),
            (404, KubernetesResourceNotFoundError),
            (409, KubernetesConflictError),
            (500, KubernetesApiError),
            (422, KubernetesApiError),
        ]

        for status_code, expected_type in cases:
            api_exception = FakeApiException(
                status=status_code,
                reason="reason-{}".format(status_code),
                body="body",
            )
            reclassified = reclassify_api_exception(api_exception)
            self.assertIsInstance(reclassified, expected_type)
            self.assertEqual(reclassified.status_code, status_code)
        return

    def test_reclassified_carries_detail(self):
        """
            The reclassified exception carries the API server detail.
        """
        api_exception = FakeApiException(status=404, reason="Not Found", body="x")
        reclassified = reclassify_api_exception(api_exception)
        self.assertEqual(reclassified.detail, "Not Found")
        return

    def test_unknown_status_falls_back_to_base(self):
        """
            An exception with no status falls back to KubernetesApiError.
        """
        plain_error = RuntimeError("network down")
        reclassified = reclassify_api_exception(plain_error)
        self.assertIsInstance(reclassified, KubernetesApiError)
        self.assertEqual(reclassified.status_code, 0)
        return


if __name__ == "__main__":
    unittest.main()
