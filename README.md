# paper-radar — 논문 레이더

> 상태: **구현 (MVP)** · 2026-07-13 신규 아이디어 · 2026-08-20 MVP 파이프라인 구현

이 저장소에는 도구가 두 개 있습니다. **논문 레이더**는 읽을 논문을 찾고(이 문서의 대부분), **논문 리더**는 찾은 논문을 읽습니다([아래](#함께-들어-있는-것-논문-리더-api-키-버전) 참고).

## 개념
arXiv(cond-mat 등)·저널의 **신규 논문을 키워드/저자로 자동 수집** → LLM 요약 + 내 관심사 **관련도 랭킹** → 데일리 다이제스트. 연구 서베이 시간을 줄인다.

## 현재 구현 상태 (2026-08)
- **MVP 파이프라인 구현 완료** (수집→분석→랭킹→다이제스트, [DESIGN.md](DESIGN.md)의 M0~M3) — 단위·E2E 테스트 포함
- 남은 것: 프로파일에 본인 관심사 채우기, 실환경 첫 실행, M4 확장(스케줄링·Obsidian·메일)

## 사용법
```bash
uv sync
cp profile.example.yaml profile.yaml   # 카테고리·키워드·관심사 서술 채우기
export ANTHROPIC_API_KEY=...           # 또는 profile 에서 llm.provider: ollama (아래 "처음 실행하기" 참고)
uv run paper-radar run                 # 수집→분석→다이제스트 (digests/YYYY-MM-DD.md)
```
`collect`(수집만), `digest --date`(재생성) 하위 명령도 있다.

**매일 자동 실행 (cron):** arXiv 발표(한국시간 화~토 오전 9~10시) 직후인 10:30 KST 권장.
```cron
30 10 * * * cd $HOME/paper-radar && ANTHROPIC_API_KEY=... uv run paper-radar run >> radar.log 2>&1
```

**메일 발송:** profile의 `digest.email` 블록을 설정하고 `SMTP_PASSWORD` 환경변수를 주면 다이제스트가 메일로도 온다 (Gmail은 앱 비밀번호 사용). Obsidian 저장은 `digest.obsidian_path` 설정.

**논문 바로 열기:** 다이제스트의 각 논문에 "리더로 열기"와 "PDF" 링크가 붙는다. "리더로 열기"는 논문 리더(API 키 버전)에서 그 논문을 바로 연다. 대상 주소는 `digest.reader_url`로 바꾸거나 `null`로 끌 수 있다. Claude 버전 논문 리더를 쓰는 경우에는 "PDF"로 내려받아 끌어다 놓는다.

## 처음 실행하기 (로컬 모델 Ollama, 무료)

API 키와 비용 없이 내 컴퓨터의 모델로 돌리는 순서다. 터미널에 한 단계씩 붙여 넣는다. (macOS 기준으로 확인함)

**1. 준비물 확인** — 셋 다 버전이 나오면 된다. Ollama는 "could not connect" 경고가 나와도 설치는 된 것이다.
```bash
uv --version; ollama --version; git --version
```

**2. Ollama 켜고 모델 확인** — 목록에 쓸 모델이 없으면 `ollama pull gemma3:12b`로 받는다 (약 8 GB).
```bash
open -a Ollama 2>/dev/null || brew services start ollama; sleep 5; ollama list
```

**3. 코드 받기, 설치, 테스트** — 마지막 줄에 `passed`가 나오면 설치가 된 것이다. 패키지는 이 폴더 안에만 설치된다.
```bash
git clone https://github.com/seongboo/paper-radar.git && cd paper-radar && uv sync && uv run pytest -q
```

**4. 설정 파일 만들기** — 예시를 복사한 뒤 `profile.yaml`을 열어 `categories`, `keywords`, `interest`를 본인 분야로 바꾸고, `llm` 블록을 아래처럼 고친다. (`effort`, `fallback`은 Claude 전용이라 지워도 된다.)
```bash
cp profile.example.yaml profile.yaml
```
```yaml
llm:
  provider: ollama
  model: gemma3:12b      # ollama list 에 나온 이름 그대로
  language: ko
```

**5. 수집만 먼저** — AI를 쓰지 않아 금방 끝난다. 마지막 줄의 "신규 N편"으로 분량을 확인한다. arXiv가 처음 한두 번 응답하지 않아 `try: 1`, `try: 2`가 보여도 자동으로 다시 시도하므로 기다리면 된다.
```bash
uv run paper-radar collect
```

**6. 전체 실행** — 논문마다 로컬 모델을 한 번씩 호출하므로 시간은 편수에 비례한다. 진행 표시가 거의 없어도 멈춘 것이 아니다. 끝나면 `digests/날짜.md`가 생긴다.
```bash
uv run paper-radar run && head -60 digests/$(date +%F).md
```

편수가 너무 많으면 `categories`를 줄이거나 더 작은 모델(`gemma3:4b` 등)로 바꾼다. 요약 품질은 모델에 따라 달라진다.

## 핵심 기능 (MVP → 확장)
- arXiv API 폴링(카테고리/키워드/저자) → 신규 항목 수집
- LLM 3줄 요약 + 관심 프로파일 대비 관련도 점수·정렬
- 데일리 마크다운/메일 다이제스트, (확장) Obsidian 자동 저장

## 기술 스택
- Python 3.11+ · uv · SQLite · arXiv API(`arxiv`) · LLM: Claude API(`anthropic`, 기본) / Ollama(로컬)

## 다음 단계
- [x] 관심 키워드·카테고리 프로파일 정의 (`profile.example.yaml` — 위상 초전도체·마요라나)
- [ ] 수집→요약→랭킹 1일치 다이제스트 생성 (실환경 첫 실행)
- [x] M4 일부: Obsidian 자동 저장, 메일 발송, cron 가이드
- [ ] M4 나머지: cron 실제 등록, Batches 전환(비용 50%↓), 저널 소스 ([DESIGN.md](DESIGN.md) 참고)

---

## 함께 들어 있는 것: 논문 리더 (API 키 버전)

찾은 논문을 **읽는** 도구입니다. 설치 없이 브라우저에서 엽니다.

- 주소: https://seongboo.github.io/paper-radar/
- arXiv 논문 바로 열기: 위쪽 칸에 arXiv 번호를 넣거나, 주소 뒤에 `?arxiv=2408.12345`를 붙인다 (논문 레이더 다이제스트의 "리더로 열기"가 이 방식)
- 파일 위치: 이 저장소의 `gh-pages` 브랜치

**기능**
- 본문 선택 → 설명, 번역, 유도(중간 단계와 가정·근사 표시), 참고문헌 조회
- 영역 캡처 → 그림, 표, 수식을 이미지로 질문
- 논문 전체를 맥락으로 대화, 요약, 핵심 문장 표시
- 스캔본 글자 인식, 메모 저장과 Markdown 복사

**사용 전 준비**
- 각자의 API 키(OpenAI, Google Gemini, Anthropic 중 하나)가 필요합니다. ChatGPT나 Gemini 구독과는 별개이며 쓴 만큼 과금됩니다.
- 오른쪽 위 "AI 설정"에서 회사와 키를 넣고, 모델 목록을 불러와 고른 뒤 연결을 확인합니다.
- PDF는 브라우저 안에서만 열리고, 키와 메모는 그 브라우저에만 저장됩니다.
