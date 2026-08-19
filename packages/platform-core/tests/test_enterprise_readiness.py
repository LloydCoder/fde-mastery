from evaluation.enterprise_gate import Gate, evaluate_readiness, is_ready


def complete_evidence():
    return {gate: True for gate in Gate}


def test_all_eight_gates_are_explicit():
    results = evaluate_readiness(complete_evidence())
    assert len(results) == 8
    assert all(result.passed for result in results)
    assert is_ready(complete_evidence()) is True


def test_missing_gate_fails_closed():
    evidence = complete_evidence()
    evidence.pop(Gate.SHADOW)
    results = evaluate_readiness(evidence)
    assert is_ready(evidence) is False
    assert next(r for r in results if r.gate is Gate.SHADOW).passed is False


def test_customer_specific_tool_gate_is_explicit():
    evidence = complete_evidence()
    evidence[Gate.TOOL_INTEGRATION] = False
    assert is_ready(evidence) is False
