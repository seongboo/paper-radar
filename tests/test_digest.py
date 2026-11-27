from paper_radar.digest import render, write_digest
from paper_radar.models import Analysis, RankedPaper

from conftest import make_paper


def _ranked(arxiv_id: str, score: int, boost: int = 0) -> RankedPaper:
    return RankedPaper(
        paper=make_paper(arxiv_id, title=f"Paper {arxiv_id}"),
        analysis=Analysis(summary=["줄1", "줄2", "줄3"], score=score, reason="근거"),
        boost=boost,
    )


def test_render_splits_detailed_and_rest(profile):
    ranked = [_ranked("1", 9), _ranked("2", 5), _ranked("3", 2)]
    md = render("2026-08-21", ranked, profile)  # min_score=4
    assert "# 논문 레이더 — 2026-08-21" in md
    assert "## 1. [Paper 1]" in md
    assert "## 2. [Paper 2]" in md
    assert "## 그 외" in md
    assert "- [Paper 3](http://arxiv.org/abs/3) — 2점" in md
    assert "줄1" in md and "근거" in md


def test_render_shows_boost_breakdown(profile):
    md = render("2026-08-21", [_ranked("1", 5, boost=3)], profile)
    assert "8점 (LLM 5 + 부스트 3)" in md


def test_render_empty(profile):
    md = render("2026-08-21", [], profile)
    assert "신규 논문이 없습니다" in md


def test_top_n_limit(profile):
    profile.digest.top_n = 1
    ranked = [_ranked("1", 9), _ranked("2", 8)]
    md = render("2026-08-21", ranked, profile)
    assert "## 1. [Paper 1]" in md
    assert "## 2." not in md
    assert "- [Paper 2]" in md  # 그 외로 밀림


def test_write_digest_and_obsidian_copy(tmp_path, profile):
    profile.digest.output_dir = str(tmp_path / "digests")
    profile.digest.obsidian_path = str(tmp_path / "vault")
    path = write_digest("2026-08-21", [_ranked("1", 9)], profile)
    assert path.read_text(encoding="utf-8").startswith("# 논문 레이더")
    assert (tmp_path / "vault" / "2026-08-21.md").exists()
