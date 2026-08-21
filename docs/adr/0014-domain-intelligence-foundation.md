# ADR-0014 — Domain Intelligence Foundation

## Status

Accepted

## Context

Builds 1–12 established a provider-neutral enterprise platform kernel and seven routable domain services. Six domains remain compatibility facades over the historical Month 1–6 implementations, while Procurement is native. The platform lacked a single machine-readable promotion contract, a canonical domain registry, representative promotion fixtures for every domain, and a safe first-class Custom domain.

## Decision

1. Keep the kernel framework/provider neutral and add domain promotion metadata to `DomainDescriptor`.
2. Keep the domain registry outside the kernel and load concrete implementations lazily through explicit factories.
3. Promote eight first-class domains: Cybersecurity, Finance, HealthTech, Logistics, Legal, RevOps, Procurement and Custom.
4. Require every promoted domain to declare capabilities, lifecycle, risk, human approval, evaluation suite and representative data.
5. Require human approval for high and critical risk domains.
6. Keep Custom configuration-driven and recommendation-only in v1; it must not execute autonomous tenant-defined side effects.
7. Use synthetic shared promotion fixtures so the promotion contract can be tested without customer data.

## Consequences

- Legacy implementations can be incrementally replaced without changing the platform contract.
- Domain promotion becomes explicit and testable.
- The platform can add future domains without changing kernel boundaries.
- Custom becomes a safe extension point instead of an unrestricted execution surface.
- Domain-specific depth can now be added in later builds without weakening the common control plane.
