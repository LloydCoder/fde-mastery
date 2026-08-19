# Canonical Domain Services

The `domains/` namespace is the production-facing architecture vocabulary for FDE Mastery.

The first six domains currently expose compatibility facades over the existing Month 1–6 implementations. This is intentional: it allows the repository to move from curriculum-oriented names to domain-oriented names without breaking imports, FastAPI routes, or integration contracts.

Procurement is implemented natively under `domains/procurement/` and is the reference pattern for future first-class domains.

## Promotion contract

Every domain must expose a shared adapter contract, health/capabilities metadata, evaluation tests, human-approval boundaries for high-impact actions, and representative evaluation data before customer promotion.
