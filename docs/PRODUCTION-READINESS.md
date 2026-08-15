# Enterprise Production Readiness Gate

This repository uses eight explicit gates before a domain is promoted from engineering to customer production. The gates are aligned with a risk-managed AI lifecycle: govern, map, measure and manage. The security baseline should be reviewed against current NIST AI RMF and OWASP GenAI guidance.

## The eight gates

1. **Golden dataset expansion** — each domain has a versioned synthetic baseline with 100 cases in v1. Customer datasets must remain outside Git and be evaluated in a controlled environment. The release gate requires reproducible evaluation results and explicit false-negative thresholds.
2. **Approved tool integration** — a tenant-scoped integration must implement the provider contract, authenticate successfully, expose health, ingestion and enrichment operations, and pass connector contract tests. The repository contains the provider-neutral contract; customer credentials are injected at deployment time.
3. **Enterprise ingestion** — incoming events must carry tenant and request identifiers, pass schema validation, enforce size/rate limits and produce an auditable request record. Unsupported or malformed inputs fail closed.
4. **Evaluation gate** — promotion requires passing domain-specific quality, safety, latency and cost thresholds. A green unit test suite alone is insufficient evidence for model quality.
5. **Staging deployment** — the signed production image is deployed with managed PostgreSQL/Redis, secrets, TLS, readiness checks and telemetry. Smoke/load tests must pass before promotion.
6. **Shadow mode** — the agent observes real or representative traffic without executing consequential actions. Recommendations are compared with human dispositions and agreement, false-negative and escalation rates are recorded.
7. **Human-in-the-loop production** — high-impact actions require an identified human approver and an auditable approval event. The action guard is fail-closed and tenant-scoped.
8. **Controlled actions** — only explicitly approved, reversible, low-risk actions may be automated initially. Destructive or high-impact operations require policy approval and remain disabled until customer-specific evidence supports promotion.

## Six-domain deployment matrix

| Domain | Typical first integration | Initial safe mode | High-impact boundary |
|---|---|---|---|
| Cybersecurity | SIEM / EDR / threat intelligence | shadow triage | containment / credential changes |
| Finance | ERP / payments / accounting | recommendation | payment / approval / rejection |
| HealthTech | EHR / scheduling / claims | recommendation | clinical / medication / patient-impacting action |
| Logistics | TMS / WMS / carrier APIs | recommendation | rerouting / dispatch / shipment cancellation |
| Legal | DMS / matter-management system | recommendation | filing / legal advice / contract execution |
| RevOps | CRM / support / billing | recommendation | customer communication / pricing / account changes |

## Promotion rule

A domain is **not production-ready** merely because the repository CI is green. The deployment record must contain evidence for all eight gates and the customer-specific integration health check. This distinction prevents a passing CI build from being mistaken for operational validation.

## Security and governance baseline

The platform follows least privilege, tenant isolation, structured auditability, signed release artifacts and fail-closed high-impact actions. AI-specific controls should be reviewed against current OWASP GenAI risks, including prompt injection, sensitive information disclosure, improper output handling and excessive agency.

## Customer deployment evidence

For each customer, retain outside the public repository:

- integration and identity configuration
- data classification and retention decision
- evaluation report and dataset version
- staging test evidence
- shadow-mode results
- approval matrix and HITL evidence
- incident/rollback plan
- RPO/RTO and restore-test evidence
- security review and penetration-test evidence where required

The repository provides the reusable engineering controls; customer-specific compliance, credentials and operational evidence must be established separately.