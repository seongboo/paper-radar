"""LLM 분석 레이어: 논문 1편당 1콜로 {3줄 요약, 점수, 근거}를 받는다.

provider 추상화: ClaudeClient(기본) / OllamaClient(로컬).
둘 다 JSON 스키마 강제(structured output)로 같은 Analysis 를 낸다.
"""

from __future__ import annotations

import json
from typing import Protocol

from pydantic import ValidationError

from .models import Analysis, LLMConfig, Paper, Profile

ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 3,
        },
        "score": {"type": "integer", "minimum": 0, "maximum": 10},
        "reason": {"type": "string"},
    },
    "required": ["summary", "score", "reason"],
    "additionalProperties": False,
}

_LANG_NAMES = {"ko": "한국어", "en": "English", "ja": "日本語"}


class AnalysisError(Exception):
    """한 편의 분석 실패 — 파이프라인은 해당 논문만 건너뛴다."""


class LLMClient(Protocol):
    model: str

    def analyze(self, paper: Paper, profile: Profile) -> Analysis: ...


def build_system(profile: Profile) -> str:
    lang = _LANG_NAMES.get(profile.llm.language, profile.llm.language)
    return (
        "당신은 연구자의 논문 서베이를 돕는 조수다.\n"
        "사용자의 연구 관심사:\n"
        f"{profile.interest.strip()}\n\n"
        "논문의 제목·초록을 읽고 다음 필드를 채워라:\n"
        f"- summary: 논문 핵심을 {lang} 3줄로 (원소 3개, 각 1문장)\n"
        "- score: 위 관심사와의 관련도 0~10 정수 (10=정확히 관심 주제, 0=무관)\n"
        f"- reason: 점수 근거 1문장 ({lang})"
    )


def build_user(paper: Paper) -> str:
    return (
        f"제목: {paper.title}\n"
        f"저자: {', '.join(paper.authors)}\n"
        f"카테고리: {', '.join(paper.categories)}\n"
        f"초록: {paper.abstract}"
    )


def parse_analysis(text: str) -> Analysis:
    try:
        return Analysis.model_validate(json.loads(text))
    except (json.JSONDecodeError, ValidationError) as e:
        raise AnalysisError(f"LLM 응답 파싱 실패: {e}") from e


class ClaudeClient:
    def __init__(self, cfg: LLMConfig):
        import anthropic  # 선택 의존이 아니므로 상단 import 도 가능하지만, ollama 만 쓰는 환경 배려

        self._anthropic = anthropic
        self._client = anthropic.Anthropic()
        self._cfg = cfg
        self.model = cfg.model

    def analyze(self, paper: Paper, profile: Profile) -> Analysis:
        kwargs = dict(
            model=self._cfg.model,
            max_tokens=4000,
            system=build_system(profile),
            messages=[{"role": "user", "content": build_user(paper)}],
            output_config={
                "format": {"type": "json_schema", "schema": ANALYSIS_SCHEMA},
                "effort": self._cfg.effort,
            },
        )
        try:
            if self._cfg.fallback:
                # 안전 거부 시 같은 요청을 폴백 모델로 서버가 재실행
                response = self._client.beta.messages.create(
                    betas=["server-side-fallback-2026-07-01"],
                    fallbacks="default",
                    **kwargs,
                )
            else:
                response = self._client.messages.create(**kwargs)
        except self._anthropic.APIStatusError as e:
            raise AnalysisError(f"Claude API 오류({e.status_code}): {e.message}") from e
        except self._anthropic.APIConnectionError as e:
            raise AnalysisError(f"Claude API 연결 실패: {e}") from e

        if response.stop_reason == "refusal":
            raise AnalysisError("모델이 분석을 거부함 (safety refusal)")
        text = next((b.text for b in response.content if b.type == "text"), None)
        if text is None:
            raise AnalysisError(f"텍스트 응답 없음 (stop_reason={response.stop_reason})")
        return parse_analysis(text)


class OllamaClient:
    def __init__(self, cfg: LLMConfig):
        self._cfg = cfg
        self.model = cfg.model

    def analyze(self, paper: Paper, profile: Profile) -> Analysis:
        import httpx

        try:
            r = httpx.post(
                f"{self._cfg.ollama_url}/api/chat",
                json={
                    "model": self._cfg.model,
                    "messages": [
                        {"role": "system", "content": build_system(profile)},
                        {"role": "user", "content": build_user(paper)},
                    ],
                    "stream": False,
                    "format": ANALYSIS_SCHEMA,
                },
                timeout=300.0,
            )
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise AnalysisError(f"Ollama 호출 실패: {e}") from e
        return parse_analysis(r.json()["message"]["content"])


def make_client(cfg: LLMConfig) -> LLMClient:
    if cfg.provider == "claude":
        return ClaudeClient(cfg)
    if cfg.provider == "ollama":
        return OllamaClient(cfg)
    raise ValueError(f"지원하지 않는 llm.provider: {cfg.provider!r} (claude | ollama)")
