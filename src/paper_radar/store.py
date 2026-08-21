"""SQLite 상태 저장: 수집 논문(중복 제거)과 분석 캐시."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import Analysis, Paper

_SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    arxiv_id   TEXT PRIMARY KEY,
    title      TEXT NOT NULL,
    authors    TEXT NOT NULL,      -- JSON 배열
    abstract   TEXT NOT NULL,
    categories TEXT NOT NULL,      -- JSON 배열
    published  TEXT NOT NULL,      -- ISO8601
    updated    TEXT NOT NULL,
    link       TEXT NOT NULL,
    first_seen TEXT NOT NULL,      -- ISO8601 UTC
    seen_date  TEXT NOT NULL       -- YYYY-MM-DD (로컬 기준, 다이제스트 날짜 매칭용)
);
CREATE INDEX IF NOT EXISTS idx_papers_seen_date ON papers (seen_date);

CREATE TABLE IF NOT EXISTS analyses (
    arxiv_id     TEXT NOT NULL,
    profile_hash TEXT NOT NULL,
    summary      TEXT NOT NULL,    -- JSON 배열 (3줄)
    llm_score    INTEGER NOT NULL,
    reason       TEXT NOT NULL,
    model        TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    PRIMARY KEY (arxiv_id, profile_hash)
);

CREATE TABLE IF NOT EXISTS runs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    new_papers INTEGER NOT NULL
);
"""


class Store:
    def __init__(self, path: str | Path = "radar.db"):
        self._conn = sqlite3.connect(str(path))
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # --- papers ---

    def insert_paper(self, paper: Paper, seen_date: str) -> bool:
        """처음 보는 논문이면 저장하고 True, 이미 있으면 False."""
        cur = self._conn.execute(
            "INSERT OR IGNORE INTO papers VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                paper.arxiv_id,
                paper.title,
                json.dumps(paper.authors, ensure_ascii=False),
                paper.abstract,
                json.dumps(paper.categories, ensure_ascii=False),
                paper.published.isoformat(),
                paper.updated.isoformat(),
                paper.link,
                datetime.now(timezone.utc).isoformat(),
                seen_date,
            ),
        )
        self._conn.commit()
        return cur.rowcount == 1

    def papers_seen_on(self, seen_date: str) -> list[Paper]:
        rows = self._conn.execute(
            "SELECT arxiv_id, title, authors, abstract, categories, published, updated, link"
            " FROM papers WHERE seen_date = ? ORDER BY updated DESC",
            (seen_date,),
        ).fetchall()
        return [
            Paper(
                arxiv_id=r[0],
                title=r[1],
                authors=json.loads(r[2]),
                abstract=r[3],
                categories=json.loads(r[4]),
                published=r[5],
                updated=r[6],
                link=r[7],
            )
            for r in rows
        ]

    # --- analyses (캐시) ---

    def get_analysis(self, arxiv_id: str, profile_hash: str) -> Analysis | None:
        row = self._conn.execute(
            "SELECT summary, llm_score, reason FROM analyses"
            " WHERE arxiv_id = ? AND profile_hash = ?",
            (arxiv_id, profile_hash),
        ).fetchone()
        if row is None:
            return None
        return Analysis(summary=json.loads(row[0]), score=row[1], reason=row[2])

    def save_analysis(
        self, arxiv_id: str, profile_hash: str, analysis: Analysis, model: str
    ) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO analyses VALUES (?,?,?,?,?,?,?)",
            (
                arxiv_id,
                profile_hash,
                json.dumps(analysis.summary, ensure_ascii=False),
                analysis.score,
                analysis.reason,
                model,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._conn.commit()

    # --- runs ---

    def record_run(self, new_papers: int) -> None:
        self._conn.execute(
            "INSERT INTO runs (started_at, new_papers) VALUES (?, ?)",
            (datetime.now(timezone.utc).isoformat(), new_papers),
        )
        self._conn.commit()
