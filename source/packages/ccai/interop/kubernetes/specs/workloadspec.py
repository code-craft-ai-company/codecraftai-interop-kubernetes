"""
    .. module:: workloadspec
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Provides :class:`WorkloadSpec`, the lightweight base class for
        every typed workload request payload.

    The ``kubernetes-workload-primitives`` design names the request payloads
    "SchemaObject subclasses". The canonical ``SchemaObject`` lives in
    ``codecraftai-restclient-base``. This package deliberately wraps the
    official ``kubernetes`` SDK and does not depend on the REST-client
    transport stack (see the AGENTS.md transport note), so a minimal local
    base providing the same required-field-validation contract is used
    instead. It keeps the workload-primitives layer free of a parallel REST
    client dependency.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import os

from typing import List, Tuple

from ccai.errors.exceptions import SemanticError


class WorkloadSpec:
    """
        Base class for every typed workload request payload.

        Subclasses declare a ``REQUIRED_FIELDS`` tuple. The
        :meth:`validate` method enforces that each required attribute has a
        non-``None`` value before the owning primitive issues an API call,
        raising :class:`SemanticError` otherwise.
    """

    REQUIRED_FIELDS: Tuple[str, ...] = ()

    def validate(self) -> None:
        """
            Verify every required field carries a non-``None`` value.

            :returns: ``None``
            :raises: SemanticError
        """
        missing: List[str] = []

        for field_name in self.REQUIRED_FIELDS:
            field_value = getattr(self, field_name, None)
            if field_value is None:
                missing.append(field_name)

        if len(missing) > 0:
            err_msg_lines = ["Workload spec is missing required fields."]
            err_msg_lines.append("SPEC: {}".format(type(self).__name__))
            err_msg_lines.append("MISSING: ({})".format(len(missing)))
            for field_name in missing:
                err_msg_lines.append("    {}".format(field_name))

            err_msg = os.linesep.join(err_msg_lines)
            raise SemanticError(err_msg) from None

        return


__all__ = ["WorkloadSpec"]
