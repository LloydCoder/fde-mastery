"""Deterministic model gateway reference implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..identity import RequestContext
from .models import (
    ModelDefinition,
    ModelErrorCode,
    ModelPolicy,
    ModelProvider,
    ModelRequest,
    ModelResponse,
)


@dataclass(frozen=True, slots=True)
class ModelGateway:
    """Interface for governed model invocation and routing."""

    registry: "ModelRegistry"
    providers: dict[str, ModelProvider]
    policy: ModelPolicy | None = None

    def invoke(self, request: ModelRequest) -> ModelResponse:
        candidates = self.registry.resolve(request.model)
        if not candidates:
            return ModelResponse(False, error_code=ModelErrorCode.MODEL_NOT_FOUND)

        last_failure: ModelResponse | None = None
        for definition in candidates:
            if not definition.enabled:
                continue
            if request.required_capabilities - definition.capabilities:
                last_failure = ModelResponse(
                    False, model=definition.name, provider=definition.provider,
                    error_code=ModelErrorCode.CAPABILITY_DENIED,
                )
                continue
            if request.data_class not in definition.allowed_data_classes:
                last_failure = ModelResponse(
                    False, model=definition.name, provider=definition.provider,
                    error_code=ModelErrorCode.DATA_CLASS_DENIED,
                )
                continue
            if definition.max_output_tokens and request.max_output_tokens > definition.max_output_tokens:
                last_failure = ModelResponse(
                    False, model=definition.name, provider=definition.provider,
                    error_code=ModelErrorCode.BUDGET_EXCEEDED,
                )
                continue
            if self.policy is not None and not self.policy.allow(request.context, definition, request):
                last_failure = ModelResponse(
                    False, model=definition.name, provider=definition.provider,
                    error_code=ModelErrorCode.POLICY_DENIED,
                )
                continue
            provider = self.providers.get(definition.provider)
            if provider is None:
                last_failure = ModelResponse(
                    False, model=definition.name, provider=definition.provider,
                    error_code=ModelErrorCode.PROVIDER_ERROR, retryable=True,
                )
                continue
            response = provider.generate(definition, request)
            if response.success or not response.retryable:
                return response
            last_failure = response
        return last_failure or ModelResponse(False, error_code=ModelErrorCode.MODEL_NOT_FOUND)


class ModelRegistry:
    """Allowlisted model catalog with deterministic ordered fallback routes."""

    def __init__(self) -> None:
        self._models: dict[str, ModelDefinition] = {}
        self._routes: dict[str, tuple[str, ...]] = {}

    def register(self, definition: ModelDefinition) -> None:
        key = self._key(definition.name, definition.version)
        if key in self._models:
            raise ValueError("model version is already registered")
        self._models[key] = definition

    def route(self, alias: str, model_versions: tuple[str, ...]) -> None:
        if not alias.strip() or not model_versions:
            raise ValueError("route alias and candidates are required")
        if any(candidate not in self._models for candidate in model_versions):
            raise ValueError("route contains an unregistered model")
        self._routes[alias] = model_versions

    def resolve(self, requested: str | None) -> tuple[ModelDefinition, ...]:
        if requested is None:
            return ()
        candidates = self._routes.get(requested, (requested,))
        return tuple(self._models[key] for key in candidates if key in self._models)

    @staticmethod
    def _key(name: str, version: str) -> str:
        return f"{name}@{version}"


def static_policy(allowed: Callable[[RequestContext, ModelDefinition, ModelRequest], bool]) -> ModelPolicy:
    """Create a small policy adapter without coupling the gateway to a policy engine."""

    class _Policy:
        def allow(self, context: RequestContext, definition: ModelDefinition, request: ModelRequest) -> bool:
            return allowed(context, definition, request)

    return _Policy()
