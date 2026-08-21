# Build 24 — Customer Value Plane

## Objective

Provide a deterministic, tenant-scoped value-realization contract that connects an FDE engagement objective to measurable customer outcomes without fabricating business results.

## Design

```text
Customer Objective
      ↓
Value Plan
      ↓
Metric + Baseline + Target
      ↓
Evidence-backed Observation
      ↓
Deterministic Calculation
      ↓
Value Report
```

The plane intentionally stores evidence references rather than raw customer content. Governance evidence remains owned by the existing evidence/control plane.

## Delivered

- Typed metric contracts for count, rate, duration, currency and ratio outcomes.
- Explicit increase/decrease/minimize/maximize directionality.
- Baseline and target contracts with optional bounds and deadlines.
- Tenant + engagement binding.
- Timezone-aware observations.
- Evidence status handling; rejected evidence cannot contribute to value reporting.
- Cross-tenant observations are ignored by the calculator.
- Deterministic latest-observation selection.
- Bounded 0..1 target-progress calculation.
- Achievement evaluation based on declared direction.
- Safe zero-baseline handling.
- Evidence-reference output for audit traceability.
- Deterministic SHA-256 evidence digest as an integrity aid.
- Decimal parser that rejects NaN/Infinity.
- Bounded metadata to prevent unbounded telemetry-style cardinality.

## Engineering decisions

The implementation is deliberately framework-agnostic. It is a contract/calculation layer, not a second telemetry or analytics platform. Existing observability and engagement systems remain the integration points.

OpenTelemetry guidance recommends consistent metric naming and attributes, meaningful aggregation, and explicit cardinality controls. High-cardinality identifiers such as user IDs should not become metric dimensions. The value plane therefore keeps tenant/engagement/evidence identifiers in the value-domain records and does not define them as unbounded telemetry attributes. citeturn0search2turn0search3

NIST AI RMF's Measure function calls for quantitative/qualitative measurement, benchmarking, uncertainty consideration, regular testing, and documented reporting. The value plane supplies the deterministic measurement/evidence contract; customer-specific baselines and outcome claims still require real evidence. citeturn0search12

## Non-goals

- No fabricated ROI or savings claims.
- No autonomous financial/accounting assertions.
- No raw prompt/customer-content storage in observations.
- No replacement for the existing telemetry system.
- No replacement for the governance evidence registry.
- No customer-production success claim without customer evidence.

## Verification

Build-specific tests cover:

- outcome calculation;
- directionality;
- target achievement;
- progress bounding;
- cross-tenant isolation;
- rejected evidence;
- timezone validation;
- finite numeric values;
- zero-baseline handling;
- deterministic evidence digest;
- bounded metadata.
