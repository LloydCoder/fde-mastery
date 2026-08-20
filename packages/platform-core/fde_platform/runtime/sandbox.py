"""Sandbox policy contracts for untrusted/custom agent workloads.

This module deliberately defines policy, not an unsafe in-process sandbox. A
production adapter should map the policy to containers, microVMs or another
isolated execution substrate.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SandboxPolicy:
    network: str = "deny"
    filesystem: str = "ephemeral"
    credentials: str = "task-scoped"
    cpu_seconds: int = 30
    memory_mb: int = 512
    timeout_seconds: int = 60

    def __post_init__(self) -> None:
        if self.network not in {"deny", "allowlisted"}:
            raise ValueError("network must be deny or allowlisted")
        if self.filesystem not in {"ephemeral", "read-only"}:
            raise ValueError("unsupported filesystem policy")
        if self.credentials not in {"none", "task-scoped"}:
            raise ValueError("unsupported credential policy")
        if min(self.cpu_seconds, self.memory_mb, self.timeout_seconds) <= 0:
            raise ValueError("sandbox resource limits must be positive")


class SandboxViolation(PermissionError):
    """Raised when an execution request exceeds the declared sandbox policy."""


def validate_sandbox(policy: SandboxPolicy, *, network_access: bool, credential_scope: str) -> None:
    if network_access and policy.network == "deny":
        raise SandboxViolation("network access denied by sandbox policy")
    if credential_scope not in {"", "task-scoped"}:
        raise SandboxViolation("credential scope is broader than task-scoped policy")
    if credential_scope == "task-scoped" and policy.credentials == "none":
        raise SandboxViolation("task-scoped credentials are disabled by sandbox policy")
