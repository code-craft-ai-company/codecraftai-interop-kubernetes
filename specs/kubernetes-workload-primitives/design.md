# Design

## Overview

The workload primitives are typed wrappers over the SDK's `BatchV1Api`,
`AppsV1Api`, `CoreV1Api`, and `NetworkingV1Api`. Each primitive owns its CRUD
verbs (`apply`, `delete`, `get`, `list`) and its type-appropriate waiters. All
verbs accept `Aspects` and reclassify exceptions via the helper from
`kubernetes-client`.

Idempotent apply is the central design constraint — it is what makes the apply
safe to re-run from `automojo-provisioning`. Read-before-create + automojo-managed
labels make this robust against partial failures and prevent accidental adoption
of foreign resources.

---

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│   WorkloadVenue provisioner / direct caller                │
└─────────────────────┬──────────────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────────────┐
│   KubernetesClient (kubernetes-client)                     │
│   .jobs   .deployments   .statefulsets                     │
│   .pvcs   .services      .ingresses                        │
└─────────────────────┬──────────────────────────────────────┘
                      │ each is an instance of …
                      ▼
┌────────────────────────────────────────────────────────────┐
│   JobPrimitive          apply / delete / get / list /      │
│                         wait_for_completion                │
│   DeploymentPrimitive   apply / delete / get / list /      │
│                         wait_for_available                 │
│   StatefulSetPrimitive  apply / delete / get / list /      │
│                         wait_for_ready                     │
│   PvcPrimitive          apply / delete / get / list /      │
│                         wait_for_bound                     │
│   ServicePrimitive      apply / delete / get / list        │
│   IngressPrimitive      apply / delete / get / list        │
└────────────────────────────────────────────────────────────┘
```

---

## Data Model

### Specs (request payloads)

```python
class JobSpec(SchemaObject):
    name: str
    image: str
    command: List[str]
    args: List[str]
    env: Dict[str, str]
    resources: ResourceRequirements
    restart_policy: str          # "Never" | "OnFailure"
    backoff_limit: int
    completions: int
    parallelism: int
    node_selector: Dict[str, str]
    tolerations: List[Toleration]


class DeploymentSpec(SchemaObject):
    name: str
    image: str
    replicas: int
    container_port: Optional[int]
    env: Dict[str, str]
    resources: ResourceRequirements
    labels: Dict[str, str]
    node_selector: Dict[str, str]


class StatefulSetSpec(SchemaObject): ...
class PvcSpec(SchemaObject): ...
class ServiceSpec(SchemaObject): ...
class IngressSpec(SchemaObject): ...
```

### Info DTOs (response payloads)

```python
@dataclass
class JobInfo:
    name: str
    namespace: str
    phase: str
    succeeded: int
    failed: int
    active: int
    start_time: Optional[datetime]
    completion_time: Optional[datetime]


@dataclass
class DeploymentInfo: ...
@dataclass
class StatefulSetInfo: ...
@dataclass
class PvcInfo: ...
@dataclass
class ServiceInfo: ...
@dataclass
class IngressInfo: ...
```

### Errors

```python
class KubernetesJobFailedError(Exception):
    info: JobInfo


class KubernetesWaitTimeoutError(Exception):
    observed: object
```

---

## Module Layout

```
source/packages/automojo/interop/kubernetes/primitives/
├── __init__.py
├── jobprimitive.py
├── deploymentprimitive.py
├── statefulsetprimitive.py
├── pvcprimitive.py
├── serviceprimitive.py
├── ingressprimitive.py
└── waitererrors.py
```

Plus specs and info DTOs in `specs/` and `model/` sub-packages.

---

## See Also

- `kubernetes-client` — parent client; exception reclassification; Aspects.
- `automojo-provisioning` `venue-coreweave` — consumer.
- `automojo-provisioning` `workload-venue-model` — provides the abstract
  WorkloadVenue surface this primitives layer fulfils underneath.

---

## Testing Strategy

- Each primitive's CRUD methods unit-tested via `FakeKubernetesApiClient`.
- Idempotency tests — apply twice; expect a single create + a single patch with
  identical resulting state; second invocation must report "no change".
- Adoption-prevention tests — apply against an existing resource lacking
  `automojo/managed=true` raises `KubernetesConflictError`.
- Waiter tests — drive scripted state sequences and assert convergence /
  failure-raise / timeout-raise.
- Spec validation tests — missing-required raises `SemanticError`.
- No live cluster required.
