from datetime import datetime, timezone
from types import SimpleNamespace

from paper_radar.collect import build_query, paper_from_result


def test_build_query():
    assert (
        build_query(["cond-mat.str-el", "cond-mat.supr-con"])
        == "cat:cond-mat.str-el OR cat:cond-mat.supr-con"
    )


def _stub_result():
    return SimpleNamespace(
        get_short_id=lambda: "2408.12345v1",
        title="A Title\n  Split Across Lines",
        authors=[SimpleNamespace(name="Alice Kim"), SimpleNamespace(name="Bob Lee")],
        summary="Abstract line one.\nLine two.",
        categories=["cond-mat.str-el", "cond-mat.supr-con"],
        entry_id="http://arxiv.org/abs/2408.12345v1",
        published=datetime(2026, 8, 20, 1, 0, tzinfo=timezone.utc),
        updated=datetime(2026, 8, 20, 2, 0, tzinfo=timezone.utc),
    )


def test_paper_from_result_normalizes():
    p = paper_from_result(_stub_result())
    assert p.arxiv_id == "2408.12345v1"
    assert p.title == "A Title Split Across Lines"  # 개행·연속 공백 정리
    assert p.abstract == "Abstract line one. Line two."
    assert p.authors == ["Alice Kim", "Bob Lee"]
    assert p.link.endswith("2408.12345v1")
