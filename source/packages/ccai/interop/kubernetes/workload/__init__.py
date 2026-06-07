"""
    .. module:: workload
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: The workload primitives layer — typed helpers for Job,
        Deployment, StatefulSet, PVC, Service, Ingress and Namespace. Each
        helper is a thin typed wrapper over the official ``kubernetes`` SDK
        exposing create/get/list/delete/wait normalised to the ccai
        ``Aspects`` pattern.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


MANAGED_LABEL_KEY = "ccai/managed"
MANAGED_LABEL_VALUE = "true"
SPEC_NAME_LABEL_KEY = "ccai/spec-name"


__all__ = ["MANAGED_LABEL_KEY", "MANAGED_LABEL_VALUE", "SPEC_NAME_LABEL_KEY"]
