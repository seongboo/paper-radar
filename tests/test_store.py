from paper_radar.models import Analysis
from paper_radar.store import Store

from conftest import make_paper


def test_insert_dedupes(tmp_path):
    store = Store(tmp_path / "t.db")
    p = make_paper("2408.00001v1")
    assert store.insert_paper(p, "2026-08-21") is True
    assert store.insert_paper(p, "2026-08-22") is False  # 이미 본 논문
    assert len(store.papers_seen_on("2026-08-21")) == 1
    assert store.papers_seen_on("2026-08-22") == []


def test_paper_roundtrip(tmp_path):
    store = Store(tmp_path / "t.db")
    p = make_paper("2408.00002v1", title="한글 제목 α", authors=["김철수", "L. O'Brien"])
    store.insert_paper(p, "2026-08-21")
    [loaded] = store.papers_seen_on("2026-08-21")
    assert loaded.title == p.title
    assert loaded.authors == p.authors
    assert loaded.updated == p.updated


def test_analysis_cache_roundtrip(tmp_path):
    store = Store(tmp_path / "t.db")
    a = Analysis(summary=["일", "이", "삼"], score=7, reason="근거")
    assert store.get_analysis("2408.00001v1", "hash1") is None
    store.save_analysis("2408.00001v1", "hash1", a, model="m")
    assert store.get_analysis("2408.00001v1", "hash1") == a
    assert store.get_analysis("2408.00001v1", "other-hash") is None  # 프로파일 바뀌면 미스
