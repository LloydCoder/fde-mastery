# Build 9 — AI Evaluation Plane

## Objective

Make evaluation a first-class platform capability and release gate rather than an ad-hoc benchmark.

## Delivered

- immutable evaluation cases and versioned datasets
- SHA-256 dataset/case fingerprints
- golden, adversarial, safety, quality and cost evaluation classes
- deterministic exact-match and safety regression scorers
- evaluation harness with explicit trusted adapter boundary
- latency and cost capture
- evaluation-run provenance: model reference + dataset fingerprint
- explicit promotion thresholds and PROMOTE/REJECT decision
- regression/security tests

## Promotion gate

```text
Dataset version + fingerprint
            ↓
     Evaluation Harness
            ↓
 ┌──────────┼──────────┐
Golden   Adversarial  Safety
   │          │          │
   └──────────┼──────────┘
              ↓
       Quality + Cost
              ↓
        Promotion Gate
          ↙        ↘
      PROMOTE     REJECT
```

Promotion requires all configured thresholds to pass. Safety failures are independently counted and cannot be hidden by a high aggregate quality score.

## Security properties

1. Case content is treated as untrusted data and is never evaluated as executable code.
2. Safety scoring is fail-closed for configured prohibited terms.
3. Dataset versions and fingerprints make silent test-set mutation detectable.
4. Model identity is recorded with every evaluation run.
5. Evaluation thresholds are explicit rather than embedded in individual scorers.
6. Agentic evaluations must include tool access, budgets and validity checks before being used as capability evidence.

## Standards basis

The design is informed by NIST AI RMF and its Generative AI Profile, NIST GenAI evaluation programs, and OWASP GenAI red-teaming/evaluation guidance. Current evaluation research emphasizes validity checks for reward hacking, contamination, evaluation awareness and harness-specific behavior.
