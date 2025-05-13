# N2 그룹웨어 통합 챗봇 기술 문서

## 1. 개요

N2 그룹웨어 통합 챗봇은 일반 대화와 연차 신청 처리를 지원하는 인공지능 기반 비서 시스템입니다. LangChain과 LangGraph를 활용하여 대화 의도 파악, 정보 수집, 연차 신청 API 호출 등의 기능을 수행합니다.

## 2. 시스템 아키텍처

### 2.1 핵심 컴포넌트

- **에이전트 상태 관리**: `GeneralAgentState` 클래스를 통한 대화 상태 관리
- **그래프 기반 워크플로우**: LangGraph를 활용한 대화 흐름 제어
- **API 클라이언트**: 연차 신청, 직원 정보 조회 등 백엔드 API 통신
- **LLM 통합**: OpenAI GPT-4o를 활용한 자연어 이해 및 생성

### 2.2 기술 스택

- **LangChain/LangGraph**: 대화 흐름 및 도구 연계
- **OpenAI API**: 자연어 처리
- **FastAPI**: 웹 서버 및 API 엔드포인트
- **HTTPX**: 비동기 HTTP 클라이언트

## 3. 주요 로직 및 기능

### 3.1 대화 의도 파악

`detect_vacation_intent` 도구는 사용자 메시지에서 연차/휴가 신청 의도를 감지합니다:

```python
@tool
async def detect_vacation_intent(text: str) -> Dict:
    """사용자 텍스트에서 연차/휴가 신청 의도와 관련 정보를 감지합니다."""
    # LLM을 이용한 의도 추출
    # 연차 유형, 날짜, 사유 등 핵심 정보 파싱
```

### 3.2 연차 신청 데이터 처리

연차 정보는 표준화된 형식으로 변환됩니다:

#### 연차 타입 매핑
```python
def map_vacation_type(user_type: str) -> str:
    """사용자 입력 연차 타입을 시스템 코드로 변환합니다."""
    # 연차 -> DAY
    # 오전반차 -> HALF_AM
    # 오후반차 -> HALF_PM
    # 등으로 변환
```

#### 날짜 처리
```python
def create_day_list(start_date: str, end_date: str, vacation_type: str) -> List[Dict]:
    """시작일과 종료일 정보로 dayList 배열을 생성합니다."""
    # 단일 일자 또는 날짜 범위 처리
    # API 형식에 맞는 reqYmd, dvType 배열 생성
```

### 3.3 API 요청 JSON 생성

```python
async def create_vacation_request_json(
    employee_id: str, vacation_data: Dict, approval_line: List
) -> Dict:
    """연차 신청을 위한 API 요청 JSON을 생성합니다."""
    # 필드 구조:
    # mstPid: 1 (연차 신청 문서 ID)
    # aprvNm: "연차 신청"
    # drafterId: 직원ID
    # docCn: 사유
    # dayList: 날짜 정보 배열
    # lineList: 결재선 정보 배열
```

### 3.4 연차 신청 처리 워크플로우

1. **시작단계**: 사용자 의도 감지
2. **정보수집**: 누락된 정보(날짜, 사유 등) 수집
3. **정보확인**: 수집된 정보 확인 및 검증
4. **신청제출**: API 요청 및 카드 생성
5. **종료**: 확인 및 일반 대화 모드 복귀

### 3.5 그래프 기반 대화 관리

```python
def create_general_graph():
    """일반 에이전트와 연차 신청 처리를 위한 그래프 생성"""
    # 노드:
    # route_input: 사용자 입력 라우팅
    # general_chat: 일반 대화 처리
    # vacation_collect: 연차 정보 수집
    
    # 엣지 연결:
    # 조건부 라우팅을 통한 흐름 제어
```

## 4. API 통신

### 4.1 연차 신청 API

```python
async def submit_vacation_request_to_api(request_json: Dict) -> Dict:
    """연차 신청 요청을 API로 전송합니다."""
    # 엔드포인트: "register"
    # 메서드: "PUT"
    # 응답 처리 및 오류 핸들링
```

### 4.2 직원 정보 API

```python
async def fetch_employee_info(employee_id: str) -> Dict:
    # 직원 기본 정보 조회

async def fetch_remaining_vacation_days(employee_id: str) -> Dict:
    # 잔여 연차 일수 조회

async def fetch_approval_line(employee_id: str) -> Dict:
    # 결재 라인 정보 조회
```

## 5. 에러 처리

- **API 통신 오류**: 데이터 유효성 검증, 타임아웃 처리
- **데이터 변환 오류**: 날짜 형식 검증, 필드 누락 확인
- **LLM 응답 오류**: 응답 파싱 실패 시 대체 로직 제공

## 6. 응답 표현

### 6.1 텍스트 응답
일반적인 대화 및 안내는 텍스트 형식으로 응답합니다.

### 6.2 HTML 카드 생성
연차 신청 완료 시 시각적인 카드를의 HTML을 생성합니다:

```python
def create_vacation_card_html(
    vacation_data: Dict, employee_info: Dict, approval_line: List, remaining_days: Any
) -> str:
    """연차 신청 정보를 표시하는 HTML 카드를 생성합니다."""
    # 결재자 목록, 날짜 정보, 휴가 유형 등 표시
```

## 7. 주요 데이터 구조

### 7.1 연차 API 요청 JSON
```json
{
  "mstPid": 1,
  "aprvNm": "연차 신청",
  "drafterId": "01180001",
  "docCn": "개인 사유",
  "dayList": [
    {
      "reqYmd": "2024-06-10",
      "dvType": "DAY"
    }
  ],
  "lineList": [
    {
      "aprvPsId": "01160001",
      "aprvDvTy": "AGREEMENT",
      "ordr": 1
    },
    {
      "aprvPsId": "01230003",
      "aprvDvTy": "APPROVAL",
      "ordr": 2
    }
  ]
}
```

### 7.2 에이전트 상태
```python
class GeneralAgentState(TypedDict):
    messages: Annotated[List, add_messages]  # 대화 메시지 목록
    current_intent: str  # 현재 의도(general/vacation)
    employee_id: Optional[str]  # 직원 ID
    vacation_info: Optional[Dict]  # 수집된 연차 정보
    api_results: Dict[str, Any]  # API 응답 결과
    handoff_to_vacation: bool  # 연차 처리 전환 여부
    vacation_request_json: Optional[Dict]  # 연차 신청 API 요청 JSON
    current_step: Optional[str]  # 현재 단계
    missing_info: Optional[List[str]]  # 누락된 정보 목록
    step_completed: Optional[bool]  # 단계 완료 여부
```

## 8. 세션 관리

웹 서버는 사용자별 세션 상태를 유지하고, 클라이언트-서버 간 세션 동기화를 지원합니다:

```python
# 세션 상태 초기화 또는 복원
if not session_state:
    session_state = {
        "messages": [HumanMessage(content=message)],
        "current_intent": "general",
        "employee_id": "01180001",  # 직원 ID 고정
        # 기타 상태 초기화
    }
else:
    # 기존 세션에 메시지 추가
    session_state["messages"].append(HumanMessage(content=message))
```

이 통합 챗봇은 일반 대화와 연차 신청 처리를 매끄럽게 통합하여, 사용자 경험을 향상시키는 동시에 업무 자동화를 실현합니다. 