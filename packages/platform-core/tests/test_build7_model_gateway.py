from __future__ import annotations

from fde_platform.identity import Environment, Principal, PrincipalType, RequestContext, TenantRef
from fde_platform.models import (
    DataClass,
    ModelCapability,
    ModelDefinition,
    ModelErrorCode,
    ModelGateway,
    ModelMessage,
    ModelRegistry,
    ModelRequest,
    ModelResponse,
)


def context() -> RequestContext:
    tenant = TenantRef("tenant-a", Environment.STAGING)
    principal = Principal("user-a", tenant.tenant_id, PrincipalType.USER)
    return RequestContext(principal, tenant, "req-model-1", Environment.STAGING)


def request(model: str | None = "chat") -> ModelRequest:
    return ModelRequest(
        context=context(),
        model=model,
        messages=(ModelMessage("user", "hello"),),
        required_capabilities=frozenset({ModelCapability.CHAT}),
        data_class=DataClass.INTERNAL,
        max_output_tokens=64,
        request_id="req-model-1",
    )


class FakeProvider:
    def __init__(self, response: ModelResponse) -> None:
        self.response = response
        self.calls = 0

    def generate(self, definition: ModelDefinition, request: ModelRequest) -> ModelResponse:
        self.calls += 1
        return self.response


def registered_gateway(provider: FakeProvider) -> ModelGateway:
    registry = ModelRegistry()
    registry.register(
        ModelDefinition(
            "chat-model", "1.0.0", "provider-a",
            frozenset({ModelCapability.CHAT}),
            frozenset({DataClass.PUBLIC, DataClass.INTERNAL}),
            context_window=8192,
            max_output_tokens=1024,
        )
    )
    registry.route("chat", ("chat-model@1.0.0",))
    return ModelGateway(registry, {"provider-a": provider})


def test_gateway_invokes_allowlisted_model() -> None:
    provider = FakeProvider(ModelResponse(True, "hello", "chat-model", "provider-a"))
    result = registered_gateway(provider).invoke(request())
    assert result.success
    assert result.output == "hello"
    assert provider.calls == 1


def test_gateway_fails_closed_for_unknown_model() -> None:
    provider = FakeProvider(ModelResponse(True, "unexpected"))
    result = registered_gateway(provider).invoke(request("missing"))
    assert result.error_code == ModelErrorCode.MODEL_NOT_FOUND
    assert provider.calls == 0


def test_gateway_denies_unsupported_capability_and_data_class() -> None:
    provider = FakeProvider(ModelResponse(True, "unexpected"))
    gateway = registered_gateway(provider)
    capability_request = ModelRequest(
        context=context(), model="chat", messages=(ModelMessage("user", "x"),),
        required_capabilities=frozenset({ModelCapability.VISION}), request_id="req-model-1"
    )
    restricted_request = ModelRequest(
        context=context(), model="chat", messages=(ModelMessage("user", "x"),),
        data_class=DataClass.RESTRICTED, request_id="req-model-1"
    )
    assert gateway.invoke(capability_request).error_code == ModelErrorCode.CAPABILITY_DENIED
    assert gateway.invoke(restricted_request).error_code == ModelErrorCode.DATA_CLASS_DENIED
    assert provider.calls == 0


def test_gateway_falls_back_only_on_retryable_provider_failure() -> None:
    registry = ModelRegistry()
    registry.register(ModelDefinition("primary", "1.0.0", "p1", frozenset({ModelCapability.CHAT})))
    registry.register(ModelDefinition("fallback", "1.0.0", "p2", frozenset({ModelCapability.CHAT})))
    registry.route("chat", ("primary@1.0.0", "fallback@1.0.0"))
    primary = FakeProvider(ModelResponse(False, error_code=ModelErrorCode.RATE_LIMITED, retryable=True))
    fallback = FakeProvider(ModelResponse(True, "ok", "fallback", "p2"))
    result = ModelGateway(registry, {"p1": primary, "p2": fallback}).invoke(request())
    assert result.output == "ok"
    assert primary.calls == 1
    assert fallback.calls == 1


def test_gateway_never_falls_back_on_non_retryable_failure() -> None:
    registry = ModelRegistry()
    registry.register(ModelDefinition("primary", "1.0.0", "p1", frozenset({ModelCapability.CHAT})))
    registry.register(ModelDefinition("fallback", "1.0.0", "p2", frozenset({ModelCapability.CHAT})))
    registry.route("chat", ("primary@1.0.0", "fallback@1.0.0"))
    primary = FakeProvider(ModelResponse(False, error_code=ModelErrorCode.INVALID_REQUEST))
    fallback = FakeProvider(ModelResponse(True, "unsafe fallback", "fallback", "p2"))
    result = ModelGateway(registry, {"p1": primary, "p2": fallback}).invoke(request())
    assert result.error_code == ModelErrorCode.INVALID_REQUEST
    assert fallback.calls == 0


def test_gateway_policy_is_evaluated_before_provider() -> None:
    provider = FakeProvider(ModelResponse(True, "unexpected"))
    gateway = registered_gateway(provider)
    denied = ModelGateway(gateway.registry, gateway.providers, lambda_policy())
    result = denied.invoke(request())
    assert result.error_code == ModelErrorCode.POLICY_DENIED
    assert provider.calls == 0


def lambda_policy():
    from fde_platform.models import static_policy
    return static_policy(lambda context, definition, request: False)
