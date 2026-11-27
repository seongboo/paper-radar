"""CLI: paper-radar run | collect | digest"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date

from .config import load_profile
from .store import Store


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="paper-radar",
        description="arXiv 신규 논문 수집·요약·랭킹 데일리 다이제스트",
    )
    parser.add_argument("--profile", default="profile.yaml", help="프로파일 경로")
    parser.add_argument("--db", default="radar.db", help="SQLite 경로")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("run", help="수집→분석→다이제스트 전체 실행")
    sub.add_parser("collect", help="arXiv 수집만 (LLM 호출 없음)")
    p_digest = sub.add_parser("digest", help="이미 수집된 날짜의 다이제스트 (재)생성")
    p_digest.add_argument("--date", default=date.today().isoformat(), help="YYYY-MM-DD")

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    try:
        profile = load_profile(args.profile)
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 1

    store = Store(args.db)
    today = date.today().isoformat()

    # LLM/arXiv 클라이언트는 실제 쓰는 명령에서만 만든다 (collect 는 API 키 불필요)
    from . import pipeline

    if args.cmd == "collect":
        from .collect import fetch_recent

        new = pipeline.collect_new(store, fetch_recent(profile), today)
        print(f"신규 {len(new)}편 수집 (오늘 누적: {len(store.papers_seen_on(today))}편)")
        return 0

    from .collect import fetch_recent
    from .llm import make_client

    llm = make_client(profile.llm)

    if args.cmd == "run":
        new = pipeline.collect_new(store, fetch_recent(profile), today)
        print(f"신규 {len(new)}편 수집")
        papers = store.papers_seen_on(today)
        path = pipeline.make_digest(store, profile, llm, today, papers)
        print(f"완료: {path}")
        return 0

    if args.cmd == "digest":
        papers = store.papers_seen_on(args.date)
        if not papers:
            print(f"{args.date} 에 수집된 논문이 없습니다. 먼저 collect/run 을 실행하세요.")
            return 1
        path = pipeline.make_digest(store, profile, llm, args.date, papers)
        print(f"완료: {path}")
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
