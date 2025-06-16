# 아키텍처 문서 (Architecture Document)

이 문서는 `design-document.md`를 기반으로 Post Watch AI 프로젝트의 소프트웨어 아키텍처를 설명합니다.

## 1. 프로젝트 구조

프로젝트의 디렉토리 구조는 다음과 같이 구성됩니다.

```
post_watch/
│
├── src/
│   ├── __main__.py         # 애플리케이션 실행을 위한 메인 진입점
│   ├── core/
│   │   ├── __init__.py
│   │   ├── crawler.py      # 웹 콘텐츠를 가져오고 파싱하는 모듈
│   │   ├── detector.py     # 신규 게시물을 감지하는 로직을 포함하는 모듈
│   │   └── summarizer.py   # 게시물 내용을 요약하는 모듈
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py     # 데이터베이스 인터페이스 및 스키마 관리
│   │
│   ├── messenger/
│   │   ├── __init__.py
│   │   └── kakao_sender.py # 카카오톡으로 메시지를 보내는 모듈
│   │
│   └── utils/
│       ├── __init__.py
│       └── config.py       # 설정 파일을 로드하는 유틸리티
│
├── tests/
│   ├── core/
│   │   ├── test_crawler.py
│   │   └── test_detector.py
│   └── ...                 # 기타 테스트 파일
│
├── config/
│   └── config.json.example # 설정 파일 예시
│
├── .gitignore
├── requirements.txt
└── README.md
```

## 2. 모듈 설명

### 2.1. `src/core/`
- **`detector.py`**: 메인 프로세스 루프입니다. 다른 컴포넌트들을 조율하며, `crawler`를 호출하고, 데이터베이스와 대조하여 신규 게시물을 확인합니다. 신규 콘텐츠에 대해서는 `summarizer`를 작동시키고, `messenger` 모듈을 통해 알림을 보냅니다.
- **`crawler.py`**: 주어진 URL에서 HTML 콘텐츠를 가져와 관련 게시물 정보(제목, 링크 등)를 추출하는 역할을 담당합니다. `requests`, `BeautifulSoup`과 같은 라이브러리를 사용합니다.
- **`summarizer.py`**: 게시물의 텍스트 콘텐츠를 받아 OpenAI의 GPT와 같은 외부 AI API를 사용하여 간결한 요약문을 생성합니다.

### 2.2. `src/db/`
- **`database.py`**: 모든 데이터베이스 연산을 관리합니다. 데이터베이스 초기화, 테이블 생성, 신규 게시물 추가 및 기존 게시물 확인 기능을 제공합니다. 단순성을 위해 SQLite를 사용합니다.

### 2.3. `src/messenger/`
- **`kakao_sender.py`**: 카카오톡 API를 사용하여 지정된 카카오톡 챗봇 채널로 메시지를 인증하고 보내는 로직을 처리합니다.

### 2.4. `src/utils/`
- **`config.py`**: `config.json`과 같은 외부 파일에서 대상 URL, API 키, 데이터베이스 경로 등의 설정 값을 로드하는 유틸리티 모듈입니다.

## 3. 데이터베이스 스키마

처리된 게시물을 추적하여 중복 알림을 방지하기 위해 단일 테이블 `posts`를 사용합니다.

### `posts` 테이블
| 컬럼명        | 데이터 타입 | 제약 조건        | 설명                                   |
|---------------|-----------|------------------|----------------------------------------|
| `id`          | INTEGER   | PRIMARY KEY      | 자동 증가 기본 키                      |
| `post_url`    | TEXT      | UNIQUE, NOT NULL | 크롤링된 게시물의 고유 URL             |
| `title`       | TEXT      | NOT NULL         | 게시물의 제목                          |
| `crawled_at`  | TIMESTAMP | NOT NULL         | 게시물이 크롤링된 시간                 |
| `is_notified` | BOOLEAN   | NOT NULL         | 알림이 발송되었는지 여부를 나타내는 플래그 |

## 4. 설정 (Configuration)

애플리케이션 설정은 루트 디렉토리에 위치한 `config.json` 파일을 통해 관리됩니다. `config/config.json.example` 예시 파일이 제공됩니다.

**`config.json` 구조:**
```json
{
  "target_url": "https://example.com/blog",
  "crawl_interval_seconds": 60,
  "db_path": "posts.db",
  "openai_api_key": "YOUR_OPENAI_API_KEY",
  "kakao": {
    "rest_api_key": "YOUR_KAKAO_REST_API_KEY"
  }
}
``` 