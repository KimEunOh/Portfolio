# Socket 기반 실시간 채팅 애플리케이션

이 프로젝트는 FastAPI와 WebSocket을 활용한 실시간 채팅 애플리케이션입니다. OpenAI의 GPT 모델을 통합하여 AI 기반 대화 기능을 제공하며, 유튜브 라이브 채팅창과 같은 실시간 스트리밍 채팅 기능을 지원합니다.

## 주요 기능

- 실시간 웹소켓 기반 채팅
- OpenAI GPT-3.5 Turbo 모델을 활용한 AI 응답
- 실시간 스트리밍 채팅 지원 (유튜브 라이브 채팅창과 유사)
- 사용자 인증 시스템 (회원가입/로그인)
- 관리자 메시지 시스템
- 채팅방별 실시간 참여자 수 표시
- 보안된 비밀번호 저장 (bcrypt 해싱)
- 실시간 채팅 이력 관리
- 웹 기반 반응형 사용자 인터페이스

## 기술 스택

- **Backend**: FastAPI
- **WebSocket**: FastAPI WebSocket
- **템플릿 엔진**: Jinja2
- **AI 모델**: OpenAI GPT-3.5 Turbo
- **데이터베이스**: SQLite + SQLAlchemy ORM
- **보안**: Passlib + Bcrypt
- **실시간 채팅**: FastAPI WebSocket
- **프론트엔드**: HTML5 + CSS3 + JavaScript

## 프로젝트 구조

```
├── main.py              # 메인 애플리케이션 파일
├── connect.py           # 소켓 연결 관리
├── webConnect.py        # 웹 소켓 구현
├── streaming.py         # 실시간 스트리밍 채팅 구현
├── models.py            # 데이터 모델 및 데이터베이스 스키마
├── templates/          
│   ├── streaming.html   # 스트리밍 채팅 UI
│   └── home.html        # 메인 페이지
├── static/             # 정적 파일 (CSS, JS, 이미지)
├── requirements.txt    # 프로젝트 의존성
└── chat.db            # SQLite 데이터베이스
```

## 설치 방법

1. 가상환경 생성 및 활성화:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 의존성 설치:
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정:
- `.env` 파일을 생성하고 다음 내용을 추가:
```
OPENAI_API_KEY=your_api_key_here
```

4. 데이터베이스 초기화:
```bash
python init_admin.py  # 관리자 계정 생성
```

5. 애플리케이션 실행:
```bash
python main.py
```

## API 엔드포인트

### 채팅 관련
- `GET /`: 채팅 페이지
- `POST /`: 채팅 메시지 처리
- `WebSocket /ws`: 실시간 채팅 연결
- `WebSocket /ws/{client_id}`: 클라이언트별 웹소켓 연결
- `GET /streaming`: 실시간 스트리밍 채팅 페이지
- `WebSocket /ws/streaming`: 실시간 스트리밍 채팅 연결

### 사용자 인증
- `POST /user/register`: 회원가입
- `POST /user/login`: 로그인

## 사용자 인증 시스템

### 회원가입
- 닉네임: 2~20자
- 사용자명: 4~20자 (영문, 숫자, 언더스코어)
- 비밀번호: 최소 8자 (영문+숫자 조합)
- 자동 중복 검사
- bcrypt 기반 비밀번호 해싱

### 로그인
- 사용자명과 비밀번호 인증
- 세션 기반 상태 관리
- 관리자/일반 사용자 권한 구분

## 실시간 스트리밍 채팅 기능

### 주요 특징
- 실시간 메시지 전송 및 수신
- 관리자 메시지 하이라이팅
- 메시지 타임스탬프
- 사용자별 권한 관리
- 채팅방별 참여자 수 실시간 업데이트
- 자동 재연결 메커니즘

### 메시지 타입
- 일반 메시지
- 관리자 메시지
- 시스템 메시지 (입장/퇴장 알림 등)

## 개발 환경에서 실행

개발 모드로 실행 시 자동 리로드가 활성화되어 있습니다:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다. 