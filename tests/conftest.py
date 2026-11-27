from datetime import datetime, timezone

import pytest

from paper_radar.llm import AnalysisError
from paper_radar.models import Analysis, Keyword, Paper, Profile


def make_paper(arxiv_id: str, title: str = "A Paper", **kw) -> Paper:
    defaults = dict(
        arxiv_id=arxiv_id,
        title=title,
        authors=["Alice Kim", "Bob Lee"],
        abstract="We study something interesting.",
        categories=["cond-mat.str-el"],
        published=datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc),
        updated=datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc),
        link=f"http://arxiv.org/abs/{arxiv_id}",
    )
    defaults.update(kw)
    return Paper(**defaults)


@pytest.fixture
def profile() -> Profile:
    return Profile(
        categories=["cond-mat.str-el", "cond-mat.supr-con"],
        keywords=[Keyword(term="kagome", weight=3), Keyword(term="superconductivity", weight=2)],
        authors=["Carol Park"],
        interest="비관례적 초전도와 카고메 격자 물질에 관심.",
    )


class FakeLLM:
    """arxiv_id → 점수 매핑으로 결정적 분석을 돌려주는 스텁. 호출 수를 센다."""

    model = "fake-model"

    def __init__(self, scores: dict[str, int], fail_ids: set[str] | None = None):
        self.scores = scores
        self.fail_ids = fail_ids or set()
        self.calls = 0

    def analyze(self, paper: Paper, profile: Profile) -> Analysis:
        self.calls += 1
        if paper.arxiv_id in self.fail_ids:
            raise AnalysisError("stub failure")
        return Analysis(
            summary=[f"{paper.title} 요약 1", "요약 2", "요약 3"],
            score=self.scores[paper.arxiv_id],
            reason=f"{paper.arxiv_id} 근거",
        )
