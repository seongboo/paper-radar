"""스텁 arXiv/LLM 으로 파이프라인 전체(E2E)를 검증한다 — 네트워크·API 키 불필요."""

from paper_radar import pipeline
from paper_radar.store import Store

from conftest import FakeLLM, make_paper


def test_collect_new_dedupes_across_runs(tmp_path):
    store = Store(tmp_path / "t.db")
    papers = [make_paper("1"), make_paper("2")]
    assert len(pipeline.collect_new(store, papers, "2026-08-21")) == 2
    # 다음 실행: 겹치는 1편 + 새 1편
    new = pipeline.collect_new(store, [make_paper("2"), make_paper("3")], "2026-08-22")
    assert [p.arxiv_id for p in new] == ["3"]


def test_analyze_uses_cache_on_rerun(tmp_path, profile):
    store = Store(tmp_path / "t.db")
    papers = [make_paper("1"), make_paper("2")]
    llm = FakeLLM(scores={"1": 5, "2": 7})

    pairs = pipeline.analyze_papers(store, profile, llm, papers)
    assert len(pairs) == 2 and llm.calls == 2

    pipeline.analyze_papers(store, profile, llm, papers)
    assert llm.calls == 2  # 전부 캐시 히트

    profile.interest = "완전히 다른 관심사"  # 프로파일 변경 → 재분석
    pipeline.analyze_papers(store, profile, llm, papers)
    assert llm.calls == 4


def test_failed_analysis_skips_paper_only(tmp_path, profile):
    store = Store(tmp_path / "t.db")
    papers = [make_paper("1"), make_paper("2")]
    llm = FakeLLM(scores={"2": 7}, fail_ids={"1"})
    pairs = pipeline.analyze_papers(store, profile, llm, papers)
    assert [p.arxiv_id for p, _ in pairs] == ["2"]


def test_digest_sends_email_when_configured(tmp_path, profile, monkeypatch):
    from paper_radar import mailer
    from paper_radar.models import EmailConfig

    profile.digest.output_dir = str(tmp_path / "digests")
    profile.digest.email = EmailConfig(to=["a@example.com"], smtp_host="h")
    sent = []
    monkeypatch.setattr(mailer, "send_digest", lambda cfg, date, body: sent.append((date, body)))

    store = Store(tmp_path / "t.db")
    llm = FakeLLM(scores={"1": 5})
    path = pipeline.make_digest(store, profile, llm, "2026-08-21", [make_paper("1")])
    assert sent and sent[0][0] == "2026-08-21"
    assert "논문 레이더" in sent[0][1]

    # 발송 실패는 실행을 깨지 않는다 (파일은 이미 생성됨)
    monkeypatch.setattr(
        mailer, "send_digest", lambda *a: (_ for _ in ()).throw(OSError("smtp down"))
    )
    path = pipeline.make_digest(store, profile, llm, "2026-08-21", [make_paper("1")])
    assert path.exists()


def test_end_to_end_digest(tmp_path, profile):
    profile.digest.output_dir = str(tmp_path / "digests")
    store = Store(tmp_path / "t.db")
    papers = [
        make_paper("1", title="Kagome superconductivity breakthrough"),  # 부스트 대상
        make_paper("2", title="Boring unrelated paper"),
        make_paper("3", title="Mildly relevant"),
    ]
    llm = FakeLLM(scores={"1": 6, "2": 2, "3": 9})

    new = pipeline.collect_new(store, papers, "2026-08-21")
    path = pipeline.make_digest(store, profile, llm, "2026-08-21", new)

    md = path.read_text(encoding="utf-8")
    # 1번: LLM 6 + 부스트 4(kagome 3 + superconductivity 2 → cap 4) = 10 → 1위
    assert md.index("Kagome superconductivity") < md.index("Mildly relevant")
    assert "## 그 외" in md and "Boring unrelated paper" in md
    assert path.name == "2026-08-21.md"
