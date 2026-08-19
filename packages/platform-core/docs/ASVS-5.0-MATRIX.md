# OWASP ASVS 5.0 Verification Matrix

This is a living verification checklist for the Month 7 platform. It maps the platform's current controls to the ASVS 5.0 structure. It is not a claim of formal certification.

Reference: urlOWASP Application Security Verification Standardhttps://owasp.org/www-project-application-security-verification-standard/

| ASVS 5 area | Platform evidence | Status |
|---|---|---|
| V1 Encoding & Sanitization | Pydantic request models; input validation tests | Partial |
| V2 Validation & Business Logic | Domain/client validation; bounded execution | Partial |
| V3 Web Frontend Security | API-focused platform; explicit CORS/security headers | Partial |
| V4 API & Web Service | FastAPI routing, auth, request limits, error contract | Partial |
| V5 File Handling | No general file-upload feature | N/A |
| V6 Authentication | API-key authentication; 401/403 semantics | Partial |
| V7 Session Management | Stateless API-key model | Partial |
| V8 Authorization | Admin authorization and tenant/domain isolation | Partial |
| V9 Self-Contained Tokens | No JWT requirement currently | N/A |
| V10 OAuth/OIDC | Not currently implemented | Planned |
| V11 Cryptography | TLS delegated to deployment; no custom cryptography | Partial |
| V12 Secure Communication | Production TLS requirements documented | Partial |
| V13 Configuration | Environment-based configuration and production validation | Partial |
| V14 Data Protection | PostgreSQL isolation, audit controls, redaction roadmap | Partial |
| V15 Secure Coding & Architecture | Repository abstraction, threat model, CI security gates | Partial |
| V16 Security Logging & Error Handling | Request IDs, audit events, sanitized error contract | Partial |
| V17 WebRTC | Not applicable | N/A |

## Required evidence before production claim

- Automated authorization/tenant-isolation regression suite
- Dependency and container vulnerability scanning
- SBOM generation
- Secret scanning
- Security headers and CORS tests
- Error-leakage tests
- Database authorization and migration tests
- Audit retention/integrity controls
- Production TLS configuration review
- Threat-model review for every new tool/agent capability

Status labels mean:

- **Implemented** — control and automated evidence exist.
- **Partial** — control exists but broader verification remains.
- **Planned** — not yet implemented.
- **N/A** — feature is outside the current platform scope.
