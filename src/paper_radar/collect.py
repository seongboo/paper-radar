"""arXiv 수집: 프로파일 카테고리의 최근 논문을 정규화해 가져온다."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import arxiv

from .models import Paper, Profile

# 최근 며칠치를 훑을지. seen dedupe 가 있으므로 하루 이틀 실행을 건너뛰어도
# 이 창 안에서 복구된다.
DEFAULT_WINDOW_DAYS = 2
DEFAULT_MAX_RESULTS = 500


def build_query(categories: list[str]) -> str:
    return " OR ".join(f"cat:{c}" for c in categories)


def _squash(text: str) -> str:
    """arXiv 피드의 제목/초록에 섞인 개행·연속 공백을 한 칸으로."""
    return " ".join(text.split())


def paper_from_result(result) -> Paper:
    """arxiv.Result → Paper. 테스트에서는 동일 속성을 가진 스텁을 넘긴다."""
    return Paper(
        arxiv_id=result.get_short_id(),
        title=_squash(result.title),
        authors=[a.name for a in result.authors],
        abstract=_squash(result.summary),
        categories=list(result.categories),
        published=result.published,
        updated=result.updated,
        link=result.entry_id,
    )


def fetch_recent(
    profile: Profile,
    window_days: int = DEFAULT_WINDOW_DAYS,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> Iterator[Paper]:
    """최근 window_days 안에 갱신된 논문을 최신순으로 낸다.

    arxiv.Client 가 요청 간격(3초)·페이징·재시도를 처리한다.
    결과가 최신순 정렬이므로 창을 벗어나면 바로 중단한다.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    client = arxiv.Client(page_size=100, delay_seconds=3.0, num_retries=3)
    search = arxiv.Search(
        query=build_query(profile.categories),
        max_results=max_results,
        sort_by=arxiv.SortCriterion.LastUpdatedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    for result in client.results(search):
        if result.updated < cutoff:
            break
        yield paper_from_result(result)
