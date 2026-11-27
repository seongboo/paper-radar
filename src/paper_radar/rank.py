"""랭킹: LLM 점수 위에 결정적 부스트(저자·키워드 매치)를 합산해 정렬."""

from __future__ import annotations

from .models import Analysis, Paper, Profile, RankedPaper

AUTHOR_BOOST = 3
KEYWORD_BOOST_CAP = 4


def compute_boost(paper: Paper, profile: Profile) -> int:
    text = f"{paper.title}\n{paper.abstract}".lower()
    keyword_boost = min(
        sum(k.weight for k in profile.keywords if k.term.lower() in text),
        KEYWORD_BOOST_CAP,
    )
    author_hit = any(
        wanted.lower() in author.lower()
        for wanted in profile.authors
        for author in paper.authors
    )
    return keyword_boost + (AUTHOR_BOOST if author_hit else 0)


def rank(pairs: list[tuple[Paper, Analysis]], profile: Profile) -> list[RankedPaper]:
    ranked = [
        RankedPaper(paper=p, analysis=a, boost=compute_boost(p, profile))
        for p, a in pairs
    ]
    ranked.sort(key=lambda r: (r.final_score, r.paper.updated), reverse=True)
    return ranked
