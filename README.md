# paper-radar — 논문 리더 + 논문 레이더

논문을 **읽는** 도구와 **찾는** 도구를 한 저장소에 모았다.

| 도구 | 하는 일 | 위치 | 버전 |
|---|---|---|---|
| [논문 리더](#1-논문-리더-읽기) | PDF를 열고 옆에서 AI에게 묻는 웹 페이지 | `gh-pages` 브랜치 → https://seongboo.github.io/paper-radar/ | 0.1.0 |
| [논문 레이더](#2-논문-레이더-찾기) | arXiv 신규 논문을 수집·요약·랭킹해 다이제스트로 정리 | `main` 브랜치 (Python) | 0.1.0 |

현재 버전: **0.1.0** (2026-11-27)

---

## 1. 논문 리더 (읽기)

설치 없이 브라우저에서 여는 논문 읽기 도구. 왼쪽에 PDF, 오른쪽에 AI 패널이 있다.

### 두 가지 버전

| | Claude 버전 | API 키 버전 |
|---|---|---|
| 대상 | Claude 구독자 | 그 외 모든 사람 |
| AI 연결 | Claude 구독으로 동작. 키 불필요 | 각자의 API 키 (OpenAI, Google Gemini, Anthropic 중 하나) |
| 추가 비용 | 없음 (구독 사용량에서 차감) | API는 쓴 만큼 과금. ChatGPT·Gemini 구독과는 별개 |
| 여는 곳 | claude.ai 안의 개인 페이지 (비공개) | https://seongboo.github.io/paper-radar/ |
| 메모 저장 | 계정 | 그 브라우저에만 |
| arXiv 번호로 바로 열기 | 불가 (PDF를 내려받아 끌어다 놓기) | 가능 |

화면은 거의 같다. 오른쪽 위에 "AI 설정" 버튼이 있으면 API 키 버전이다.

### 기능

- **글자 선택** → 설명, 번역, 유도(중간 단계와 가정·근사를 따로 표시), 참고문헌 조회
- **영역 캡처** → 그림, 표, 글자가 깨지는 수식을 이미지로 잡아서 질문
- **대화** → 논문 전체를 맥락으로 질문. 답변의 `p.3` 표시를 누르면 그 쪽으로 이동
- **요약 · 핵심 문장 표시** → 방법, 결과, 기여, 가정과 근사를 정리하고 본문에 색으로 표시
- **스캔본 글자 인식** → 글자 정보가 없는 옛날 논문을 AI가 쪽 단위로 읽음
- **메모** → 답변을 논문별로 저장하고 Markdown으로 복사 (Obsidian 등에 붙여넣기)
- **추천 질문 · 내 질문** → 자주 쓰는 질문을 저장해 두고 한 번에 전송
- **답변 언어** → 한국어 / English 전환

### API 키 버전 쓰는 법

1. https://seongboo.github.io/paper-radar/ 를 연다.
2. 오른쪽 위 **AI 설정** → AI 회사를 고르고 API 키를 붙여 넣는다.
3. **모델 목록 불러오기**로 모델을 고른다. 캡처와 글자 인식에는 이미지 입력을 지원하는 모델이 필요하다.
4. **연결 확인**을 누른 뒤 저장한다.
5. PDF를 끌어다 놓거나, 위쪽 칸에 arXiv 번호(예: `2408.12345`)를 넣고 **arXiv 열기**를 누른다.

주소 뒤에 `?arxiv=2408.12345`를 붙여도 그 논문이 바로 열린다.

### 개인정보

- PDF는 브라우저 안에서만 열린다.
- AI에 물을 때 해당 내용이 고른 AI 회사로 직접 전송된다. 중간 서버는 없다.
- API 키, 메모, 글자 인식 결과는 그 브라우저에만 저장된다. 공용 컴퓨터에서는 키 저장을 끈다.

### 확인된 것과 아닌 것

- 확인: PDF 열기, arXiv 번호로 열기(실제 사이트에서), 각 기능의 화면 동작, 세 회사 요청 형식(모의 서버).
- 미확인: **실제 API 키를 사용한 호출**. 문제가 있으면 Issues에 남긴다.

### 한계

- 핵심 문장 표시는 문장이 아니라 줄 단위로 칠해진다.
- 2단 편집이나 저자-연도 방식 인용은 참고문헌 목록 분리가 실패할 수 있다 (그때는 AI가 대신 찾는다).
- 아주 긴 논문은 앞부분만 AI에 전달되고, 화면 위에 안내가 뜬다.
- 스캔본은 글자 인식 후에도 본문 위 글자 선택이 안 된다. 특정 수식은 영역 캡처로 묻는다.

---

## 2. 논문 레이더 (찾기)

arXiv의 신규 논문을 카테고리로 수집 → 논문마다 LLM이 3줄 요약과 관련도 점수 → 키워드·저자 가산점을 더해 정렬 → 하루치 Markdown 다이제스트. 연구 서베이 시간을 줄이는 것이 목적이다.

### 상태

- 수집 → 분석 → 랭킹 → 다이제스트 파이프라인. 단위·E2E 테스트 포함.
- 2026-11-27 실환경 첫 실행 확인: 로컬 모델로 48편을 약 8분에 처리.
- 다이제스트의 각 논문에 **리더로 열기**(논문 리더 API 키 버전에서 바로 열림)와 **PDF** 링크가 붙는다.

### 처음 실행하기 (로컬 모델 Ollama, 무료)

API 키와 비용 없이 내 컴퓨터의 모델로 돌리는 순서다. 터미널에 한 단계씩 붙여 넣는다. (macOS에서 확인함)

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

**4. 설정 파일 만들기** — 예시를 복사한 뒤 `profile.yaml`을 열어 `categories`, `keywords`, `interest`를 본인 분야로 바꾸고, `llm` 블록을 아래처럼 고친다. (`effort`, `fallback`은 Claude 전용이라 지워도 된다.) `profile.yaml`은 개인 설정이라 저장소에 올라가지 않는다.
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

**6. 전체 실행** — 논문마다 모델을 한 번씩 호출하므로 시간은 편수에 비례한다. 끝나면 `digests/날짜.md`가 생긴다.
```bash
uv run paper-radar run && head -60 digests/$(date +%F).md
```

### 실행 참고 (실측, 2026-11-27)

- 환경: Apple Silicon 맥북 프로, `gemma3:12b`, `cond-mat.mtrl-sci`.
- 속도: 48편에 약 8분 (편당 약 10초). 실패 없음.
- 요약: 한국어로 정상 생성. 초록 내용을 충실히 옮김.
- 점수: 로컬 모델의 관련도 점수가 5~8점대에 몰려 변별이 약했고, 근거 설명이 억지스러운 경우가 있었다. 그 결과 순위가 키워드 가산점에 크게 좌우됐다. (상위 7편만 보고 내린 평가)
- 조정 방법: `keywords`의 가중치를 낮추고 `digest.min_score`를 올린다. 편수가 많으면 `categories`를 줄이거나 더 작은 모델을 쓴다.

### 그 밖의 실행 방법

**Claude API로 실행** (유료, 기본 설정) — `profile.yaml`의 `llm.provider`를 `claude`로 두고 키를 환경변수로 준다.
```bash
export ANTHROPIC_API_KEY=...
uv run paper-radar run
```

**하위 명령** — `collect`(수집만), `digest --date YYYY-MM-DD`(다이제스트 재생성).

**매일 자동 실행 (cron)** — arXiv 발표(한국시간 화~토 오전 9~10시) 직후인 10:30 KST 권장. Claude API를 쓰면 명령 앞에 `ANTHROPIC_API_KEY=...`를 붙인다.
```cron
30 10 * * * cd $HOME/paper-radar && uv run paper-radar run >> radar.log 2>&1
```

**메일 발송** — profile의 `digest.email` 블록을 설정하고 `SMTP_PASSWORD` 환경변수를 주면 다이제스트가 메일로도 온다 (Gmail은 앱 비밀번호 사용).

**Obsidian 저장** — `digest.obsidian_path`를 설정하면 다이제스트를 그 폴더에도 복사한다.

**열기 링크** — "리더로 열기"의 대상 주소는 `digest.reader_url`로 바꾸거나 `null`로 끌 수 있다(끄면 PDF 링크만). Claude 버전 논문 리더를 쓰는 경우에는 "PDF"로 내려받아 끌어다 놓는다.

---

## 저장소 구조

| 브랜치 | 내용 | 수정하면 |
|---|---|---|
| `main` | 논문 레이더 (Python 패키지, 테스트, 문서) | 저장소 첫 화면과 코드가 바뀜 |
| `gh-pages` | 논문 리더 API 키 버전 (정적 웹 파일) | 1~2분 뒤 사이트가 바뀜 |

두 브랜치는 공유하는 파일이 없다. 서로 합치지 않는다.

## 기술 스택

- 논문 리더: HTML/JavaScript 단일 페이지 · PDF.js · KaTeX · marked · DOMPurify · GitHub Pages
- 논문 레이더: Python 3.11+ · uv · SQLite · arXiv API(`arxiv`) · LLM: Claude API(`anthropic`) / Ollama(로컬)

## 문서

- [DESIGN.md](DESIGN.md) — 논문 레이더 설계
- [CLAUDE.md](CLAUDE.md) — AI 도우미가 이 저장소에서 작업할 때의 안내
- `gh-pages` 브랜치의 README — 논문 리더 API 키 버전 안내
