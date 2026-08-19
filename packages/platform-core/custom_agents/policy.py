"""Fail-closed policy boundary for custom workflows."""
HIGH_IMPACT_ACTIONS = frozenset({"approve_payment", "approve_purchase", "award_supplier", "disable_account", "isolate_endpoint", "clinical_intervention", "reject_contract", "send_customer_notice"})


def requires_human_approval(action: str, context: dict | None = None) -> bool:
    if action in HIGH_IMPACT_ACTIONS:
        return True
    return bool((context or {}).get("require_human_approval"))
