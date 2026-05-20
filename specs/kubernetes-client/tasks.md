# Implementation Plan — Kubernetes Client

- [x] 1. Create `automojo.interop.kubernetes` package skeleton.

- [x] 2. Define exception hierarchy in `kuberneteserrors.py` (KubernetesApiError +
  the four 4xx subclasses).

- [x] 3. Define `KubernetesHealth` dataclass.

- [x] 4. Define `DEFAULT_KUBERNETES_ASPECTS` (timeout=30s, poll_interval=2s, INFO
  logging).

- [x] 5. Implement `_reclassify(api_exception)` helper.

- [x] 6. Implement `KubernetesClient.__init__` accepting one-of
  `(kubeconfig_path, kubeconfig_dict, in_cluster)` — raise `SemanticError` for
  zero or multiple.

- [x] 7. Implement `use_namespace`, `use_context`.

- [x] 8. Implement `health(aspects)` — reachable / version / node_count.

- [x] 9. Wire `Aspects` into every public method (timeout, poll_interval, logging).

- [x] 10. Hook every SDK call site through `_reclassify` so no `ApiException` leaks.

## Tests

- [x] 11. Construction validation — three valid paths + zero + multiple.

- [x] 12. Exception reclassification — table-driven over status codes.

- [x] 13. Namespace switching.

- [x] 14. Context switching including unknown-context raising.

- [x] 15. Health probe — reachable / unreachable / partial info.

- [x] 16. Aspects forwarding test.
