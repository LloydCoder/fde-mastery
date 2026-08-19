from evaluation.generate_golden import CASES_PER_DOMAIN, DOMAINS, build_case


def test_golden_dataset_has_100_cases_per_domain():
    for domain in DOMAINS:
        cases = [build_case(domain, i) for i in range(CASES_PER_DOMAIN)]
        assert len(cases) == 100
        assert len({case["id"] for case in cases}) == 100
        assert {case["label"] for case in cases} == {"benign", "suspicious", "malicious", "ambiguous"}
