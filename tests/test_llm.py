import json

import pytest

from paper_radar.llm import (
    AnalysisError,
    build_system,
    build_user,
    make_client,
    parse_analysis,
)
from paper_radar.models import LLMConfig

from conftest import make_paper


def test_build_system_contains_interest_and_language(profile):
    s = build_system(profile)
    assert profile.interest.strip() in s
    assert "한국어" in s


def test_build_user_contains_paper_fields(profile):
    p = make_paper("2408.1v1", title="T", abstract="ABS")
    u = build_user(p)
    assert "T" in u and "ABS" in u and "Alice Kim" in u


def test_parse_analysis_valid():
    a = parse_analysis(json.dumps({"summary": ["1", "2", "3"], "score": 9, "reason": "r"}))
    assert a.score == 9


@pytest.mark.parametrize(
    "bad",
    [
        "not json",
        json.dumps({"summary": ["1", "2"], "score": 9, "reason": "r"}),  # 2줄
        json.dumps({"summary": ["1", "2", "3"], "score": 11, "reason": "r"}),  # 범위 밖
    ],
)
def test_parse_analysis_invalid(bad):
    with pytest.raises(AnalysisError):
        parse_analysis(bad)


def test_make_client_claude(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client = make_client(LLMConfig(provider="claude"))
    assert client.model == "claude-opus-5"


def test_make_client_ollama():
    client = make_client(LLMConfig(provider="ollama", model="qwen3:14b"))
    assert client.model == "qwen3:14b"


def test_make_client_unknown():
    with pytest.raises(ValueError):
        make_client(LLMConfig(provider="gpt"))
