# 전자결재 양식 자동 추천 시스템 개발 계획서

## 1. 목표

- 사용자의 자연어 입력을 받아, 적합한 전자결재 양식(HTML 카드)을 자동으로 추천 및 반환하는 시스템을 개발한다.
- LLM을 활용해 입력 의도를 분류하고, 분류 결과에 따라 미리 정의된 HTML 양식 템플릿을 제공한다.
- 프론트엔드와 백엔드가 연동되어, 사용자는 추천된 양식에 내용을 입력하고 제출할 수 있다.

---

## 2. 전체 아키텍처

1. **사용자 입력 수집**
   - 프론트엔드에서 자연어 입력을 수집

2. **LLM 기반 의도 분류**
   - 입력 문장을 LLM에 전달하여 결재 양식 유형(form_type) 및 키워드 추출

3. **양식 템플릿 매핑**
   - 분류된 form_type에 따라 사전 정의된 HTML 양식 템플릿을 선택

4. **HTML 카드 반환**
   - 선택된 HTML 양식 카드(HTML string)를 프론트엔드에 반환

5. **사용자 입력 및 제출**
   - 사용자가 양식에 내용을 입력 후 제출
   - 제출된 데이터는 결재 시스템(내부 API 또는 외부 연동)으로 전달

---

## 3. 세부 기능 및 구현 계획

### 3.1. LLM 기반 의도 분류

- **입력:** 자연어 문장 (예: "출장비 결재 올려줘")
- **처리:**  
  - LLM 프롬프트 설계 (시스템/유저 역할 구분)
  - OpenAI Function Calling 또는 유사 기능 활용
  - Pydantic 등으로 Output Schema 검증
- **출력:**  
  ```json
  {
    "form_type": "출장비_신청서",
    "keywords": ["출장", "교통비", "비용"]
  }
  ```

### 3.2. 양식 템플릿 관리 및 매핑

- form_type별 HTML 템플릿 사전 정의 (예: 연차 신청서, 출장비 신청서 등)
- form_type → HTML 템플릿 매핑 함수 구현

### 3.3. API/서버 구현

- **엔드포인트:**  
  - POST /form-selector
    - 입력: 사용자 자연어
    - 출력: 추천 양식의 HTML string 또는 JSON
- **로직:**  
  1. 입력 수신
  2. LLM 호출 및 의도 분류
  3. form_type에 맞는 HTML 템플릿 반환

### 3.4. 프론트엔드 연동

- 사용자 입력 폼 및 결과 HTML 카드 표시
- 카드 내 입력값 제출 시, 결재 시스템 연동(POST 등)

---

## 4. 기술 스택 및 도구

- **백엔드:** Python (FastAPI, Flask 등), OpenAI API, Pydantic
- **프론트엔드:** React, Vue, 또는 단순 HTML/JS
- **기타:** LangChain, Schema validation, API 연동

---

## 5. 예외 처리 및 확장성

- 미지원 form_type 입력 시 안내 메시지 반환
- 양식 종류 추가 시 템플릿 및 매핑 함수 확장
- LLM 응답 오류/지연 시 fallback 처리

---

## 6. 개발 단계

1.  **LLM 프롬프트 및 Output Schema 설계** (완료)
    *   `form_selector/schema.py`: `UserInput`, `FormSelectorOutput` Pydantic 모델 정의
    *   `form_selector/llm.py`: `ChatPromptTemplate` 및 `PydanticOutputParser` 설정
2.  **form_type별 HTML 템플릿 작성** (완료)
    *   `templates/` 폴더 내 4종 (`annual_leave.html`, `business_trip.html`, `meeting_expense.html`, `other_expense.html`) HTML 템플릿 생성
3.  **백엔드 API 기본 구현 (LLM 연동, 정적 템플릿 매핑)** (완료)
    *   `form_selector/service.py`: `classify_and_get_template` 초기 버전 (정적 매핑)
    *   `main.py`: FastAPI 앱 설정 및 `/form-selector` 엔드포인트
4.  **RAG 기반 템플릿 검색 기능 도입** (완료)
    *   `requirements.txt`: `langchain-community`, `faiss-cpu` 추가
    *   `form_selector/rag.py`: FAISS 벡터스토어 생성, HTML 템플릿 인덱싱 및 검색 로직 구현
    *   `form_selector/service.py`: `classify_and_get_template` 함수에서 RAG 검색 사용하도록 수정
    *   `form_selector/template_map.py` 삭제 (RAG로 대체)
5.  **기본 프론트엔드 UI 구현** (완료)
    *   `static/index.html`: 사용자 입력 및 결과 표시를 위한 기본 HTML/CSS/JS UI
    *   `main.py`: StaticFiles 마운트 (`/ui` 경로)
6.  **가상 환경 설정 및 실행 환경 안정화** (완료)
    *   프로젝트 루트에 `.venv` 가상환경 생성 및 `requirements.txt` 기반 패키지 설치
    *   FastAPI 실행 명령어 및 환경변수(.env) 관리
7.  **통합 테스트 및 초기 오류 수정** (진행중)
    *   OpenAI API 키 설정 오류 해결
    *   `ModuleNotFoundError` 해결 (가상환경)
    *   `ChatPromptTemplate` 변수 오류 수정
8.  **LLM 응답 품질 개선 (Few-shot 프롬프팅 및 외부 파일 관리)** (완료)
    *   `form_selector/prompts/form_selector_system_prompt.txt`: Few-shot 예시를 포함한 프롬프트 템플릿 생성
    *   `form_selector/llm.py`: 외부 파일에서 프롬프트 템플릿을 로드하도록 수정
9.  **문서화 및 배포** (예정)

---

## 7. 고도화 전략 (추가 제안)

### 7.1. LLM 응답 품질 향상

*   **Few-shot 프롬프팅**: `llm.py`의 프롬프트에 다양한 예시 입출력 쌍을 추가하여 LLM의 `form_type` 분류 및 `slots` 추출 정확도 향상. (완료 - 외부 파일로 관리)
*   **LLM 모델 변경 및 파라미터 튜닝**: 현재 `gpt-4o` 또는 `gpt-3.5-turbo` 사용 중. 필요시 다른 모델(예: Claude, Gemini) 테스트 또는 `temperature`, `top_p` 등 파라미터 조정. (완료 - 수정없음음)
*   **OutputParser 재시도 로직**: LLM 출력이 Pydantic 스키마와 불일치할 경우, `OutputFixingParser` 등을 활용하여 자동 교정 시도 또는 재요청 로직 추가. (OutputFixingParser 적용 및 실패 시 사용자 되묻기 로직 추가 완료)

### 7.2. RAG 성능 개선

*   **임베딩 모델 최적화**: 현재 `OpenAIEmbeddings` 사용 중. 한국어 특화 임베딩 모델 (예: `ko-sroberta-multitask`, `paraphrase-multilingual-mpnet-base-v2` 등 HuggingFace 모델)로 변경하여 검색 품질 향상 고려. (완료 - 추후 고려)
*   **Advanced RAG 기법 적용**:
    *   **Query Transformation**: 사용자 입력(`input`)을 그대로 사용하지 않고, LLM을 통해 검색에 더 적합한 형태로 변환 (예: 키워드 확장, 질문 재구성).
    *   **Re-ranking**: 초기 검색 결과(예: Top-N개)를 가져온 후, 더 정교한 모델(예: Cross-encoder)을 사용하여 순위를 재조정.
    *   **Hybrid Search**: FAISS와 같은 벡터 검색 외에, BM25 같은 키워드 기반 검색을 결합하여 결과 보완.
*   **문서 청킹 전략 개선**: `rag.py`에서 HTML 파일을 `Document`로 만들 때, 의미 단위로 더 잘게 나누거나, 중요한 메타데이터를 더 풍부하게 추가하는 방식 고려.

### 7.3. 사용자 경험(UX) 개선

*   **템플릿 내 슬롯 자동 채우기 정교화**: `service.py`의 `fill_slots_in_template` 함수 개선. LLM이 추출한 `slots` 정보를 단순히 치환하는 것을 넘어, 날짜 형식 변환, 금액 단위 통일 등 추가 처리.
*   **미지원 양식 처리 개선**: 현재는 에러 메시지만 반환. "일반 문의" 또는 "기타 요청" 양식을 기본으로 제공하거나, 사용자에게 어떤 양식을 원하는지 다시 질문하는 방식 등 고려.
*   **비동기 처리 및 로딩 상태 표시**: LLM 및 RAG 처리 시간 동안 UI에 로딩 인디케이터 표시. FastAPI의 `BackgroundTasks` 등을 활용하여 응답 시간 개선.
*   **세션 관리 및 대화형 인터페이스**: 간단한 요청/응답을 넘어, 이전 대화 내용을 기억하고 이어갈 수 있는 챗봇 형태로 발전 (LangChain의 Memory 모듈 활용).

### 7.4. 시스템 안정성 및 확장성

*   **로깅 및 모니터링**: FastAPI 요청/응답, LLM 호출 과정, RAG 검색 결과 등을 상세히 로깅하여 문제 발생 시 추적 용이하게. (예: `loguru`, Sentry 연동)
*   **Configuration 관리**: `OPENAI_API_KEY` 외의 주요 설정값(모델명, 임베딩 모델명, FAISS 인덱스 경로 등)을 `.env` 또는 별도 설정 파일로 분리.
*   **테스트 코드 작성**: `pytest` 등을 사용하여 각 모듈(LLM, RAG, Service)별 단위 테스트 및 통합 테스트 코드 작성.
*   **Docker 기반 배포**: 개발된 애플리케이션을 Docker 이미지로 빌드하여 배포 용이성 및 환경 일관성 확보.

### 7.5. 추가 기능

*   **다중 양식 추천**: 사용자의 모호한 요청에 대해 하나의 양식이 아닌, 여러 후보 양식을 신뢰도와 함께 제시하고 사용자가 선택하도록 유도.
*   **양식 미리보기**: 추천된 HTML 양식을 바로 렌더링하는 것 외에, 양식의 스크린샷이나 간단한 설명을 함께 제공.
*   **관리자 페이지**: 새로운 양식 템플릿을 UI를 통해 쉽게 추가/수정/삭제하고, RAG 인덱스를 재생성할 수 있는 관리자 기능. 