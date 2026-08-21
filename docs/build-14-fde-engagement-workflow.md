# Build 14 — FDE Engagement & Workflow Engine

## Objective

Turn the platform's domain and workflow primitives into a governed FDE delivery lifecycle. The capability makes customer objectives, workflow identity, measurable value, acceptance criteria, evidence and promotion gates explicit while reusing the existing durable workflow runtime.

## Delivered

- Tenant-scoped `FDEEngagement` contract.
- `MetricDefinition` with immutable baseline and target values.
- Explicit `AcceptanceCriterion` and evidence references.
- Lifecycle stages from discovery through retirement.
- Fail-closed stage transition validation.
- Block/resume/cancel lifecycle controls.
- `FDEStageGate` promotion contracts.
- Explicit human-approval requirements for pilot, shadow, production and transfer.
- Production deployment evidence requirement.
- Deterministic promotion readiness reporting.
- Compiler from the FDE lifecycle into the existing `WorkflowDefinition` contract.
- Contract tests for transition safety, promotion gates, workflow compilation, evidence requirements and tenant scoping.

## Lifecycle

```text
discovery
  ↓
workflow_mapping
  ↓
value_case
  ↓
architecture
  ↓
build
  ↓
evaluation
  ↓
pilot ───────────────┐
  ↓                  │
shadow               │
  ↓                  │
production ←─────────┘
  ↓
operate
  ↓
transfer
  ↓
retired
```

Pilot can move directly to production when all required gates are satisfied; shadow mode provides the safer controlled path.

## Architecture

```text
FDEEngagement
     │
     ├── objective
     ├── value metrics
     ├── acceptance criteria
     └── evidence
            │
            ▼
       FDEWorkflow
            │
       promotion gates
            │
            ▼
 Existing WorkflowDefinition
            │
            ▼
 Existing durable workflow runtime
            │
      ┌─────┼─────┐
    Policy Tools Models
      │      │      │
      └──────┼──────┘
             ▼
       Audit / Eval / Ops
```

The engagement layer is a control-plane contract. It does not execute external side effects and does not create a second workflow engine.

## Security

- Tenant identity is mandatory.
- Invalid lifecycle transitions fail closed.
- Promotion stages with high operational impact require explicit approval evidence.
- Production requires deployment and approval evidence.
- Evidence references are immutable; payload storage remains outside this contract.
- Model output is never an authorization decision.
- Existing identity, policy, tool, model, approval, evaluation and audit boundaries remain authoritative.

## Research basis

The implementation follows production FDE lifecycle practice: qualify a real workflow, establish measurable value, design/build, evaluate, pilot, deploy, transfer and operate the resulting service. NIST AI RMF organizes AI risk management around Govern, Map, Measure and Manage and recommends testing before deployment and regularly in operation. OWASP's 2026 Agentic Applications work treats autonomous-agent security as a lifecycle and operational concern.

## Verification

Build 14 is complete only after the complete Platform Quality workflow is green, including pytest, domain checks, enterprise controls, migration validation, Ruff, MyPy, Bandit, dependency audit, compile validation, Terraform, SBOM, staging/load smoke, production Docker runtime smoke and Semgrep.

## Version

Platform version: **1.13.0**
