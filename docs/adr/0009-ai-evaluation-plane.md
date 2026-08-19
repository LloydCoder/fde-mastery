# ADR 0009 — AI Evaluation Plane

- **Status:** Accepted
- **Date:** 2026-08-19
- **Build:** 9

## Context

Production AI systems require evidence that changes preserve capability, safety, quality and operational constraints. A single aggregate benchmark is insufficient for agentic systems because the harness, tools, budgets, scorers and environment can materially change results.

## Decision

FDE Mastery introduces a framework-neutral evaluation plane with five explicit evaluation classes:

1. Golden regression cases for deterministic capability/quality behavior.
2. Adversarial cases for hostile or boundary inputs.
3. Safety cases with fail-closed prohibited-output checks.
4. Quality and structural scorers with bounded scores.
5. Cost/latency measurements captured alongside quality results.

Datasets are versioned and fingerprinted. Evaluation runs record dataset provenance and model identity. Promotion is an explicit gate based on pass rate, mean score, safety failures and optional cost/latency budgets.

Evaluation inputs remain data; the harness does not execute case content as code. Provider/model adapters are supplied by trusted application code through an explicit callable boundary.

## Validity requirements

Evaluation reports must preserve enough information to reproduce interpretation: dataset name/version/fingerprint, model reference, result metrics, scorer behavior and promotion thresholds. Future agentic evaluations must also record tool access, budgets and validity checks for shortcutting, reward hacking, contamination and evaluation awareness.

## Consequences

Positive:

- regressions become merge/release gates;
- model changes can be compared using stable datasets;
- safety is independently measurable from capability;
- cost and latency are first-class constraints;
- later observability can correlate production telemetry with evaluation evidence.

Trade-offs:

- maintaining high-quality datasets is ongoing work;
- deterministic scorers cannot capture every semantic quality dimension;
- adversarial suites require continuous refresh as threats evolve;
- evaluation results must be interpreted with validity checks rather than treated as absolute capability claims.

## Standards and research basis

The design follows NIST AI RMF/GenAI evaluation and governance principles, NIST's Test, Evaluation, Verification and Validation emphasis, and OWASP GenAI red-teaming guidance. Current frontier-evaluation practice also requires visibility into the tested system, harness, tools, budgets and validity hazards rather than relying on headline scores alone.
