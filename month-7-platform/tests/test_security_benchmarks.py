from pathlib import Path

from security.redteam import load_corpus, run_benchmark


def test_redteam_corpus_is_non_empty_and_passes_safe_responder():
    cases = load_corpus()

    def safe_responder(_prompt: str) -> str:
        return "I cannot disclose secrets, customer records, privileged exports, or administrative credentials."

    result = run_benchmark(safe_responder, cases)
    assert result["passed"] is True
    assert result["total"] >= 4
    assert result["failed"] == 0


def test_migrations_have_unique_ordered_versions():
    files = sorted(Path("persistence/migrations").glob("[0-9][0-9][0-9]_*.sql"))
    versions = [int(path.name.split("_", 1)[0]) for path in files]
    assert versions == sorted(set(versions))
    assert files
