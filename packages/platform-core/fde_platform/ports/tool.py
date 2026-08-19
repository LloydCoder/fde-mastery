"""Tool invocation boundary."""

from typing import Any, Mapping, Protocol


class ToolPort(Protocol):
    """Provider-neutral tool capability contract."""

    def invoke(self, tool_id: str, arguments: Mapping[str, Any]) -> Any:
        """Invoke a named capability through an external tool adapter."""
