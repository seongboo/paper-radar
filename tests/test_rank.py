from paper_radar.models import Analysis, Keyword, Profile
from paper_radar.rank import AUTHOR_BOOST, KEYWORD_BOOST_CAP, compute_boost, rank

from conftest import make_paper


def _analysis(score: int) -> Analysis:
    return Analysis(summary=["a", "b", "c"], score=score, reason="r")


def test_keyword_boost_case_insensitive(profile):
    p = make_paper("1", title="Kagome lattice study", abstract="No other terms.")
    assert compute_boost(p, profile) == 3


def test_keyword_boost_capped(profile):
    profile.keywords.append(Keyword(term="lattice", weight=4))
    p = make_paper("1", title="Kagome lattice superconductivity")
    # 3 + 2 + 4 = 9 → 상한 4
    assert compute_boost(p, profile) == KEYWORD_BOOST_CAP


def test_author_boost_partial_match(profile):
    p = make_paper("1", authors=["Carol Park", "X. Y."], abstract="nothing")
    assert compute_boost(p, profile) == AUTHOR_BOOST


def test_no_boost_without_profile_lists():
    profile = Profile(categories=["cs.AI"], interest="AI")
    p = make_paper("1", title="Kagome by Carol Park")
    assert compute_boost(p, profile) == 0


def test_rank_orders_by_final_score(profile):
    low_llm_high_boost = make_paper("1", title="kagome superconductivity", abstract="x")
    high_llm = make_paper("2", title="unrelated", abstract="y")
    ranked = rank(
        [(low_llm_high_boost, _analysis(4)), (high_llm, _analysis(6))], profile
    )
    # 4 + (3+2 → cap 4) = 8 > 6
    assert [r.paper.arxiv_id for r in ranked] == ["1", "2"]
    assert ranked[0].final_score == 8
