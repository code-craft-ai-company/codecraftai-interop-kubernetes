=========================================
Automation Mojo Interop - Kubernetes
=========================================

The ``automojo-interop-kubernetes`` package is the Kubernetes interop client for the
automojo suite. It wraps the official ``kubernetes`` Python client and exists to serve two
distinct consumers: ``automojo-provisioning`` ``WorkloadVenue`` provisioners (CoreWeave,
Sunk Slurm-on-K8s, self-hosted clusters) and landscaping packages that enumerate or
interact with workloads on a cluster.

Highlights
==========

- ``KubernetesClient`` — the top-level client, constructed from a kubeconfig path, a kubeconfig dict, or an in-cluster service-account context.
- A workload primitives layer — typed helpers for ``Job``, ``Deployment``, ``StatefulSet``, ``PersistentVolumeClaim``, ``Service``, and ``Ingress``, each exposing ``apply``, ``delete``, ``get``, ``list``, and waiter methods built on ``automojo-waiting``.
- Consistent typed return objects — every method returns a typed result object (DTOs under ``model/``), not a raw dict.
- Consistent failure shape — API errors are reclassified into named exceptions (``KubernetesResourceNotFoundError``, ``KubernetesConflictError``, etc.) so callers do not decode ``ApiException`` status codes.
- All public APIs normalize the underlying client to the automojo ``Aspects`` pattern — callers control timeouts, retries, and logging; no behaviour-modifying decorators.

Repository Structure
====================

- ``development/`` - Runtime environment scripts.
- ``repository-setup/`` - Repository homing and setup scripts.
- ``source/packages/automojo/interop/kubernetes/`` - Package source code.
- ``source/testroots/testbase/automojo/tests/interop/kubernetes/`` - TestBase test roots.
- ``specs/`` - Requirements, design, and task documentation (Kiro-style).
- ``userguide/`` - Standards, conventions, and documentation.

Environment Setup
=================

When working in a Codex container:

.. code-block:: bash

   ./development/setup-agent-container

For local development:

.. code-block:: bash

   ./repository-setup/rehome-repository
   ./development/setup-environment

Running Tests
=============

.. code-block:: bash

   source .venv/bin/activate
   PYTHONPATH=source/packages:source/testroots/testbase python -m pytest source/testroots -q

Standards and Conventions
=========================

- Naming conventions: ``userguide/10-02-naming-conventions.rst``
- Code organization: ``userguide/10-01-code-organization.rst``
- Coding standards: ``userguide/10-00-coding-standards.rst``

Additional Resources
====================

- User guide entry point: ``userguide/userguide.rst``
