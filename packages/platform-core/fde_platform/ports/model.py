"""Model-provider boundary."""

from typing import Any, Mapping, Protocol


class ModelPort(Protocol):
    """Provider-neutral model invocation contract."""

    def generate(self, prompt: str, *, metadata: Mapping[str, Any] | None = None) -> str:
        """Generate a response without exposing provider-specific APIs to callers."""
