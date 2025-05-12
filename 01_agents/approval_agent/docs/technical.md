# GW Agent 기술 문서

## 1. 시스템 아키텍처

### 1.1 개요
GW Agent는 LangChain과 LangGraph를 기반으로 구축된 대화형 에이전트 시스템입니다. 일반 대화와 연차 신청을 통합적으로 처리하며, FastAPI를 통해 REST API를 제공합니다.

### 1.2 핵심 컴포넌트

#### 1.2.1 에이전트 상태 관리
- **GeneralAgentState**: 대화 상태를 관리하는 핵심 클래스
  - 메시지 히스토리 관리
  - 연차 정보 저장
  - 다음 단계 결정
  - 세션 ID 관리

#### 1.2.2 그래프 기반 워크플로우
- **LangGraph**: 대화 흐름을 제어하는 상태 기반 그래프
  - Supervisor: 사용자 의도 파악 및 라우팅
  - Vacation Collector: 연차 정보 수집
  - Vacation Extractor: 정보 추출 및 검증
  - Vacation Confirmer: 사용자 확인
  - Vacation Submitter: 최종 제출

#### 1.2.3 API 클라이언트
- **ApiClient**: 백엔드 시스템과의 통신
  - 연차 신청 처리
  - 직원 정보 조회
  - 결재 라인 조회
  - 잔여 연차 조회

#### 1.2.4 LLM 통합
- **ChatOpenAI**: OpenAI GPT-4o 기반 자연어 처리
  - 사용자 의도 파악
  - 자연어 응답 생성
  - 정보 추출 및 검증
  - 대화 컨텍스트 관리

## 2. 기술 스택

### 2.1 프레임워크
- **FastAPI**: RESTful API 서버
- **LangChain**: LLM 기반 에이전트 프레임워크
- **LangGraph**: 상태 기반 대화 흐름 관리

### 2.2 언어 및 환경
- **Python 3.9+**: 주요 개발 언어
- **GPT-4o-mini**: OpenAI의 LLM 모델
- **메모리 기반 세션 저장소**: 사용자 세션 관리

## 3. 컴포넌트 설명

### 3.1 API 레이어
- **엔드포인트**
  - `/api/chat`: 채팅 요청 처리
  - `/api/health`: 시스템 상태 확인
  - `/chat`: 웹 인터페이스

- **모델**
  ```python
  class ChatRequest(BaseModel):
      message: str
      session_id: Optional[str]
      session_state: Optional[Dict]
      agent_type: Optional[str]
  ```

### 3.2 세션 관리
- **세션 생성 및 검증**
  ```python
  def get_or_create_session(session_id: Optional[str] = None) -> str:
      if session_id:
          return session_id
      return str(uuid.uuid4())
  ```

- **세션 상태**
  ```python
  class GeneralAgentState(TypedDict):
      messages: List[Message]
      vacation_info: DocumentInfo
      next: str
      thread_id: str
  ```

### 3.3 그래프 엔진
- **노드 구성**
  - Supervisor: 사용자 의도 파악
  - Vacation Collector: 연차 정보 수집
  - Vacation Extractor: 정보 추출
  - Vacation Confirmer: 정보 확인
  - Vacation Submitter: 신청 제출

- **의도에 따른 분기**
  ```python
  builder.add_conditional_edges(
      "supervisor",
      lambda state: state["next"],
      {
          "VACATION_REQUEST": "VACATION_REQUEST",
          "GENERAL_CHAT": "GENERAL_CHAT",
          END: END,
      },
  )
  ```

### 3.4 에이전트 노드
- **일반 채팅**
  - 사용자 입력 처리
  - 컨텍스트 유지
  - 자연어 응답 생성

- **연차 처리**
  - 정보 수집
  - 정보 추출
  - 정보 확인
  - 신청 제출

## 4. 데이터 구조 예시

### 4.1 연차 정보
```python
class DocumentInfo(TypedDict):
    mstPid: int
    aprvNm: str
    drafterId: str
    docCn: str
    dayList: List[DayList]
    lineList: List[LineList]
```

### 4.2 세션 상태
```python
class GeneralAgentState(TypedDict):
    messages: List[Message]
    vacation_info: DocumentInfo
    next: str
    thread_id: str
```
