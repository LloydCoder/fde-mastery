# Custom Agents

Customer-specific workflows live behind a tenant-scoped contract instead of modifying first-party domain code.

## Safety requirements

- Agent specifications are versioned.
- Registry keys include tenant ID and agent name.
- Tools are explicitly allowlisted.
- High-impact actions require human approval.
- Customer data and credentials must never be committed to the repository.
- Every production custom agent should have a golden dataset, evaluation threshold, audit policy, and rollback path.

This layer is intended to support FDE engagements where a customer workflow does not justify creating a new permanent platform domain.
