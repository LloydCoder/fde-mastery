# Security Policy

FDE Mastery includes security-sensitive boundaries for identity, tenant isolation, agent execution, tool access, model integrations, approvals, secrets and audit evidence. Responsible disclosure helps protect users and deployments.

## Supported versions

Security fixes are prioritized for the latest code on `main`. Older tags and forks may not receive fixes. Include the affected commit, tag or deployment version in a report.

## Report a vulnerability privately

**Do not create a public GitHub issue or pull request for an undisclosed vulnerability.**

Use [GitHub Private Vulnerability Reporting](https://github.com/LloydCoder/fde-mastery/security/advisories/new). If that route is unavailable, email **hello@tinlance.com** with the subject `Private Security Report — FDE Mastery`. Do not include live credentials or unnecessary personal/customer data in the initial report.

Where possible, include:

- A concise description and affected component.
- The affected commit, tag or deployment version.
- Preconditions and reproducible steps.
- Impact and a realistic attack scenario.
- Proof-of-concept material that does not access or expose third-party data.
- Suggested mitigation, if known.

## Response expectations

| Activity | Target |
|---|---|
| Initial acknowledgement | Within 5 business days |
| Initial triage and severity assessment | Within 10 business days |
| Status updates | At least every 10 business days while active |
| Remediation | Based on severity, exploitability and release risk |

These are response targets, not a guarantee of a fixed remediation date. Critical issues may require coordinated mitigation or deployment-specific action.

## Coordinated disclosure

Allow time for investigation and a coordinated fix before public disclosure. The maintainer will coordinate an appropriate disclosure timeline with the reporter. Do not publish exploit details while users remain exposed.

## Security scope

Relevant areas include authentication and authorization, tenant boundaries, APIs and webhooks, secrets, tool/model gateways, prompt injection, agent permissions, approval enforcement, persistence, deployment configuration, CI workflows and software supply chain.

A green CI run or signed artifact is not a security certification. Customer deployments require environment-specific threat modeling, configuration review and operational controls.
