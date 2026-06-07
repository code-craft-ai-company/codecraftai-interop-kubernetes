# Design

## Overview

`KubernetesClient` is a thin, opinionated wrapper around the official `kubernetes`
Python SDK that normalises behaviour to the ccai `Aspects` pattern. It owns
kubeconfig loading, the active namespace / context, exception reclassification,
and the health probe. The workload primitives (Job, Deployment, etc.) are delivered
by the sibling `kubernetes-workload-primitives` spec and operate on the same
client instance.

---

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│   Caller (WorkloadVenue provisioner, landscape coupling)   │
└─────────────────────┬──────────────────────────────────────┘
                      │ constructs
                      ▼
┌────────────────────────────────────────────────────────────┐
│   KubernetesClient                                         │
│   - kubeconfig loading (path | dict | in-cluster)          │
│   - active context / namespace state                       │
│   - exception reclassification                             │
│   - health probe                                           │
│   - holds primitive sub-clients (Jobs, Deployments, etc.)  │
└─────────────────────┬──────────────────────────────────────┘
                      │ delegates to
                      ▼
┌────────────────────────────────────────────────────────────┐
│   kubernetes SDK (official Python client)                  │
│   CoreV1Api, AppsV1Api, BatchV1Api, NetworkingV1Api, ...   │
└────────────────────────────────────────────────────────────┘
```

---

## Data Model

```python
@dataclass
class KubernetesHealth:
    reachable: bool
    version: str
    node_count: int


class KubernetesApiError(Exception):
    status_code: int
    detail: str


class KubernetesResourceNotFoundError(KubernetesApiError): ...
class KubernetesConflictError(KubernetesApiError): ...
class KubernetesForbiddenError(KubernetesApiError): ...
class KubernetesUnauthorizedError(KubernetesApiError): ...
```

---

## Exception Reclassification

| SDK status | New exception |
| --- | --- |
| 401 | `KubernetesUnauthorizedError` |
| 403 | `KubernetesForbiddenError` |
| 404 | `KubernetesResourceNotFoundError` |
| 409 | `KubernetesConflictError` |
| any other | `KubernetesApiError` |

All reclassifications use `raise … from original` to preserve the SDK exception
chain for debuggability.

---

## Module Layout

```
source/packages/ccai/interop/kubernetes/
├── __init__.py
├── kubernetesclient.py         # KubernetesClient
├── kuberneteshealth.py         # KubernetesHealth
├── kuberneteserrors.py         # exception hierarchy
├── exceptionmapping.py         # _reclassify(api_exception) helper
├── aspectskubernetes.py        # DEFAULT_KUBERNETES_ASPECTS
└── primitives/                 # owned by kubernetes-workload-primitives
```

---

## See Also

- `kubernetes-workload-primitives` — Job, Deployment, StatefulSet, PVC, Service,
  Ingress helpers built on top of this client.
- `codecraftai-interop-coreweave` — composes this client via a CoreWeave-issued
  kubeconfig.
- `codecraftai-provisioning` `venue-coreweave` — top-level consumer.

---

## Testing Strategy

- All tests use a `FakeKubernetesApiClient` shim that mimics the relevant SDK
  Api classes (`CoreV1Api`, `AppsV1Api`, etc.).
- Construction tests — three valid construction paths + two invalid (multiple,
  none).
- Exception reclassification tests — table-driven over status codes.
- Namespace / context switching tests.
- Health probe — reachable, unreachable, partial-info (no nodes list permission).
- Aspects forwarding test — assert each method accepts and forwards `aspects`.
- No live cluster required.
