# Post Watch AI

인벤 메이플스토리 자유게시판 등 지정 사이트의 **신규 게시글**을 실시간 감지,  
**AI 요약** 및 **디스코드 Webhook**으로 전송하는 자동화 파이프라인입니다.  
(댓글 추천 Top 3 포함, 배치/즉시 실행, 중복 방지)

---

## 주요 기능

- 지정 커뮤니티(인벤 등) **신규 게시글 실시간 감지**
- **OpenAI GPT-4o** 기반 게시글 본문 요약
- **댓글 추천 Top 3** 자동 추출 및 메시지 포함 (Selenium 기반)
- **디스코드 Webhook**으로 자동 알림 전송
- **중복 게시글 방지** (SQLite DB)
- **30초마다 배치 실행** + **실행 직후 1회 즉시 실행**
- 모든 주요 기능에 **단위 테스트** 포함

---

## 설치 및 준비

### 1. Python 및 패키지 설치

- Python 3.8 이상 필요

```bash
pip install -r requirements.txt
pip install selenium
```

### 2. ChromeDriver 설치

- [ChromeDriver 다운로드](https://chromedriver.chromium.org/downloads) (본인 크롬 버전에 맞게)
- chromedriver.exe를 프로젝트 폴더 또는 PATH에 위치

---

## 설정

`config/config.json` 파일을 아래와 같이 작성:

```json
{
  "target_url": "https://www.inven.co.kr/board/maple/5974",
  "crawl_interval_seconds": 30,
  "db_path": "posts.db",
  "openai_api_key": "YOUR_OPENAI_API_KEY",
  "discord_webhook_url": "YOUR_DISCORD_WEBHOOK_URL"
}
```

- `target_url`: 크롤링할 게시판 목록 페이지
- `crawl_interval_seconds`: 크롤링 주기(초) (권장: 30)
- `db_path`: SQLite DB 파일 경로
- `openai_api_key`: OpenAI API 키
- `discord_webhook_url`: 디스코드 Webhook URL

---

## 실행 방법

```bash
python run_test.py
```

- **실행 직후 1회 즉시 감지/알림**
- 이후 **30초마다 자동 배치 실행**
- 새 글이 감지되면,  
  - `[제목]`, `[URL]`, `[본문 요약]`, `[댓글 Top 3]`가 포함된 메시지가 디스코드로 전송됨
  - 중복 글이 나오면 즉시 멈추고, 다음 배치까지 대기

---

## 메시지 예시

```
[수다]신캐 축제에 자기가 참여 안하겠다는데
https://www.inven.co.kr/board/maple/5974/5113339
보상을 왜 아쉬워 하누. 본인이 하기 싫어서 안 하는거 아님...?

[댓글 Top 3]
1. (추천 12) 닉네임: 댓글 내용
2. (추천 8) 닉네임: 댓글 내용
3. (추천 5) 닉네임: 댓글 내용
```

---

## 기타

- **Selenium** 기반 댓글 크롤링(크롬드라이버 필요)
- **DB/설정/파이프라인/테스트** 등 상세 구조는 `architecture.md`, `design-document.md` 참고
- 확장: 멀티 게시판, 고급 필터링, Slack/Telegram 등 다양한 메신저 연동 가능

---

## 문의/기여

- 이슈/PR/문의는 언제든 환영합니다! 