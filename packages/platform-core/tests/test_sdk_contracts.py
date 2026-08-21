import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sdks" / "python"))

from fde_mastery import FDEMasteryClient  # noqa: E402


def test_python_sdk_requires_https_outside_localhost() -> None:
    with pytest.raises(ValueError):
        FDEMasteryClient("http://api.example.com")


def test_python_sdk_rejects_ambiguous_credentials() -> None:
    with pytest.raises(ValueError):
        FDEMasteryClient("https://api.example.com", api_key="a", bearer_token="b")


def test_python_sdk_validates_timeout_and_retry_bounds() -> None:
    with pytest.raises(ValueError):
        FDEMasteryClient("https://api.example.com", timeout=0)
    with pytest.raises(ValueError):
        FDEMasteryClient("https://api.example.com", max_retries=6)
