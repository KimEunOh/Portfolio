# 포트폴리오 프로젝트 마이그레이션 현황

## 1. 프로젝트 구조 분석
### 1.1 01_agents/
- [x] approval_agent
  - FastAPI 기반 그룹웨어 API 에이전트
  - LangChain, LangGraph 기반 휴가 신청 챗봇
  - 의존성: FastAPI, LangChain, OpenAI, LangGraph
  - Docker 설정 필요
  - GitHub Actions CI/CD 설정 필요

### 1.2 02_LLM/
- [x] socket/
  - FastAPI와 WebSocket 기반 실시간 채팅
  - OpenAI GPT-3.5 Turbo 통합
  - SQLite + SQLAlchemy ORM
  - 의존성: FastAPI, OpenAI, SQLAlchemy, WebSocket
  - MIT 라이센스
- [x] LLM_local_api/
  - FastAPI 기반 이미지 처리 및 챗봇 API
  - Prometheus + Grafana 모니터링
  - Docker Compose 설정 완료
  - 의존성: FastAPI, OpenAI, FAISS, LangChain
  - 보안 이슈: API 키가 docker-compose.yml에 노출됨
- [x] gpt_api_tutorial/
  - Flask 기반 간단한 GPT-4 챗봇
  - 의존성: Flask, OpenAI, python-dotenv
  - 버그: GPT-4 모델명 오타 ("gpt-4o")
  - Docker 설정 필요
- [x] dify/
  - Dify + OpenWebUI 통합 프로젝트
  - Docker Compose 기반 설정
  - Ollama 모델 통합
  - 포트: 80(Dify API), 3000(OpenWebUI), 11434(Ollama)
  - 상세 설치 가이드 문서화 완료

### 1.3 03_cv-multimodal/
- [x] OCR/
  - OCR 이미지 처리 및 분석
  - YOLOv5 모델 통합
  - Jupyter Notebook 기반 개발
  - Docker 설정 필요
- [x] QA_AI/
  - PDF 기반 QA 시스템
  - 의존성 파일 존재 (requirements.txt)
  - Docker 설정 필요
- [x] deepfake/
  - CLIP 유사도 기반 Multimodal RAG 검증 기법
  - Jupyter Notebook 기반 개발
  - LLaVA, CLIP, YOLOv8 모델 통합
  - 대용량 데이터셋 및 모델 파일 포함
  - Docker 설정 필요
- Poetry 기반 의존성 관리
  - Python 3.11 이상 필요
  - ipykernel 개발 의존성

### 1.4 04_data-science/
- [x] HR_Analytics/
  - 퇴사 예측 및 대전 상권 분석
  - Java + Python 하이브리드 프로젝트
  - Maven 기반 Java 프로젝트 구성
  - Jupyter Notebook 기반 데이터 분석
  - 의존성: org.json:json:20231013
  - Docker 설정 필요
- [x] demo/
  - 더미 데이터 생성 및 시각화
  - Dash 기반 웹 애플리케이션
  - 데이터 실시간 모니터링 기능
  - Docker 설정 필요
- [x] travel_time/
  - 여행 경로 최적화 (TSP)
  - 거리 계산 및 크롤링
  - Jupyter Notebook 기반 개발
  - Docker 설정 필요
- [x] vacation/
  - Dash 기반 휴가 관리 대시보드
  - 휴가 사용 현황 시각화
  - 부서별/유형별 휴가 분석
  - Flask-Caching 활용
  - Docker 설정 필요
- [x] otour/
  - Flask 기반 여행 상품 분석 시스템
  - MySQL 데이터베이스 연동
  - 판매량 분석 및 시각화
  - 포트: 5001
  - 보안 이슈: DB 접속 정보 노출

### 1.5 77_side/
- [x] sujata/
  - PyQt5 기반 판매관리 시스템의 웹 마이그레이션
  - Flask + React.js 기반 웹 애플리케이션
  - Docker Compose 설정 완료
  - 의존성: PyQt5, pandas, SQLAlchemy
  - MIT 라이센스
  - 포트: 5000 (백엔드)

### 1.6 99_archive/
- [x] MCP_example/
  - LangGraph 기반 MCP 에이전트 구현
  - 한국어/영어 버전 README 및 애플리케이션
  - requirements.txt 존재
  - Docker 설정 필요
- [x] DDL/
  - DDL to 엔티티/리포지토리 변환 프롬프트
  - domain/ 및 repository/ 구조
  - 데이터베이스 스키마 관리
- [x] openai_cua/
  - OpenAI Custom User Assistant 샘플
  - Docker 설정 필요
- [x] anthropic_CUA/
  - Anthropic Claude 기반 커스텀 어시스턴트
  - anthropic-quickstarts 포함
  - Docker 설정 필요

## 2. 공통 작업 항목

### 2.1 의존성 관리
- [x] requirements-llm.txt 초안 작성 (approval_agent 기준)
  ```
  fastapi>=0.104.1
  uvicorn>=0.24.0
  python-dotenv>=1.0.0
  langchain-openai>=0.3.12
  langchain-core>=0.2.38
  langchain>=0.3.23
  langgraph>=0.3.25
  openai>=1.10.0,<2.0.0
  ```
- [x] requirements-socket.txt 초안 작성
  ```
  fastapi
  uvicorn[standard]
  SQLAlchemy
  bcrypt==4.0.1
  passlib==1.7.4
  python-jose
  python-multipart
  jinja2
  openai
  ```
- [x] requirements-llm-local.txt 초안 작성
  ```
  fastapi>=0.95.0
  uvicorn>=0.20.0
  prometheus-client>=0.16.0
  pydantic>=2.0.0
  python-dotenv>=0.21.0
  faiss-cpu>=1.7.0
  langchain-community>=0.0.0
  openai>=1.32.0
  pdf2image>=1.16.0
  pillow>=9.0.0
  ```
- [x] requirements-tutorial.txt 초안 작성
  ```
  flask==3.1.0
  python-dotenv==1.0.0
  openai==1.3.0
  ```
- [x] pyproject.toml 초안 작성 (cv-multimodal)
  ```toml
  [tool.poetry]
  name = "ntoday"
  version = "0.1.0"
  python = "^3.11"

  [tool.poetry.dependencies]
  python = "^3.11"

  [tool.poetry.group.dev.dependencies]
  ipykernel = "^6.29.5"
  ```
- [x] pom.xml 초안 작성 (HR_Analytics)
  ```xml
  <dependencies>
    <dependency>
      <groupId>org.json</groupId>
      <artifactId>json</artifactId>
      <version>20231013</version>
    </dependency>
  </dependencies>
  ```
- [ ] requirements-cv.txt 생성
- [ ] 각 프로젝트별 의존성 분석
- [x] requirements-otour.txt 초안 작성
  ```
  flask
  pandas
  sqlalchemy
  pymysql
  ```
- [x] requirements-sujata.txt 초안 작성
  ```
  PyQt5>=5.15.6
  pandas>=1.3.5
  numpy>=1.21.5
  openpyxl>=3.0.9
  sqlalchemy>=1.4.31
  xlrd>=2.0.1
  xlsxwriter>=3.0.3
  reportlab>=3.6.6
  pillow>=9.0.1
  oletools>=0.60.1
  ```

### 2.2 문서화
- [x] README.md 템플릿 확보 (approval_agent의 README.md 활용)
  - 프로젝트 개요
  - 기술 스택
  - 주요 기능
  - 시스템 구조
  - 설치 방법
  - 실행 방법
  - 사용 방법
  - 개발 정보
  - 라이센스
- [x] 상세 설치 가이드 템플릿 확보 (dify의 README.md 활용)
  - Docker Desktop 설치
  - 모델 설정
  - 환경 설정
  - 컨테이너 실행
  - 포트 설정
  - 웹 UI 설정
- [ ] 각 프로젝트 README.md 적용
- [ ] 배지 추가 (GitHub Actions, Docker Hub, PyPI)

### 2.3 CI/CD
- [x] Docker 설정 템플릿 확보 (LLM_local_api, dify)
  - Dockerfile
  - docker-compose.yml (Prometheus + Grafana 포함)
  - .dockerignore
  - 멀티 컨테이너 구성 (dify)
- [x] GitHub Actions 워크플로우 작성
  - Python 패키지 빌드 및 테스트 (python-ci.yml)
  - Docker 이미지 빌드 및 푸시
  - 코드 품질 검사 (ruff)
  - Maven 빌드 및 테스트 (java-ci.yml)
- [ ] 유닛 테스트 설정
- [ ] E2E 테스트 설정
- [ ] pre-commit 설정

### 2.4 경로 수정
- [ ] import 경로 검사 및 수정
- [ ] Dockerfile 경로 검사 및 수정
- [ ] CI 설정 경로 검사 및 수정

## 3. 진행 상황

### 현재 작업 중:
- 01_agents/approval_agent 분석 완료
- 02_LLM/socket 분석 완료
- 02_LLM/LLM_local_api 분석 완료
- 02_LLM/gpt_api_tutorial 분석 완료
- 02_LLM/dify 분석 완료
- 03_cv-multimodal/ 분석 완료
- 04_data-science/HR_Analytics 분석 완료
- 04_data-science/demo 분석 완료
- 04_data-science/travel_time 분석 완료
- 04_data-science/otour 분석 완료
- 77_side/sujata 분석 완료
- requirements-llm.txt 초안 작성
- requirements-socket.txt 초안 작성
- requirements-llm-local.txt 초안 작성
- requirements-tutorial.txt 초안 작성
- pyproject.toml 초안 작성
- pom.xml 초안 작성
- README.md 템플릿 확보
- Docker 설정 템플릿 확보
- requirements-otour.txt 초안 작성
- requirements-sujata.txt 초안 작성
- 99_archive/ 디렉토리 분석 완료
- GitHub Actions 워크플로우 작성 완료
- API 키 보안 강화 완료

### 다음 작업:
- 프로젝트 문서화 개선

## 4. 이슈 및 해결 방안
1. socket 프로젝트의 중복된 의존성
   - 해결: requirements.txt 정리 필요 (uvicorn, python-multipart 등 중복)

7. deepfake 프로젝트 접근 불가
   - [x] 파일 시스템 접근 확인 완료
   - [x] 대용량 파일 정상 확인
   - [ ] Docker 설정 필요
   - [ ] 의존성 관리 필요
8. vacation 프로젝트 접근 불가
   - [x] 파일 시스템 접근 확인 완료
   - [x] 주요 기능 파악 완료
   - [ ] Docker 설정 필요
   - [ ] 의존성 관리 필요 (dash, pandas, plotly 등)
9. 의존성 관리 도구 혼용
   - 해결: uv와 pip requirements.txt 통합 관리 방안 수립 필요
   - uv 기반으로 통일하는 것 고려

11. DB 접속 정보 노출
    - 해결: app.py에서 하드코딩된 DB 접속 정보를 .env 파일로 이동
    - GitHub Actions secrets 활용 계획
14. 프로젝트 문서화 개선
    - 해결: C:\keo\README.md 참고하여 각 프로젝트 README.md 개선 필요
    - 양식: C:\keo\documents_guide.md 양식 참고고