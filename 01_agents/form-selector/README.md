# 전자결재 양식 자동 추천 및 완성 시스템

## 1. 프로젝트 개요 (Overview)

본 프로젝트는 사용자의 자연어 입력을 이해하여, 다양한 전자결재 양식 중 가장 적합한 것을 추천하고, 입력 내용에서 주요 정보를 추출하여 해당 양식에 자동으로 채워주는 시스템입니다. 이를 통해 사용자는 반복적인 문서 작성 시간을 줄이고 업무 효율성을 높일 수 있습니다.

주요 기능:
- 자연어 기반 전자결재 양식 추천
- LLM을 활용한 정보 추출 (슬롯 필링)
- 추출된 정보의 동적 HTML 양식 자동 완성
- 상대적/절대적 날짜 표현 자동 변환 (예: "내일", "다음 주 월요일" -> "YYYY-MM-DD")
- 다중 항목 입력 지원 (예: 구매 품의서의 여러 품목)

## 2. 기술 스택 (Tech Stack)

- **백엔드:**
    - Python 3.10+
    - FastAPI: 고성능 웹 프레임워크
    - LangChain: LLM 애플리케이션 개발 프레임워크
    - Pydantic: 데이터 유효성 검사 및 설정 관리
    - Uvicorn: ASGI 서버
- **프론트엔드:**
    - HTML5
    - CSS3
    - JavaScript (ES6+)
- **LLM:**
    - OpenAI GPT-4o (또는 호환 가능한 모델)
- **벡터 스토어 (RAG):**
    - FAISS: 유사도 검색을 위한 라이브러리

## 3. 디렉토리 구조 (Directory Structure)

\`\`\`
01_agents/form-selector/
├── .venv/                  # 가상 환경
├── form_selector/          # 핵심 백엔드 애플리케이션 패키지
│   ├── __init__.py
│   ├── main.py             # FastAPI 앱 정의 및 API 엔드포인트
│   ├── service.py          # 핵심 서비스 로직 (양식 분류, 슬롯 추출, 템플릿 채우기)
│   ├── llm.py              # LangChain LLM 체인 구성
│   ├── schema.py           # Pydantic 모델 (데이터 스키마 정의)
│   ├── rag.py              # RAG 로직 (FAISS 기반 HTML 템플릿 검색)
│   ├── form_configs.py     # 양식별 설정 (모델, 프롬프트 경로, HTML 경로 등)
│   ├── utils.py            # 유틸리티 함수 (날짜 파싱 등)
│   └── prompts/            # LLM 프롬프트 템플릿 저장 디렉토리
│       ├── form_classifier_prompt.txt
│       └── ... (각 양식별 슬롯 추출 프롬프트)
├── static/                 # 정적 파일 (CSS, JavaScript, 메인 HTML)
│   ├── css/                # (제안) CSS 파일 저장 폴더
│   │   └── style.css
│   ├── js/                 # (제안) JavaScript 파일 저장 폴더
│   │   ├── purchase_approval_scripts.js
│   │   └── ... (각 양식별 JS 파일)
│   └── index.html          # 메인 사용자 인터페이스 HTML
├── templates/              # 서버에서 처리되어 클라이언트로 전달될 HTML 양식 템플릿
│   ├── purchase_approval_form.html
│   └── ... (각 양식별 HTML 템플릿)
├── .env.example            # 환경 변수 예시 파일
├── README.md               # 프로젝트 설명 문서 (현재 파일)
└── requirements.txt        # Python 라이브러리 의존성 목록
\`\`\`

## 4. 설치 및 실행 방법 (Setup and Run)

1.  **저장소 복제 (Clone Repository):**
    \`\`\`bash
    git clone <repository_url>
    cd 01_agents/form-selector
    \`\`\`

2.  **가상 환경 생성 및 활성화:**
    \`\`\`bash
    python -m venv .venv
    # Windows
    .venv\\Scripts\\activate
    # macOS/Linux
    source .venv/bin/activate
    \`\`\`

3.  **필수 라이브러리 설치:**
    \`\`\`bash
    pip install -r requirements.txt
    \`\`\`

4.  **환경 변수 설정:**
    -   `.env.example` 파일을 복사하여 `.env` 파일을 생성합니다.
        \`\`\`bash
        cp .env.example .env
        \`\`\`
    -   `.env` 파일을 열어 실제 OpenAI API 키 등 필요한 환경 변수를 설정합니다.
        \`\`\`
        OPENAI_API_KEY="sk-your_openai_api_key_here"
        # 기타 필요한 환경 변수들...
        \`\`\`

5.  **애플리케이션 실행:**
    FastAPI 애플리케이션은 `form_selector` 패키지 내의 `main.py` 파일에서 실행합니다.
    프로젝트 루트 디렉토리(`01_agents/form-selector/`)에서 다음 명령어를 실행합니다.
    \`\`\`bash
    uvicorn form_selector.main:app --reload --port 8000
    \`\`\`
    -   `--reload`: 코드 변경 시 서버 자동 재시작
    -   `--port 8000`: 8000번 포트 사용 (필요시 변경 가능)

6.  **애플리케이션 접속:**
    웹 브라우저에서 `http://127.0.0.1:8000` 로 접속합니다.

## 5. 주요 기능 상세 설명 (Features)

-   **양식 추천 (Form Recommendation):**
    1.  사용자가 자연어로 원하는 업무를 입력합니다 (예: "다음 주 월요일부터 3일간 연차 쓰고 싶어요").
    2.  양식 분류 LLM 체인(`llm.py`의 `get_form_classifier_chain`)이 입력을 분석하여 가장 적합한 양식의 종류(예: "연차 신청서")와 검색 키워드를 추출합니다.
    3.  추출된 양식 종류와 키워드를 `rag.py`의 `retrieve_template` 함수로 전달하여, FAISS 벡터 스토어에 인덱싱된 HTML 템플릿 중 가장 유사한 것을 검색합니다.

-   **정보 자동 채우기 (Slot Auto-filling):**
    1.  분류된 양식 종류에 해당하는 슬롯 추출 LLM 체인(`llm.py`의 `SLOT_EXTRACTOR_CHAINS`)이 사용자 입력으로부터 필요한 정보들(예: 휴가 시작일, 기간, 사유)을 추출합니다.
    2.  `service.py`의 `fill_slots_in_template` 함수는 추출된 슬롯 값들을 처리합니다:
        -   `utils.py`의 `parse_relative_date_to_iso` 등을 사용하여 "내일", "다음 주 월요일" 같은 날짜 표현을 "YYYY-MM-DD" 형식으로 변환합니다.
        -   구매 품의서의 경우, `item_delivery_request_date`를 `item_delivery_date`로, `item_purpose`를 `item_notes`로 내부적으로 키 이름을 변경하여 처리합니다.
        -   JavaScript로 전달될 다중 항목 데이터(예: 구매 품의서의 품목 리스트)는 JSON 문자열로 변환됩니다.
    3.  처리된 슬롯 값들은 검색된 HTML 템플릿 내의 해당 위치(플레이스홀더)에 삽입됩니다.

-   **지원 양식 목록:**
    (현재 `form_configs.py`의 `AVAILABLE_FORM_TYPES` 리스트를 참고하여 작성 필요. 예시:)
    -   연차 신청서
    -   야근식대비용 신청서
    -   교통비 신청서
    -   파견 및 출장 보고서
    -   비품/소모품 구입내역서
    -   구매 품의서
    -   개인 경비 사용 내역서
    -   법인카드 지출내역서
    -   *(추가 예정 양식)*

-   **오류 처리:**
    -   LLM이 양식 분류에 실패하거나 슬롯 추출에 실패(파싱 오류 등)하는 경우, 사용자에게 적절한 안내 메시지를 포함한 JSON 응답을 반환합니다.
    -   요청된 양식의 HTML 템플릿을 찾을 수 없는 경우에도 오류를 반환합니다.

## 6. 향후 개선 방향 (Future Work)

-   **코드 모듈성 강화:** 각 기능별 책임 분리 및 코드 가독성 향상
-   **UI/UX 개선:** 사용자 편의성 증대 및 시각적 디자인 개선
-   **추가 양식 지원 확대:** 다양한 종류의 전자결재 양식 추가
-   **테스트 코드 작성:** 단위 테스트 및 통합 테스트를 통한 안정성 확보
-   **사용자 인증/인가 기능 추가:** (필요시)
-   **데이터베이스 연동:** (필요시) 신청 내역 저장 및 관리 기능
-   **결재 라인 자동 완성 및 선택:** 결재 라인 자동 완성 및 선택 기능 추가

---

*이 README 문서는 프로젝트 진행 상황에 따라 지속적으로 업데이트될 예정입니다.* 