# paper-radar — 논문 레이더

> 상태: **구현 (MVP)** · 2026-07-13 신규 아이디어 · 2026-08-20 MVP 파이프라인 구현 · Obsidian: `0. Inbox/논문 레이더 (paper-radar).md`

## 개념
arXiv(cond-mat 등)·저널의 **신규 논문을 키워드/저자로 자동 수집** → LLM 요약 + 내 관심사 **관련도 랭킹** → 데일리 다이제스트. 연구 서베이 시간을 줄인다.

## 현재 구현 상태 (2026-08)
- **MVP 파이프라인 구현 완료** (수집→분석→랭킹→다이제스트, [DESIGN.md](DESIGN.md)의 M0~M3) — 단위·E2E 테스트 포함
- 남은 것: 프로파일에 본인 관심사 채우기, 실환경 첫 실행, M4 확장(스케줄링·Obsidian·메일)

## 사용법
```bash
uv sync
cp profile.example.yaml profile.yaml   # 카테고리·키워드·관심사 서술 채우기
export ANTHROPIC_API_KEY=...           # 또는 profile 에서 llm.provider: ollama
uv run paper-radar run                 # 수집→분석→다이제스트 (digests/YYYY-MM-DD.md)
```
`collect`(수집만), `digest --date`(재생성) 하위 명령도 있다. 매일 10:30 KST cron 권장 (arXiv 발표: 한국시간 화~토 오전).

## 핵심 기능 (MVP → 확장)
- arXiv API 폴링(카테고리/키워드/저자) → 신규 항목 수집
- LLM 3줄 요약 + 관심 프로파일 대비 관련도 점수·정렬
- 데일리 마크다운/메일 다이제스트, (확장) Obsidian 자동 저장

## 기술 스택
- Python 3.11+ · uv · SQLite · arXiv API(`arxiv`) · LLM: Claude API(`anthropic`, 기본) / Ollama(로컬)

## 다음 단계
- [x] 관심 키워드·카테고리 프로파일 정의 — 스키마·예시 완료(`profile.example.yaml`), 본인 값 채우기만 남음
- [ ] 수집→요약→랭킹 1일치 다이제스트 생성 (실환경 첫 실행)
- [ ] M4 확장: cron/GitHub Actions 스케줄링, Obsidian 자동 저장, 메일 발송 ([DESIGN.md](DESIGN.md) 참고)

## 관련
- 24 seongboo2, 16 AARLA, 34 inbox-triage
