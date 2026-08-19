# Month 7 AI Threat Model

## Assets

- Client identity and enabled-domain permissions
- Domain request payloads
- Model/provider credentials
- Client preferences and rubric overrides
- Audit identifiers and usage data
- Financial, healthcare, legal, security, and operational outputs

## Trust boundaries

1. External client → API gateway
2. API gateway → domain router
3. Router → domain adapter/agent
4. Agent → external model provider
5. Application → persistence backend
6. Application → rate-limit backend

## Primary abuse cases

| Threat | Example | Control |
|---|---|---|
| Broken authorization | Client calls another client's domain | Client + domain authorization |
| Prompt injection | Untrusted document tells agent to ignore policy | Deterministic policy layer; treat retrieved text as untrusted |
| Data exfiltration | Prompt attempts to return secrets/PHI | Input/output validation, least privilege, redaction |
| Excessive agency | Agent directly executes high-impact action | Human approval boundaries |
| Resource exhaustion | Huge payload or request burst | Body-size and rate limits |
| Credential theft | API/database keys committed to source | Environment secrets + CI scanning |
| Cross-tenant leakage | Preferences loaded from another client | Client-scoped paths and repository access |
| Supply-chain risk | Vulnerable Python dependency | pip-audit + pinned production builds |

## AI-specific engineering rules

- Treat model output as untrusted data until schema validation succeeds.
- Never allow retrieved text to override system/application policy.
- Keep credentials outside prompts and model-visible context.
- Separate planning from authorization to execute high-impact actions.
- Log identifiers and outcomes, not sensitive payloads.
- Use synthetic data in tests and demonstrations.

## Residual risks

The portfolio implementation does not constitute a complete production threat model, penetration test, compliance assessment, or certification. Production deployments require domain-specific threat modeling, red teaming, secret management, network controls, data-loss prevention, and incident response.
