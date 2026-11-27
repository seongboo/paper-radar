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


def test_render_adds_reader_and_pdf_links(profile):
    profile.digest.reader_url = "https://example.org/reader/"
    md = render("2026-08-21", [_ranked("2408.12345v1", 9), _ranked("cond-mat/0407123", 2)], profile)
    # 상세 항목: 리더 링크(arXiv 번호를 쿼리로) + PDF 링크
    assert (
        "- 열기: [리더로 열기](https://example.org/reader/?arxiv=2408.12345v1)"
        " · [PDF](https://arxiv.org/pdf/2408.12345v1)"
    ) in md
    # 그 외 한 줄 항목에도 붙고, 옛 형식 번호의 '/' 는 쿼리에서 인코딩된다
    assert "?arxiv=cond-mat%2F0407123) · [PDF](https://arxiv.org/pdf/cond-mat/0407123)" in md


def test_render_pdf_link_only_when_reader_disabled(profile):
    profile.digest.reader_url = None
    md = render("2026-08-21", [_ranked("2408.12345v1", 9)], profile)
    assert "- 열기: [PDF](https://arxiv.org/pdf/2408.12345v1)" in md
    assert "리더로 열기" not in md


def test_reader_url_with_existing_query(profile):
    profile.digest.reader_url = "https://example.org/reader/?lang=ko"
    md = render("2026-08-21", [_ranked("2408.12345v1", 9)], profile)
    assert "(https://example.org/reader/?lang=ko&arxiv=2408.12345v1)" in md
