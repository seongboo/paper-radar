"""파이프라인 단계 연결: 수집 → 분석(캐시) → 랭킹 → 다이제스트.

각 단계는 의존성 주입(fetch, llm, store)을 받아 네트워크 없이 테스트된다.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

from . import mailer
from .digest import write_digest
from .llm import AnalysisError, LLMClient
from .models import Analysis, Paper, Profile
from .rank import rank
from .store import Store

log = logging.getLogger("paper_radar")


def collect_new(store: Store, papers: Iterable[Paper], seen_date: str) -> list[Paper]:
    """수집분 중 처음 보는 논문만 저장하고 돌려준다."""
    new = [p for p in papers if store.insert_paper(p, seen_date)]
    store.record_run(len(new))
    return new


def analyze_papers(
    store: Store, profile: Profile, llm: LLMClient, papers: list[Paper]
) -> list[tuple[Paper, Analysis]]:
    """논문별 분석. 캐시 히트면 API 호출 없음, 실패한 논문은 건너뛴다."""
    profile_hash = profile.analysis_hash()
    pairs: list[tuple[Paper, Analysis]] = []
    for i, paper in enumerate(papers, start=1):
        analysis = store.get_analysis(paper.arxiv_id, profile_hash)
        if analysis is None:
            log.info("분석 중 (%d/%d): %s", i, len(papers), paper.arxiv_id)
            try:
                analysis = llm.analyze(paper, profile)
            except AnalysisError as e:
                log.warning("건너뜀 %s: %s", paper.arxiv_id, e)
                continue
            store.save_analysis(paper.arxiv_id, profile_hash, analysis, llm.model)
        pairs.append((paper, analysis))
    return pairs


def make_digest(
    store: Store, profile: Profile, llm: LLMClient, date: str, papers: list[Paper]
) -> Path:
    pairs = analyze_papers(store, profile, llm, papers)
    ranked = rank(pairs, profile)
    path = write_digest(date, ranked, profile)
    log.info("다이제스트 생성: %s (%d편)", path, len(ranked))

    if profile.digest.email:
        try:
            mailer.send_digest(
                profile.digest.email, date, path.read_text(encoding="utf-8")
            )
            log.info("메일 발송: %s", ", ".join(profile.digest.email.to))
        except Exception as e:  # 파일은 이미 생성됐으므로 발송 실패로 실행을 깨지 않는다
            log.error("메일 발송 실패 (다이제스트 파일은 생성됨): %s", e)

    return path
