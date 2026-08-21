"""핵심 데이터 모델: 프로파일, 논문, 분석 결과."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

from pydantic import BaseModel, Field


class Keyword(BaseModel):
    term: str
    weight: int = 1


class LLMConfig(BaseModel):
    provider: str = "claude"  # claude | ollama
    model: str = "claude-opus-5"
    language: str = "ko"
    effort: str = "low"  # claude 전용: low | medium | high
    fallback: bool = True  # claude 전용: 안전 거부 시 서버측 폴백
    ollama_url: str = "http://localhost:11434"


class EmailConfig(BaseModel):
    to: list[str] = Field(min_length=1)
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str | None = None  # 로그인 계정 — 비밀번호는 SMTP_PASSWORD 환경변수로만
    sender: str | None = None  # 미설정 시 smtp_user
    starttls: bool = True
    ssl: bool = False  # 465 포트(SMTPS)면 true


class DigestConfig(BaseModel):
    top_n: int = 10
    min_score: int = 4
    output_dir: str = "digests"
    obsidian_path: str | None = None
    email: EmailConfig | None = None


class Profile(BaseModel):
    categories: list[str] = Field(min_length=1)
    keywords: list[Keyword] = []
    authors: list[str] = []
    interest: str
    llm: LLMConfig = LLMConfig()
    digest: DigestConfig = DigestConfig()

    def analysis_hash(self) -> str:
        """분석 캐시 키. 요약·점수에 영향을 주는 필드만 포함한다 —
        keywords/authors 는 부스트에만 쓰이므로 제외 (수정해도 캐시 유지)."""
        payload = json.dumps(
            {
                "interest": self.interest,
                "model": self.llm.model,
                "language": self.llm.language,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


class Paper(BaseModel):
    arxiv_id: str  # 예: 2408.12345v1
    title: str
    authors: list[str]
    abstract: str
    categories: list[str]
    published: datetime
    updated: datetime
    link: str


class Analysis(BaseModel):
    summary: list[str] = Field(min_length=3, max_length=3)
    score: int = Field(ge=0, le=10)
    reason: str


class RankedPaper(BaseModel):
    paper: Paper
    analysis: Analysis
    boost: int = 0

    @property
    def final_score(self) -> int:
        return self.analysis.score + self.boost
