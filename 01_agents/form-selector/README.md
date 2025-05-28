# 전자결재 양식 자동 추천 및 완성 시스템

## 1. 프로젝트 개요 (Overview)

본 프로젝트는 사용자의 자연어 입력을 이해하여, 다양한 전자결재 양식 중 가장 적합한 것을 추천하고, 입력 내용에서 주요 정보를 추출하여 해당 양식에 자동으로 채워주는 시스템입니다. 이를 통해 사용자는 반복적인 문서 작성 시간을 줄이고 업무 효율성을 높일 수 있습니다.

주요 기능:
- 자연어 기반 전자결재 양식 추천
- LLM을 활용한 정보 추출 (슬롯 필링)
- 추출된 정보의 동적 HTML 양식 자동 완성
- 상대적/절대적 날짜 표현 자동 변환 (예: "내일", "다음 주 월요일" -> "YYYY-MM-DD")
- 다중 항목 입력 지원 (예: 구매 품의서의 여러 품목)
- 양식 기반 결재자 정보 자동 조회 및 표시

### 예시 화면

다음은 `01_agents/form-selector` 시스템의 주요 기능에 대한 예시 화면입니다.

1.  **양식 선택 및 내용 입력 UI**
    *   사용자가 자연어로 "다음 주 월요일부터 3일간 연차 쓰고 싶어요. 사유는 가족 여행입니다."와 같이 특정 업무(예: 연차 신청)를 요청하면, 시스템은 해당 요청의 의도를 파악하여 '연차 신청서' 양식을 자동으로 선택합니다. 동시에 대화 내용에서 "다음 주 월요일" (시작일), "3일간" (기간), "가족 여행" (사유) 등의 핵심 정보를 추출하여, 아래 그림과 같이 해당 양식의 각 항목을 자동으로 완성된 형태로 사용자에게 제공합니다.
    ![양식 선택 및 내용 입력 UI](assets/스크린샷%202025-05-23%20132023.png)

2.  **LLM 기반 양식 추천 및 슬롯 필링 결과**
    *   사용자의 요청이 특정 양식(예: 연차)에 국한되지 않고, 다양한 업무 관련 요청일 경우에도 LLM은 요청의 맥락(예: "구매")을 이해하고 키워드 기반의 RAG 검색을 통해 가장 적합한 전자결재 양식(예: '비품/소모품 구매 요청서')을 지능적으로 추천합니다. 또한, 입력된 자연어에서 "A4용지 10박스", "네임펜 20개"(구매 품목 및 수량), "연구실 사용"(사용 목적) 등의 필요한 정보를 입력한 경우에도 정확히 추출(Slot Filling)하여 해당 양식의 필드를 자동으로 채워줍니다.
    ![LLM 기반 양식 추천 및 슬롯 필링 결과](assets/스크린샷%202025-05-23%20132503.png)

3.  **결재자 정보 표시**
    *   시스템에서 양식이 추천되고 내용이 채워지면, 해당 양식의 종류(예: '연차 신청서', '비품/소모품 구매 요청서')와 내부 식별자(Form ID), 그리고 기안자 정보를 기반으로, 사전에 정의된 결재 규칙 또는 외부 API 연동을 통해 결재 라인(기안자 정보, 결재자 목록, 결재 구분, 순서)이 자동으로 조회됩니다. 이 정보는 화면 상단에 명확하게 표시되어, 사용자가 해당 문서의 결재 흐름을 한눈에 파악할 수 있도록 지원합니다.
    ![결재자 정보 표시](assets/스크린샷%202025-05-23%20132035.png)

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

## 2.1. 시스템 아키텍처 (System Architecture)

```mermaid
graph TD
    A["사용자 입력 (UI/자연어)"] --> B("FastAPI: /form-selector");
    B --> C{"양식 결정, 정보 추출 및 결재 정보 통합 (service.py)"};
    
    C -- "1a. LLM 기반 양식 분류 및 키워드 추출" --> D["양식 분류 LLM (llm.py)"];
    D -- "분류 결과, 키워드" --> C;
    
    C -- "1b. 키워드 기반 템플릿 검색 (RAG)" --> E["HTML 템플릿 유사도 검색 (rag.py + FAISS)"];
    E -- "유사 템플릿 후보" --> C; 
    %% C에서 D와 E의 결과를 종합하여 최종 양식(템플릿) 결정

    C -- "2. (결정된 양식 기반) 슬롯 추출 요청" --> F["슬롯 추출 LLM 체인 (llm.py)"];
    F -- "슬롯 Pydantic 모델" --> C;
    
    C -- "3. 날짜/시간 등 변환" --> G["유틸리티 함수 (utils.py)"];
    G -- "변환된 슬롯 값" --> C;
    
    C -- "4. 결재 정보 조회" --> C_approver{"결재 정보 조회 로직"};
    C_approver -- "내부 로직/서비스 호출" --> S_approver["service.py 내 get_approval_info (호출)"];
    S_approver --> C_approver;
    C_approver -- "외부 API 직접 호출 (필요시)" --> ExtAPI["외부 결재 API"];
    ExtAPI -- "결재 정보" --> C_approver;
    C_approver -- "조회된 결재 정보" --> C;
    
    C -- "5. HTML 템플릿 채우기 및 최종 응답 생성" --> H["최종 HTML 및 데이터 통합"];
    H --> B;
    
    B --> I["API 응답 (JSON: HTML, 슬롯 정보, 결재 정보 등)"];
    I --> A;
    
    subgraph "리소스: LLM 설정 및 프롬프트"
        J["프롬프트 템플릿 (prompts/)"]
        K["양식별 설정 (form_configs.py)"]
        LLM_Core["LLM 실행환경/공유객체 (llm.py)"]
    end

    subgraph "리소스: 데이터 저장소 및 스키마"
        L["Pydantic 모델 (schema.py)"]
        M["HTML 템플릿 (templates/)"]
        N["FAISS 인덱스 (faiss_index/)"]
    end

    %% Connections to Resources
    D -.-> J;
    D -.-> LLM_Core;

    F -.-> J;
    F -.-> K;
    F -.-> L; 
    F -.-> LLM_Core;
    
    E -.-> M; 
    E -.-> N;
    
    G -.-> LLM_Core; 

    C -.-> L; 
    S_approver -.-> L; 
    C_approver -.-> L; 
```

**결재자 정보 조회 흐름:**

- 사용자가 UI에서 특정 양식에 대한 결재 정보 조회를 요청하면 (일반적으로 양식 로드 후), UI는 기안자 ID와 양식 ID를 FastAPI 백엔드의 `/approver-info` 또는 `/myLine` 엔드포인트로 전송합니다.
- `/approver-info`는 내부 로직이나 `service.py`의 `get_approval_info` 함수를 통해, `/myLine`은 외부 결재 시스템 API를 직접 호출하여 결재 라인 정보를 가져옵니다.
- 조회된 결재 정보(기안자, 결재자 목록 등)는 UI로 반환되어 화면에 표시됩니다.

## 3. 디렉토리 구조 (Directory Structure)

```
01_agents/form-selector/
├── .venv/                  # 가상 환경
├── form_selector/          # 핵심 백엔드 애플리케이션 패키지
│   ├── __init__.py
│   ├── service.py          # 핵심 서비스 로직 (양식 분류, 슬롯 추출, 템플릿 채우기)
│   ├── llm.py              # LangChain LLM 체인 구성
│   ├── schema.py           # Pydantic 모델 (데이터 스키마 정의)
│   ├── rag.py              # RAG 로직 (FAISS 기반 HTML 템플릿 검색)
│   ├── utils.py            # 유틸리티 함수 (날짜 파싱 등)
│   └── prompts/            # LLM 프롬프트 템플릿 저장 디렉토리
│       ├── form_classifier_prompt.txt
│       └── ... (각 양식별 슬롯 추출 프롬프트)
├── static/                 # 정적 파일 (CSS, JavaScript, 메인 HTML)
│   ├── css/                # CSS 파일 저장 폴더
│   │   └── style.css
│   ├── js/                 # JavaScript 파일 저장 폴더
│   │   ├── purchase_approval_scripts.js
│   │   └── ... (각 양식별 JS 파일)
│   └── index.html          # 메인 사용자 인터페이스 HTML
├── templates/              # 서버에서 처리되어 클라이언트로 전달될 HTML 양식 템플릿
│   ├── purchase_approval_form.html
│   └── ... (각 양식별 HTML 템플릿)
├── faiss_index/            # FAISS 벡터 스토어 인덱스 저장 디렉토리
├── main.py                 # FastAPI 앱 정의 및 API 엔드포인트 (애플리케이션 진입점)
├── form_configs.py     # 양식별 설정 (모델, 프롬프트 경로, HTML 경로 등)
├── .env.example            # 환경 변수 예시 파일
├── README.md               # 프로젝트 설명 문서 (현재 파일)
└── requirements.txt        # Python 라이브러리 의존성 목록
```

## 4. 설치 및 실행 방법 (Setup and Run)

1.  **저장소 복제 (Clone Repository):**
    ```bash
    git clone <repository_url>
    cd 01_agents/form-selector
    ```

2.  **가상 환경 생성 및 활성화:**
    ```bash
    python -m venv .venv
    # Windows
    .venv\\Scripts\\activate
    # macOS/Linux
    source .venv/bin/activate
    ```

3.  **필수 라이브러리 설치:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **환경 변수 설정:**
    -   `.env.example` 파일을 복사하여 `.env` 파일을 생성합니다.
        ```bash
        cp .env.example .env
        ```
    -   `.env` 파일을 열어 실제 OpenAI API 키 등 필요한 환경 변수를 설정합니다.
        ```
        OPENAI_API_KEY="sk-your_openai_api_key_here"
        # 기타 필요한 환경 변수들...
        ```

5.  **애플리케이션 실행:**
    FastAPI 애플리케이션은 프로젝트 루트 디렉토리의 `main.py` 파일에서 실행합니다.
    프로젝트 루트 디렉토리(`01_agents/form-selector/`)에서 다음 명령어를 실행합니다.
    ```bash
    uvicorn main:app --reload --port 8000
    ```
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
        -   **날짜/시간 변환**: LLM이 추출한 자연어 날짜/시간 표현을 표준 형식으로 변환하기 위해 `form_selector/utils.py`의 파싱 함수들을 사용합니다. 주요 파싱 로직은 다음과 같습니다:
            -   `parse_relative_date_to_iso` (주로 "YYYY-MM-DD" 형식 반환):
                1.  **규칙 기반 1차 변환**: "오늘", "내일", "다음 주 월요일", "2023년 12월 25일" 등 비교적 명확한 날짜 표현을 `dateutil` 라이브러리 및 내부 규칙을 통해 우선적으로 파싱합니다.
                2.  **LLM 기반 2차 변환**: 1차 규칙 기반 파싱으로 변환되지 못한 복잡하거나 모호한 표현에 대해, 해당 날짜 문자열과 현재 날짜 정보를 `_call_llm_for_datetime_parsing` 함수를 통해 LLM에 전달하여 "YYYY-MM-DD" 형식으로 변환을 시도합니다. LLM은 제공된 오늘 날짜를 기준으로 상대적인 날짜를 계산합니다.
            -   `parse_datetime_description_to_iso_local` (주로 "YYYY-MM-DDTHH:MM" 형식 반환):
        -   구매 품의서의 경우, 아이템 리스트 내 각 아이템의 `item_delivery_request_date` 키를 `item_delivery_date`로, `item_purpose` 키를 `item_notes`로 내부적으로 키 이름을 변경하여 처리합니다. (날짜 파싱은 키 변경 후 이루어짐)
        -   휴가 신청서의 `leave_type` (예: "오전 반차")과 같이 LLM이 자연어로 추출한 특정 슬롯 값을 HTML `<select>` 태그의 `value` (예: "half_day_morning")에 맞게 내부적으로 매핑(`LEAVE_TYPE_TEXT_TO_VALUE_MAP` 사용)합니다.
        -   야근 신청서의 `overtime_ampm` 값을 "AM" 또는 "PM"으로 표준화합니다.
        -   HTML 템플릿에 값을 채울 때 `re.sub`의 백슬래시 문제를 방지하기 위해 슬롯 값 내 백슬래시를 이스케이프 처리합니다.
        -   JavaScript로 전달될 다중 항목 데이터(예: 구매 품의서의 품목 리스트)는 JSON 문자열로 변환됩니다.
    3.  처리된 슬롯 값들은 검색된 HTML 템플릿 내의 해당 위치(플레이스홀더)에 삽입됩니다.

-   **결재자 정보 조회 (Approver Information Retrieval):**
    1.  양식 추천 및 슬롯 채우기가 완료된 후, 클라이언트(UI)는 해당 양식의 식별자(`mstPid`)와 기안자 ID(`drafterId`)를 `/approver-info` 또는 `/myLine` API 엔드포인트로 전송합니다.
    2.  `/approver-info` 엔드포인트는 내부 로직 또는 서비스(`service.py`의 `get_approval_info`)를 통해 결재자 정보를 조회합니다.
    3.  `/myLine` 엔드포인트는 환경 변수(`APPROVAL_API_BASE_URL`)에 설정된 외부 결재 API를 직접 호출하여 실시간으로 결재 라인 정보를 가져옵니다.
    4.  조회된 기안자 정보(이름, 부서) 및 결재자 목록(결재자 ID, 이름, 결재 구분, 순서)은 JSON 형식으로 클라이언트에 반환되어 화면에 표시됩니다.

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

## 7. 새로운 양식 추가 방법 (Adding New Forms)

새로운 전자결재 양식을 시스템에 통합하는 방법에 대한 자세한 안내는 `NEW_FORM_INTEGRATION_MANUAL.md` 파일을 참고하십시오. 이 문서는 HTML 템플릿 준비, Pydantic 모델 정의, 슬롯 추출 프롬프트 생성, 양식 설정 파일 업데이트, RAG 인덱스 업데이트 및 테스트 등 새로운 양식을 추가하는 데 필요한 단계별 지침을 제공합니다.

---

*이 README 문서는 프로젝트 진행 상황에 따라 지속적으로 업데이트될 예정입니다.* 
