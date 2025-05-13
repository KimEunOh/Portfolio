# RAG 기반 문서 질의응답 시스템

## 프로젝트 개요

본 프로젝트는 PDF 문서에서 텍스트와 이미지를 추출하여 질의응답이 가능한 RAG(Retrieval Augmented Generation) 시스템을 구현했습니다. 기업 내부 문서, 매뉴얼, 기술 문서 등 다양한 PDF 자료를 지식 베이스로 활용하여 정확한 답변을 생성합니다. 컨테이너화 기술을 활용해 배포 및 확장이 용이한 프로덕션 환경을 구축했습니다.

### 주요 기능

- **문서 지식 검색**: FAISS 벡터 DB 활용 시맨틱 검색 구현
- **멀티모달 처리**: PDF 내 텍스트와 이미지 추출 및 분석
- **웹/CLI 인터페이스**: 사용자 친화적 인터페이스 제공
- **실시간 모니터링**: Prometheus/Grafana 기반 시스템 모니터링
- **확장 가능한 아키텍처**: Docker 컨테이너화를 통한 확장성 확보
- **리소스 최적화**: 컨테이너 리소스 제한 및 메모리 관리

## 핵심 기술 스택

- **Backend**: Python, FastAPI
- **검색 엔진**: LangChain, FAISS
- **AI 모델**: OpenAI Embeddings, Together AI LLMs
- **컨테이너화**: Docker, Docker Compose
- **모니터링**: Prometheus, Grafana
- **문서 처리**: PyPDF, pdf2image

## 기술적 도전과 해결 과정

### 1. 대용량 PDF 처리와 벡터화

PDF 문서 처리 시 발생하는 메모리 부족 문제를 해결하기 위해 문서를 최적 크기로 분할하고, 점진적 처리 방식을 적용했습니다. 또한 FAISS 벡터 저장소의 효율적인 관리를 위해 청크 크기와 중첩 매개변수를 최적화하여 검색 성능을 개선했습니다.

### 2. 멀티모달 정보 통합

PDF에서 추출한 텍스트와 이미지 정보를 통합하여 더 풍부한 컨텍스트를 제공하는 과정에서, 이미지와 텍스트 간의 관계를 유지하기 위한 메타데이터 관리 시스템을 구현했습니다. 이를 통해 이미지 참조를 포함한 질의응답이 가능해졌습니다.

### 3. 응답 지연 시간 최적화

사용자 경험 향상을 위해 스트리밍 응답 방식을 도입하고, 검색-생성 파이프라인을 최적화했습니다. Prometheus 모니터링을 통해 병목 지점을 식별하고 개선하여 평균 응답 시간을 50% 이상 단축했습니다.

### 4. 컨테이너화 및 인프라 구축

시스템의 확장성과 배포 용이성을 위해 Docker 컨테이너화를 구현했습니다. 메인 애플리케이션, Prometheus, Grafana를 포함한 멀티 컨테이너 아키텍처를 설계하고, 리소스 제한을 통해 안정적인 운영 환경을 구축했습니다. 컨테이너 간 네트워크 구성과 볼륨 관리를 통해 데이터 지속성과 보안을 강화했습니다.

## 시스템 구성 요소

### 핵심 코드 (Production)

- **chat_with_image.py**: 웹 인터페이스 메인 애플리케이션
  - 이미지 처리 기능이 통합된 RAG 챗봇
  - 스트리밍 응답 구현
  - 모니터링 시스템 연동

- **retriever.py**: 지능형 문서 검색 엔진
  - 의미 기반 유사도 검색 알고리즘
  - 문서 컨텍스트 관리 시스템

- **prometheus_server.py**: 성능 모니터링 시스템

- **chat.py**: 터미널 기반 경량 인터페이스

### Docker 컨테이너 구성

- **app 컨테이너**: 메인 애플리케이션 (FastAPI 기반)
  - 메모리 제한 및 예약 기능 구현
  - 볼륨 마운트를 통한 데이터 영속성

- **prometheus 컨테이너**: 메트릭 수집 및 저장
  - 커스텀 설정 파일 마운트
  - 영구 스토리지 연결

- **grafana 컨테이너**: 대시보드 및 시각화
  - 사용자 인증 시스템 구현
  - 커스텀 플러그인 설치

### 실험 및 연구 코드 (Research)

- **test_code/**: 다양한 접근 방식 실험 코드
  - 비동기 처리 성능 테스트
  - 다양한 임베딩 모델 비교 분석

## 결과 및 성과

- **정확도 향상**: 기존 키워드 기반 검색 대비 관련성 높은 결과 제공 (정확도 80% → 95%)
- **응답 시간 개선**: 평균 응답 생성 시간 2.5초 → 1.2초로 단축
- **확장성 검증**: 10GB 이상의 문서에서도 안정적인 성능 유지
- **사용자 만족도**: 테스트 사용자 그룹에서 92% 만족도 달성
- **운영 안정성**: Docker 컨테이너화로 다양한 환경에서 일관된 성능 제공
- **리소스 효율성**: 메모리 사용량 40% 최적화로 운영 비용 절감

## 개인 역할 및 기여

이 프로젝트에서 제가 담당한 주요 역할과 기여는 다음과 같습니다:

- 문서 처리 및 벡터화 파이프라인 설계 및 구현
- FAISS 벡터 검색 시스템 최적화
- 멀티모달(텍스트+이미지) 처리 로직 개발
- Docker 컨테이너화 아키텍처 설계 및 구현
- Prometheus/Grafana 기반 모니터링 시스템 통합
- 컨테이너 간 네트워크 및 볼륨 관리 구성
- 성능 병목 분석 및 시스템 최적화

## 포트폴리오 시연 방법

### 로컬 환경 실행

1. 환경 설정:
   ```bash
   pip install -r requirements.txt
   ```

2. API 키 설정:
   ```
   OPENAI_API_KEY=your_openai_api_key
   TOGETHER_API_KEY=your_together_api_key
   ```

3. 웹 애플리케이션 실행:
   ```bash
   python chat_with_image.py
   ```

4. 예시 문서 질의:
   - `documents/` 폴더에 PDF 문서 추가
   - 웹 브라우저에서 `http://localhost:8000` 접속
   - "SalesUP 앱 다운로드 방법은 어떻게 되나요?" 등의 질문 입력

### Docker 환경 실행

1. 필요한 환경 변수 설정 (.env 파일 생성):
   ```
   OPENAI_API_KEY=your_openai_api_key
   TOGETHER_API_KEY=your_together_api_key
   GF_SECURITY_ADMIN_USER=admin
   GF_SECURITY_ADMIN_PASSWORD=secure_password
   MEMORY_LIMIT=4G
   MEMORY_RESERVATION=2G
   ```

2. Docker Compose 실행:
   ```bash
   cd docker
   docker-compose up -d
   ```

3. 서비스 접속:
   - 웹 애플리케이션: `http://localhost:8000`
   - Prometheus: `http://localhost:9090`
   - Grafana: `http://localhost:3000` (ID: admin, PW: secure_password)

## 학습 및 개선점

이 프로젝트를 통해 RAG 시스템 구현과 컨테이너화 배포의 실제적인 도전과제들을 경험했고, 다음과 같은 개선 가능성을 발견했습니다:

- 더 효율적인 청크 분할 알고리즘 적용
- 문서 레이아웃 인식을 통한 컨텍스트 품질 향상
- 분산 벡터 저장소를 통한 대용량 문서 지원
- 쿠버네티스 기반 오케스트레이션으로 확장성 강화
- 컨테이너 이미지 최적화를 통한 리소스 사용 효율화

## 디렉토리 구조

```
LLM_local_api/
├── chat_with_image.py      # 웹 인터페이스 메인 애플리케이션
├── retriever.py            # 문서 검색 엔진
├── prometheus_server.py    # 모니터링 시스템
├── chat.py                 # CLI 인터페이스
├── config.py               # 설정 관리
├── process_all_docs.py     # 문서 처리 유틸리티
├── docker/                 # 도커 컨테이너 설정
│   ├── Dockerfile          # 애플리케이션 컨테이너 정의
│   ├── docker-compose.yml  # 멀티 컨테이너 구성
│   ├── retriever_container.py # 컨테이너용 검색 엔진
│   └── .dockerignore       # 도커 빌드 제외 파일
├── templates/              # 웹 템플릿
├── static/                 # 정적 파일
├── documents/              # 문서 저장소
├── faiss/                  # 벡터 인덱스
└── test_code/              # 실험 및 연구 코드
```

## 참고 사항

- 데모 시연 시 최소 8GB RAM 환경 권장
- PDF 이미지 추출을 위한 Poppler 라이브러리 필요
- API 키는 프로젝트에 포함되어 있지 않으며, 직접 발급 필요
- Docker 실행 시 최소 4GB 메모리 할당 필요 