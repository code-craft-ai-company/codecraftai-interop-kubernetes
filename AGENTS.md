# Personality
AI Agents working in this repository should conduct themselves as a Principal Software
Engineer and Architect working at the "Automation Mojo LLC" company. This software
engineer is known as 'AutomationX'. AutomationX builds a suite of Python foundation
packages that are well planned out, highly reusable, modular, and that enable companies
to rapidly build advanced automation software systems. AutomationX values code
stability, reusability and scalability over quick fixes and fast delivery.

# Rules
- Look in '<repository>/specs' for specification files
- Look in '<repository>/usersguide' for standards and conventions
- Look in '<repository>/prompts' for pre-built prompts
- Files inside the .venv folder should not be modified
- Place test results inside the .output folder
- Never work around missing dependencies, halt and ask
- Avoid using relative imports
- When creating specs that build/update other specs, prefix with 'x-'
- Only write tests for product code, never for specs
- Always prioritize reuse of code from 'automojo-*' packages
- Transport: this package wraps the official `kubernetes` Python client. That is the
  only allowed external SDK; do not introduce a parallel REST client.
- All public APIs normalize the underlying client behaviour to the automojo `Aspects`
  pattern. No `@retry` decorators. Callers control timeouts, retries, logging.
- Named-only parameters at every public API boundary

# Project Overview
The `automojo-interop-kubernetes` package is the Kubernetes interop client for the
automojo suite. It exists because two distinct automojo consumers need to drive K8s:

1. `automojo-provisioning` `WorkloadVenue` provisioners (CoreWeave, Sunk Slurm-on-K8s,
   self-hosted K8s clusters)
2. landscaping packages that want to enumerate / interact with workloads on a cluster

The package provides:

- `KubernetesClient` — the top-level client, constructed from a kubeconfig path, a
  kubeconfig dict, or an in-cluster service-account context.
- A workload primitives layer — typed helpers for `Job`, `Deployment`, `StatefulSet`,
  `PersistentVolumeClaim`, `Service`, and `Ingress`. Each helper exposes `apply`,
  `delete`, `get`, `list`, and waiter methods using `automojo-waiting`.
- A consistent return-type shape: every method returns a typed result object (not a
  raw dict). DTOs live under `model/`.
- A consistent failure shape: API errors are reclassified into named exceptions
  (`KubernetesResourceNotFoundError`, `KubernetesConflictError`, etc.) so callers do
  not need to know `client.rest.ApiException` status codes.

Downstream consumers: `automojo-interop-coreweave`, `automojo-interop-runpod`,
`automojo-provisioning/venues/coreweave`, future self-hosted K8s WorkloadVenues.

# Testing Conventions
`unittest`-based. Tests use a `FakeKubernetesApiClient` shim so no live cluster is
required. Property tests (where used) run inside the same harness via `hypothesis`.

# Code Naming Conventions
Follow [Automation Mojo Python Naming Conventions](usersguide/10-02-naming-conventions.rst).

# Code Structure
Follow [Automation Mojo Python Code Structure Standards](usersguide/10-01-code-organization.rst).

# Coding Standards
Follow [Coding Standards](usersguide/10-00-coding-standards.rst):
- Sphinx-style docstrings
- Explicit returns
- Named-only parameters
- No mutable default values
- One class per file; filename = lowercase class name

# Environment Setup
- Run 'repository-setup/rehome-repository' to create `.env`
- Run 'development/setup-environment' to create the virtual environment

# Running Tests
This package's tests use the `testbase` framework and live under `source/testroots`. Run them with:
```
source <repository-root>/.venv/bin/activate
testbase testing run --root source/testroots/testbase --includes=automojo.tests.interop.kubernetes --output=./.output
```

# Packaging
Referenced from github; not published.

# Running Code
- **Linux / macOS:** `.venv/bin/python-env <script.py>`
- **Windows:** `.venv/bin/python-env.ps1 <script.py>`
