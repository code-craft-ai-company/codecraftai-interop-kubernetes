"""
    .. module:: workload
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: The workload primitives layer — typed helpers for Job,
        Deployment, StatefulSet, PVC, Service, Ingress and Namespace. Each
        helper is a thin typed wrapper over the official ``kubernetes`` SDK
        exposing create/get/list/delete/wait normalised to the automojo
        ``Aspects`` pattern.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


MANAGED_LABEL_KEY = "automojo/managed"
MANAGED_LABEL_VALUE = "true"
SPEC_NAME_LABEL_KEY = "automojo/spec-name"


__all__ = ["MANAGED_LABEL_KEY", "MANAGED_LABEL_VALUE", "SPEC_NAME_LABEL_KEY"]
