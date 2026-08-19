# Interactive demonstration

## Five-minute walkthrough

1. Start the API in test mode with the mock provider.
2. Open `/docs` and authenticate with the demo API key.
3. Execute one request for each of the six domains.
4. Show the returned structured `DomainAgentResult`.
5. Trigger an invalid domain and show the controlled error.
6. Show request correlation and audit-event records when PostgreSQL is enabled.
7. Show OpenTelemetry spans when `OTEL_ENABLED=true`.
8. Open the GitHub Actions release workflow and show the immutable image, signature, and SBOM attestation.

## Demo safety

The demo uses synthetic data and mock AI providers. It must never contain production credentials, patient data, financial records, private contracts, or customer secrets.
