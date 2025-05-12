# GW Agent 시스템 아키텍처

## 1. 시스템 개요

GW Agent는 일반적인 대화 처리와 연차 신청을 통합한 에이전트 시스템입니다. LangChain과 LangGraph를 기반으로 구축되었으며, FastAPI를 통해 REST API를 제공합니다.

### 1.1 핵심 기능
- 자연어 기반 대화 처리
- 연차 신청 프로세스 자동화
- 세션 기반 상태 관리
- RESTful API 인터페이스

### 1.2 기술 스택
- **프레임워크**: FastAPI, LangChain, LangGraph
- **언어**: Python 3.9+
- **AI 모델**: GPT-4
- **데이터베이스**: 메모리 기반 세션 저장소
- **로깅**: Python logging 모듈

## 2. 디렉토리 구조

```
LLM/
├── assets/              # 정적 자원 (이미지, 아이콘 등)
├── config.py            # 루트 레벨 설정 파일
├── services/            # 공통 서비스
├── models/              # 공통 모델
├── utils/               # 공통 유틸리티
├── config/              # 공통 설정
├── gw_agent/            # GW Agent 메인 디렉토리
│   ├── api.py          # API 관련 코드
│   ├── main.py         # 메인 애플리케이션 진입점
│   ├── general_chatbot.py # 일반 챗봇 및 연차 신청 처리 통합 에이전트
│   ├── core/           # 코어 기능
│   │   └── session.py  # 세션 관리 로직
│   ├── graph/          # 그래프 관리
│   │   └── builder.py  # LangGraph 그래프 구성
│   ├── agents/         # 에이전트 노드
│   │   ├── chat.py    # 일반 채팅 노드
│   │   └── vacation_nodes.py # 휴가 관련 노드
│   ├── models/         # 모델 정의
│   │   └── state.py   # 상태 관련 타입 정의
│   ├── services/       # 비즈니스 로직
│   │   └── vacation_service.py # 휴가 관련 비즈니스 로직
│   ├── utils/          # 유틸리티
│   │   └── vacation_utils.py  # 휴가 관련 유틸리티 함수
│   ├── config/         # 설정
│   │   └── settings.py # 시스템 설정
│   ├── templates/      # HTML 템플릿
│   ├── static/         # 정적 파일 (CSS, JS 등)
│   ├── README.md       # 프로젝트 문서
│   └── requirements.txt # 의존성 목록
├── docs/               # 문서
│   ├── api_examples.md # API 예제
│   ├── architecture_overview.md # 아키텍처 개요
│   └── system_architecture.md # 시스템 아키텍처 문서
└── CHANGELOG.md        # 변경 이력
```

## 3. 주요 컴포넌트

### 3.1 API 레이어 (api.py)
- FastAPI 기반의 REST API 엔드포인트
  - `/api/chat`: 채팅 요청 처리
  - `/api/health`: 시스템 상태 확인
  - `/chat`: 웹 인터페이스 제공
- 채팅 요청/응답 모델 정의
- 세션 관리 및 상태 처리
- 에러 핸들링 및 로깅

### 3.2 코어 (core/)
- 세션 관리 로직
  - 세션 생성 및 삭제
  - 상태 저장 및 복구
  - 세션 타임아웃 관리
- 세션 ID 생성 및 검증
- 체크포인트 관리

### 3.3 그래프 (graph/)
- LangGraph 기반의 워크플로우 구성
  - 노드 정의 및 연결
  - 상태 전이 관리
  - 조건부 분기 처리
- 그래프 실행 및 체크포인트 관리

### 3.4 에이전트 (agents/)
- 일반 채팅 노드
  - 사용자 입력 처리
  - 컨텍스트 유지
  - 자연어 응답 생성

- 휴가 노드
  - 정보 수집 (collector): 직원 정보, 잔여 연차, 결재 라인 조회
  - 정보 추출 (extractor): 날짜, 연차 유형, 사유 추출
  - 정보 확인 (confirmer): HTML 카드 생성 및 사용자 확인
  - 신청 제출 (submitter): API 호출 및 결과 처리

### 3.5 모델 (models/)
- 상태 관련 타입 정의
  ```python
  class GeneralAgentState(TypedDict):
      messages: List[Message]
      vacation_info: DocumentInfo
      next: str
      thread_id: str
  ```
- API 요청/응답 모델
- 비즈니스 로직 모델

### 3.6 서비스 (services/)
- 휴가 관련 비즈니스 로직
  - 연차 계산
  - 결재 라인 관리
  - 신청 처리
- API 호출 및 데이터 처리
- 비즈니스 규칙 적용

### 3.7 유틸리티 (utils/)
- 공통 유틸리티 함수
- HTML 생성 및 포맷팅
- 날짜 처리 및 변환

### 3.8 설정 (config/)
- 시스템 설정 관리
- 환경 변수 및 상수 정의
- 로깅 설정

## 4. 주요 기능

### 4.1 일반 채팅
- 사용자 메시지 처리 및 의도 파악
- 대화 컨텍스트 유지
- 자연스러운 대화 흐름 생성

### 4.2 연차 신청
- 연차 정보 수집 및 검증
- 사용자 확인 및 수정 처리
- API를 통한 신청 제출

## 5. 데이터 흐름

1. 사용자 요청 수신 (API)
2. 세션 상태 확인/생성
3. 에이전트 유형 판단 및 라우팅
4. 적절한 워크플로우 실행
5. 결과 반환 및 상태 업데이트

## 6. 에러 처리

- HTTP 예외 처리 (400, 401, 404, 500)
- 비즈니스 로직 예외 처리
- 로깅 및 모니터링
- 사용자 친화적 에러 메시지

## 7. 보안

- API 키 관리 (환경 변수, 암호화)
- 세션 보안 (UUID, 타임아웃)
- 입력 데이터 검증
- 에러 메시지 보안

## 8. 확장성

- 모듈화된 구조로 쉬운 기능 추가
- 새로운 에이전트 유형 추가 용이
- 설정 기반 동작 제어
- 체크포인트를 통한 상태 관리 