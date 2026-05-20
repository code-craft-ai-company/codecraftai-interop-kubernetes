# Implementation Plan — Kubernetes Workload Primitives

## Spec and DTO definitions

- [x] 1. `JobSpec` + `JobInfo`.
- [x] 2. `DeploymentSpec` + `DeploymentInfo`.
- [x] 3. `StatefulSetSpec` + `StatefulSetInfo`.
- [x] 4. `PvcSpec` + `PvcInfo`.
- [x] 5. `ServiceSpec` + `ServiceInfo`.
- [x] 6. `IngressSpec` + `IngressInfo`.
- [x] 7. Errors: `KubernetesJobFailedError`, `KubernetesWaitTimeoutError`.

## Primitives

- [x] 8. `JobPrimitive` — apply / delete / get / list / `wait_for_completion`.

- [x] 9. `DeploymentPrimitive` — apply / delete / get / list /
  `wait_for_available`.

- [x] 10. `StatefulSetPrimitive` — apply / delete / get / list / `wait_for_ready`.

- [x] 11. `PvcPrimitive` — apply / delete / get / list / `wait_for_bound`.

- [x] 12. `ServicePrimitive` — apply / delete / get / list.

- [x] 13. `IngressPrimitive` — apply / delete / get / list.

## Cross-cutting

- [x] 14. Read-before-create idempotent apply across all primitives.

- [x] 15. Auto-attach `automojo/managed=true` + `automojo/spec-name=<name>`
  labels on every `apply`.

- [x] 16. Adoption-prevention: raise `KubernetesConflictError` when applying
  against an unmanaged existing resource.

- [x] 17. Wire each primitive's CRUD onto `KubernetesClient.<accessor>`.

## Tests

- [x] 18. CRUD unit tests per primitive (happy, not-found, conflict).
- [x] 19. Idempotency tests — apply twice → second is a no-op.
- [x] 20. Adoption-prevention tests.
- [x] 21. Waiter tests — convergence / failure / timeout per primitive.
- [x] 22. Spec validation tests — missing-required raises `SemanticError`.
