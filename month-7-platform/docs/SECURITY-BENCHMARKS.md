# AI Security Red-Team Benchmarks

The platform uses repeatable, non-production adversarial tests for prompt injection, instruction override, sensitive-data extraction, tool misuse, and unsafe output handling.

## Required benchmark properties

- deterministic fixtures
- no production credentials
- no real customer data
- expected-safe outcome for every case
- regression tracking by release
- CI gate for critical regressions

## Initial benchmark classes

1. Prompt injection through untrusted domain input
2. System-instruction override attempts
3. Secret extraction requests
4. Cross-tenant data access attempts
5. Tool-argument manipulation
6. Malicious or malformed structured output
7. Excessive-resource requests

A benchmark failure blocks a release when the expected security invariant is violated.
