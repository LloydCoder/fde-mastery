# FDE Mastery — Six-Domain Deployment Guide

This guide defines the supported deployment boundary for the six Month 1–6 domain agents behind the Month 7 platform router.

## Deployment posture

All six domains are exposed through the same platform contract and run in **human-in-the-loop mode**. The platform may produce recommendations and workflow steps, but high-impact actions must be reviewed by an authorized human before execution.

Domains:

1. Cybersecurity — SOC alert triage and IOC prioritization
2. Finance — transaction risk and compliance evaluation
3. HealthTech — PHI de-identification and clinical risk triage
4. Logistics — shipment, trade-compliance and cold-chain risk
5. Legal — contract clause risk and redline recommendations
6. RevOps — opportunity health and deal-governance evaluation

## Required production configuration

- Configure OIDC issuer, audience, JWKS and approved signing algorithms.
- Configure tenant identity claims and least-privilege scopes.
- Configure PostgreSQL and Redis using managed production services.
- Configure OpenTelemetry OTLP export to the organization's collector/backend.
- Configure production secrets through the supported secrets-provider integration; do not commit provider credentials.
- Use the signed container image produced by the release workflow.
- Verify the published SBOM and image signature before deployment.
- Keep high-impact domain actions behind the platform's human-approval policy.

## Domain-specific inputs

### Cybersecurity

Input: structured SIEM JSON represented by `RawSecurityLog`.
Required fields include log ID, timestamp, source IP, event type and payload summary. Optional destination IP and user identity improve enrichment. Start with mock mode for CI and staging; production requires an approved LLM provider configuration and real SIEM/tool integrations.

### Finance

Input: `FinancialTransaction`. Required fields include transaction ID, account/counterparty IDs, transaction type, amount, source country and destination country. The agent has a deterministic fallback path when an LLM provider is unavailable. `AUTO_REJECT` and `FREEZE_ACCOUNT` decisions remain subject to human approval and the customer's financial-control policy.

### HealthTech

Input: `HealthtechPayload`. PHI must be handled under the customer's approved HIPAA/privacy controls. De-identification should occur before data is sent to an external model provider. Clinical outputs are decision support only; `IMMEDIATE_INTERVENTION` and physician escalation require qualified clinical review.

### Logistics

Input: `ShipmentPayload`, including transport mode, route, HS code, declared temperature range and telemetry. Sanctions, customs holds and cold-chain actions must integrate with the customer's trade-compliance and operations authority. Quarantine/reroute actions require approval according to customer policy.

### Legal

Input: `ContractPayload` with extracted clauses and governing jurisdiction. The agent produces risk flags and proposed redlines; it does not provide final legal advice or execute contracts autonomously. Contract rejection, amendment and approval remain counsel-controlled decisions.

### RevOps

Input: `OpportunityPayload` with ARR, stage, discount, sponsorship and product telemetry. CRM, marketing, scheduling and communications integrations must be explicitly authorized per tenant. Deal Desk escalation, churn intervention and automated assignment remain subject to customer governance.

## Staging procedure

1. Deploy the signed image into an isolated staging environment.
2. Run database migrations before enabling traffic.
3. Verify `/healthz` and `/readyz`.
4. Verify OIDC authentication and tenant isolation.
5. Run the six-domain deployment smoke test with synthetic data.
6. Confirm traces, metrics and audit events are visible.
7. Exercise retry, timeout and circuit-breaker paths.
8. Run the red-team and evaluation suites.
9. Run a controlled load smoke test.
10. Enable shadow mode against real customer telemetry before production decisions are acted upon.

## Production acceptance criteria

A customer deployment is accepted only when all of the following are true:

- CI is green on the exact release commit.
- Container signature and SBOM verification succeed.
- Managed PostgreSQL/Redis connectivity and backup policy are validated.
- OIDC/JWT and tenant-scoped authorization are tested with customer identities.
- Domain-specific input validation succeeds.
- High-impact recommendations are demonstrably human-gated.
- Audit events include actor, tenant, action, outcome and request correlation.
- Observability dashboards and alerts are configured.
- Restore/rollback procedures have been tested in the target environment.
- Customer-specific data-retention, privacy, regulatory and escalation requirements are approved.

Passing the repository's CI suite establishes **deployment readiness of the software contract**, not automatic authorization to operate it without customer-specific security, regulatory and operational validation.
