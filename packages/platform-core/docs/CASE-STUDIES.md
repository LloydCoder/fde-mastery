# Customer Case Studies

These are clearly labeled **demonstration scenarios**, not claims of production customer results.

## Case 1 — Fintech risk triage

**Problem:** A fintech operations team receives high-volume transaction alerts and needs consistent first-pass risk classification.

**Platform path:** Finance request → domain adapter → Month 2 risk agent → resilience boundary → normalized result → audit event.

**Demonstrated value:** A repeatable workflow with tenant-aware authorization, auditable decisions, confidence scoring, and human-review escalation.

## Case 2 — Security operations

**Problem:** A security team needs to normalize noisy security events before analyst review.

**Platform path:** Security event → Month 1 SOC triage agent → normalized platform result → audit + usage telemetry.

**Demonstrated value:** One platform contract around a specialist agent, allowing the customer to integrate a single endpoint rather than six unrelated agent APIs.

## Case 3 — Multi-domain enterprise

**Problem:** An enterprise wants cybersecurity, finance, healthcare, logistics, legal, and revenue operations automation behind one control plane.

**Platform path:** OIDC identity → tenant/scopes → router → domain-specific adapter → resilience → audit/observability.

**Demonstrated value:** Consistent authentication, resilience, observability, and governance while preserving domain-specific agent implementations.

## Evidence policy

Do not present these scenarios as named customer references, measured ROI, production deployments, or testimonials unless independently verified customer evidence is added.
