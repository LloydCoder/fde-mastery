# Enterprise Security & AI Governance Standards Map

This document records the standards used to guide the FDE Mastery engineering baseline. It is an engineering control map, not a certification or compliance claim.

## OWASP ASVS 5.0

The application-security baseline is aligned to the OWASP Application Security Verification Standard (ASVS) 5.0.0. The relevant control families for this platform are:

- authentication and identity verification
- session and token handling
- access control and tenant isolation
- input validation and output encoding
- cryptography and secret handling
- secure communications
- error handling and logging
- data protection
- API and web-service security
- configuration and deployment security

Repository evidence includes OIDC/JWKS validation, scoped authorization, tenant-scoped registries, secret-provider contracts, sensitive-data redaction, security scanning, TLS-oriented deployment configuration, audit events, and API validation. Customer deployments still require a control-by-control assessment against their actual threat model and environment.

## NIST AI RMF / Generative AI Profile

AI lifecycle controls are informed by NIST AI RMF 1.0 and the Generative AI Profile (NIST AI 600-1). The implementation emphasizes:

- documented intended use and scope boundaries
- measurable evaluation and drift detection
- adversarial/red-team testing
- human oversight for high-impact actions
- provenance of evidence and model outputs
- incident and recovery procedures
- monitoring after deployment
- explicit separation of facts from model-generated inference

The platform must not present synthetic evaluation results as customer outcomes.

## OpenTelemetry

Observability follows OpenTelemetry concepts and semantic conventions. Instrumentation should use stable/common attribute names for HTTP, database, messaging, service, exception, and deployment telemetry rather than inventing incompatible names. Production exporters remain customer-configurable.

Required correlation dimensions include request/correlation ID, tenant/client ID where policy permits, domain, service name, deployment version, and error classification. Sensitive payloads must not be copied into spans or logs merely for debugging.

## SLSA / Artifact Provenance

Container releases use signed images and SBOM attestations. The release workflow additionally creates GitHub artifact provenance using the SLSA-oriented attestation mechanism. Provenance should bind the immutable container digest to the workflow/build context so consumers can verify where and how the image was produced.

Deployment environments should verify both the image signature and provenance before accepting a production artifact.

## Required enterprise evidence

Before a customer-specific production launch, collect:

1. threat model and data-flow diagram
2. identity and access-control configuration
3. tenant-isolation test evidence
4. dependency/SBOM report
5. image signature and provenance verification
6. evaluation results for the customer's golden dataset
7. red-team/security regression results
8. staging and shadow-mode results
9. backup/restore evidence and RPO/RTO results
10. operational runbooks and escalation contacts
11. retention/deletion configuration
12. domain-specific compliance and legal review

A green GitHub workflow demonstrates repository engineering quality; it does not replace customer security review, penetration testing, compliance assessment, or production operational evidence.
