# Agent Resilience

The Month 7 router wraps each domain adapter in an independent resilience executor. A failure in one domain therefore does not open the circuit for unrelated domains.

## Controls

- bounded execution timeout
- bounded retries for transient connection/timeout/OS failures
- exponential backoff with jitter
- per-domain circuit breaker
- per-domain concurrency limit
- timeout failures are terminal for the request; the platform does not retry a still-running timed-out operation
- standardized API errors
- failure audit events
- readiness/agent health visibility

## Configuration

```text
FDE_AGENT_TIMEOUT_SECONDS=30
FDE_AGENT_MAX_RETRIES=2
FDE_AGENT_BACKOFF_SECONDS=0.25
FDE_AGENT_MAX_BACKOFF_SECONDS=2
FDE_AGENT_CIRCUIT_FAILURE_THRESHOLD=5
FDE_AGENT_CIRCUIT_RECOVERY_SECONDS=30
FDE_AGENT_MAX_CONCURRENCY=32
```

Keep timeout and concurrency values aligned with provider quotas, worker capacity, and expected request latency. Production values should be validated with load testing.

## Error contract

Agent failures use machine-readable error codes without exposing provider exceptions or stack traces:

- `AGENT_TIMEOUT` — `504`, retryable
- `AGENT_CIRCUIT_OPEN` — `503`, retryable
- `INVALID_AGENT_INPUT` — `422`, not retryable
- `AGENT_EXECUTION_FAILED` — `500`, not retryable

Every response includes the request ID for correlation with logs and audit records.
