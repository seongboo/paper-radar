"""다이제스트 렌더: 랭킹된 논문을 Markdown 파일로."""

from __future__ import annotations

import shutil
from pathlib import Path

from .models import Profile, RankedPaper

# arXiv 신규 발표는 일~목 20:00 ET → 한국시간 화~토 오전. 일·월 아침엔 신규 없음.
_NO_PAPERS = "신규 논문이 없습니다. (arXiv 발표 일정: 한국시간 화~토 오전 9~10시)"


def _authors_line(authors: list[str], limit: int = 3) -> str:
    shown = ", ".join(authors[:limit])
    rest = len(authors) - limit
    return f"{shown} 외 {rest}명" if rest > 0 else shown


def render(date: str, ranked: list[RankedPaper], profile: Profile) -> str:
    cfg = profile.digest
    detailed = [r for r in ranked if r.final_score >= cfg.min_score][: cfg.top_n]
    detailed_ids = {r.paper.arxiv_id for r in detailed}
    rest = [r for r in ranked if r.paper.arxiv_id not in detailed_ids]

    lines = [f"# 논문 레이더 — {date}", ""]
    if not ranked:
        lines += [_NO_PAPERS, ""]
        return "\n".join(lines)

    lines += [
        f"수집 {len(ranked)}편 · 상세 {len(detailed)}편 (점수 ≥ {cfg.min_score}, 상위 {cfg.top_n})",
        "",
    ]

    for i, r in enumerate(detailed, start=1):
        p, a = r.paper, r.analysis
        boost_note = f" (LLM {a.score} + 부스트 {r.boost})" if r.boost else ""
        lines += [
            f"## {i}. [{p.title}]({p.link}) — {r.final_score}점{boost_note}",
            f"- 저자: {_authors_line(p.authors)} · {', '.join(p.categories[:3])}"
            f" · {p.updated.date().isoformat()}",
            f"- 근거: {a.reason}",
            "- 요약:",
            *[f"  - {line}" for line in a.summary],
            "",
        ]

    if rest:
        lines += ["## 그 외", ""]
        lines += [
            f"- [{r.paper.title}]({r.paper.link}) — {r.final_score}점" for r in rest
        ]
        lines += [""]

    return "\n".join(lines)


def write_digest(date: str, ranked: list[RankedPaper], profile: Profile) -> Path:
    out_dir = Path(profile.digest.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{date}.md"
    path.write_text(render(date, ranked, profile), encoding="utf-8")

    if profile.digest.obsidian_path:
        obsidian_dir = Path(profile.digest.obsidian_path)
        obsidian_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, obsidian_dir / path.name)

    return path
