# Build 19 — Customer Control Plane

## Objective

Provide a single tenant-scoped control-plane contract over customer environments, projects and platform resources while preserving the existing identity and authorization boundaries.

## Research basis

The design follows NIST AI RMF governance principles: lifecycle governance requires documented roles, accountability, inventories and ongoing monitoring. It also follows OWASP authorization guidance: authorization must be enforced server-side, least privilege must be applied, and multi-tenant data must remain segregated. citeturn1search0turn1search1turn1search8

## Delivered

- Customer environment contract.
- Customer project contract with explicit environment ownership.
- Typed control-plane resource inventory covering agents, workflows, tools, models, policies, integrations, evaluations, deployments and incidents.
- Tenant-scoped control-plane snapshots.
- Existing `RequestContext` used as the tenant boundary.
- Existing `AuthorizationService` used as the only authorization decision boundary.
- Hierarchical environment → project → resource validation.
- Cross-tenant reads and writes fail closed.
- No second RBAC/ABAC engine introduced.
- Immutable resource contracts with version/state metadata.

## Architecture

`Identity/RequestContext -> Existing AuthorizationService -> CustomerControlPlane -> Environment -> Project -> Resource Inventory`

The control plane is an inventory and orchestration boundary. It does not execute agents, tools, workflows or deployments.

## Security properties

- Explicit tenant binding on every resource.
- Server-side authorization.
- Least-privilege-compatible action/resource contracts.
- Cross-tenant lookup cannot escape the request tenant.
- Unknown hierarchy members fail closed.

## Verification

Build 19 is green only after the full repository Platform Quality and Semgrep gates pass, including tests, security checks, static analysis, SBOM, staging/load smoke and production Docker runtime smoke.
