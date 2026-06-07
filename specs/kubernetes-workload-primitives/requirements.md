# Requirements

## Introduction

The `kubernetes-workload-primitives` feature delivers typed helpers for the
Kubernetes resource kinds the WorkloadVenue provisioners need: `Job`, `Deployment`,
`StatefulSet`, `PersistentVolumeClaim`, `Service`, `Ingress`. Each primitive
exposes the standard CRUD + wait surface (`apply`, `delete`, `get`, `list`,
plus type-appropriate waiters) and operates against the `KubernetesClient`
delivered by `kubernetes-client`.

The primitives are consumed by `codecraftai-provisioning` `venue-coreweave` and other
WorkloadVenues. They are deliberately small wrappers — they do not try to be a
general-purpose Kubernetes ORM.

---

## Requirements

### Requirement 1: Apply / Delete / Get / List Per Primitive

#### Acceptance Criteria

1. WHEN any primitive exposes `apply(spec=..., namespace=..., aspects=...)` THE
   SYSTEM SHALL create the resource if absent, patch it if present (read-before-
   create idempotence), and return the typed result DTO.
2. WHEN any primitive exposes `delete(name=..., namespace=..., aspects=...)` THE
   SYSTEM SHALL delete the resource if present and return without raising;
   absent resource SHALL also return without raising (idempotent delete).
3. WHEN any primitive exposes `get(name=..., namespace=..., aspects=...)` THE
   SYSTEM SHALL return the typed DTO or raise
   `KubernetesResourceNotFoundError`.
4. WHEN any primitive exposes `list(namespace=..., label_selector=None,
   aspects=...)` THE SYSTEM SHALL return a list of typed DTOs.

---

### Requirement 2: Waiters

**User Story:** As a WorkloadVenue provisioner, I want to wait for resources to
reach a usable state, so I can verify the apply succeeded.

#### Acceptance Criteria

1. THE SYSTEM SHALL provide `Job.wait_for_completion(name, namespace, aspects)`
   that blocks until the Job reports `Succeeded` or `Failed`; raise
   `KubernetesJobFailedError` on `Failed`; raise `VSphereWaitTimeoutError`-style
   `KubernetesWaitTimeoutError` on timeout.
2. THE SYSTEM SHALL provide `Deployment.wait_for_available(name, namespace,
   aspects)` that blocks until `status.availableReplicas == spec.replicas`.
3. THE SYSTEM SHALL provide `StatefulSet.wait_for_ready(name, namespace,
   aspects)` similarly.
4. THE SYSTEM SHALL provide `PersistentVolumeClaim.wait_for_bound(name,
   namespace, aspects)` that blocks until `phase == Bound`.

---

### Requirement 3: Typed Specs and DTOs

#### Acceptance Criteria

1. THE SYSTEM SHALL provide typed `*Spec` request payloads for each primitive
   (`JobSpec`, `DeploymentSpec`, `StatefulSetSpec`, `PvcSpec`, `ServiceSpec`,
   `IngressSpec`) as `SchemaObject` subclasses.
2. THE SYSTEM SHALL provide typed `*Info` response DTOs for each primitive that
   carry the runtime status fields needed by waiters and inventory.
3. WHEN a spec is missing a required field THE SYSTEM SHALL raise
   `SemanticError` before issuing the API call.

---

### Requirement 4: Label and Annotation Discipline

#### Acceptance Criteria

1. WHEN `apply(...)` is called THE SYSTEM SHALL automatically attach the
   codecraftai-managed labels `ccai/managed=true` and
   `ccai/spec-name=<spec.name>` so that subsequent reconciles can identify
   codecraftai-managed resources.
2. WHEN `apply(...)` is called on a resource that exists but does not carry the
   codecraftai-managed label THE SYSTEM SHALL raise `KubernetesConflictError` to
   prevent accidental adoption of foreign resources.
