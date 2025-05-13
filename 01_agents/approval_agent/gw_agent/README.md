# N2 그룹웨어 API 에이전트 시스템

이 프로젝트는 N2 그룹웨어 API를 자연어 인터페이스로 제공하고, 휴가 신청을 대화형으로 처리하는 기능을 통합한 웹 애플리케이션입니다.

## 프로젝트 개요

이 시스템은 두 가지 주요 에이전트로 구성되어 있습니다:

1. **API 에이전트**: N2 그룹웨어 API를 자연어로 호출할 수 있는 인터페이스를 제공합니다.
2. **휴가 에이전트**: 사용자와 대화를 통해 휴가 신청 과정을 안내합니다.

## 기술 스택

- **백엔드**: FastAPI
- **AI/ML**: LangChain, OpenAI API (GPT-4)
- **프론트엔드**: HTML, JavaScript, Jinja2 템플릿
- **기타**: LangGraph (에이전트 워크플로우 구성)

## 주요 기능

### API 에이전트 기능
- 그룹웨어 API 자연어 인터페이스 제공
- 서버 상태 확인
- 결재 양식 목록 조회
- 결재 문서 승인
- 결재 저장
- 잔여 휴가일수 확인
- 결재 취소
- 결재선 조회

### 휴가 에이전트 기능
- 대화형 휴가 신청 과정 안내
- 휴가 정보 수집 및 검증
- 휴가 신청 제출
- 휴가 상태 확인

## 시스템 구조

- **main.py**: 메인 FastAPI 애플리케이션 및 라우트 설정
- **api_agent.py**: N2 그룹웨어 API 에이전트 구현
- **vacation_agent.py**: 휴가 신청 대화형 에이전트 구현
- **templates/**: HTML 템플릿
  - index.html: 메인 페이지
  - api_agent.html: API 에이전트 인터페이스
  - vacation_agent.html: 휴가 에이전트 인터페이스
- **static/**: 정적 리소스 (이미지 등)
- **.env**: 환경 변수 설정 (API 키 등)
- **requirements.txt**: 의존성 패키지 목록

## 설치 방법

1. 저장소 복제
```
git clone <repository-url>
```

2. 가상 환경 생성 및 활성화
```
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. 의존성 설치
```
pip install -r requirements.txt
```

4. 환경 변수 설정
`.env` 파일에 필요한 API 키 및 환경 변수 설정 (OpenAI API 키 등)

## 실행 방법

1. FastAPI 서버 실행
```
uvicorn main:app --reload
```

2. 웹 브라우저에서 접속
```
http://localhost:8000
```

## 사용 방법

### API 에이전트 사용
1. 웹 인터페이스에서 "API 에이전트" 선택
2. 자연어로 API 관련 요청 입력 (예: "결재 양식 목록을 보여줘")
3. 에이전트의 응답 확인

### 휴가 에이전트 사용
1. 웹 인터페이스에서 "휴가 에이전트" 선택
2. 대화를 통해 휴가 신청 정보 입력
3. 안내에 따라 휴가 신청 완료

## 개발 정보

- LangGraph를 활용한 에이전트 워크플로우 구현
- OpenAI GPT-4 모델 기반 자연어 처리
- FastAPI를 이용한 RESTful API 구현
- 세션 관리를 통한 대화 컨텍스트 유지

## 라이센스

N/A 