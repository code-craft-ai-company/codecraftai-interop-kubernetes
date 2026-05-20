# Requirements

## Introduction

The `kubernetes-client` feature delivers `KubernetesClient`, the top-level interop
client wrapping the official `kubernetes` Python SDK and normalising it to the
automojo `Aspects` pattern. It is the foundation that the workload primitives
(`kubernetes-workload-primitives`) and downstream WorkloadVenue provisioners
(CoreWeave, self-hosted K8s) build on.

The client deliberately wraps the official SDK rather than reimplementing the REST
surface. Every public method translates the SDK's behaviour into automojo
conventions:

- `Aspects`-controlled timeouts / retries / logging on every call
- typed return values (no raw V1* SDK objects leak out)
- typed exceptions (no `ApiException` leak out)
- named-only parameters at the public surface

---

## Requirements

### Requirement 1: Client Construction

#### Acceptance Criteria

1. WHEN the caller constructs `KubernetesClient(kubeconfig_path=...,
   context=None)` THE SYSTEM SHALL load the kubeconfig from disk and configure
   the underlying SDK with the resolved cluster + auth.
2. WHEN the caller constructs `KubernetesClient(kubeconfig_dict=...,
   context=None)` THE SYSTEM SHALL load the kubeconfig from the dict.
3. WHEN the caller constructs `KubernetesClient(in_cluster=True)` THE SYSTEM SHALL
   use the in-cluster service-account context.
4. WHEN more than one of `kubeconfig_path` / `kubeconfig_dict` / `in_cluster=True`
   is supplied THE SYSTEM SHALL raise `SemanticError`.
5. WHEN none of them are supplied THE SYSTEM SHALL raise `SemanticError`.

---

### Requirement 2: Aspects on Every Call

#### Acceptance Criteria

1. WHEN any public method is declared on `KubernetesClient` or its workload
   primitives THE SYSTEM SHALL include `aspects: Aspects =
   DEFAULT_KUBERNETES_ASPECTS` as a keyword-only parameter.
2. WHEN the method invokes the underlying SDK THE SYSTEM SHALL apply
   `aspects.timeout_seconds` as the request timeout, `aspects.poll_interval` for
   any waiter sub-loop, and `aspects.logging_level` for structured logging.
3. THE SYSTEM SHALL NOT use any `@retry`-style decorator anywhere in the package.

---

### Requirement 3: Typed Exceptions

#### Acceptance Criteria

1. WHEN the underlying SDK raises `client.rest.ApiException` with status 404 THE
   SYSTEM SHALL reclassify into `KubernetesResourceNotFoundError`.
2. WHEN the underlying SDK raises `ApiException` with status 409 THE SYSTEM SHALL
   reclassify into `KubernetesConflictError`.
3. WHEN the underlying SDK raises `ApiException` with status 403 THE SYSTEM SHALL
   reclassify into `KubernetesForbiddenError`.
4. WHEN the underlying SDK raises `ApiException` with status 401 THE SYSTEM SHALL
   reclassify into `KubernetesUnauthorizedError`.
5. WHEN the underlying SDK raises any other `ApiException` THE SYSTEM SHALL
   reclassify into `KubernetesApiError` carrying the status code and message.

---

### Requirement 4: Namespace and Context Awareness

#### Acceptance Criteria

1. WHEN any method accepts a `namespace` parameter THE SYSTEM SHALL default it to
   the current context's default namespace if not supplied.
2. WHEN `client.use_namespace(...)` is called THE SYSTEM SHALL update the
   client-wide default namespace for subsequent calls.
3. WHEN `client.use_context(...)` is called THE SYSTEM SHALL switch to the named
   context in the loaded kubeconfig and raise
   `KubernetesResourceNotFoundError` if the context does not exist.

---

### Requirement 5: Health Probe

#### Acceptance Criteria

1. WHEN `client.health(aspects=...)` is called THE SYSTEM SHALL invoke the API
   server's `/healthz` (or equivalent) endpoint and return a `KubernetesHealth`
   dataclass with `reachable: bool`, `version: str`, `node_count: int`.
2. WHEN the API server is unreachable THE SYSTEM SHALL return
   `KubernetesHealth(reachable=False, version="", node_count=0)` without raising.
