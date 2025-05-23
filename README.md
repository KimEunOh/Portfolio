## 프로젝트 구조

## [00_docs/](00_docs/)
- 프로젝트 관련 문서
  - 1. 발표자료 : AI 컨퍼런스 관련 자료
  - 2. 테스트 결과 : 모니터링 관련 자료

## [01_agents/](01_agents/)
### 1. [approval_agent/](01_agents/approval_agent/)
- 전자결재 챗봇 구현
  - API 통신 기반 결재 정보 불러오기 및 전송 프로세스 구현
  - LangGraph의 상태 기반 워크플로우로 복잡한 대화 흐름 관리
  - 연차 신청 프로세스를 자연어 대화로 처리하는 대화형 인터페이스
  - 문의 의도 파악, 연차 정보 수집, 검증, 제출 등의 프로세스 자동화
- 주요 기술 스택: 
  - FastAPI, Uvicorn, Jinja2
  - LangChain, LangGraph, OpenAI


## [02_LLM/](02_LLM/)
- Large Language Model 관련 프로젝트
### 1. [LLM_local_api/](02_LLM/LLM_local_api/)
- RAG 기반 문서 질의응답 시스템
  - PDF에서 텍스트와 이미지를 추출하여 지식 기반 QA 시스템 구현
  - FAISS 벡터 DB를 활용한 시맨틱 검색
  - 대용량 PDF 처리와 멀티모달 정보 통합
  - Docker 컨테이너화를 통한 배포 및 확장성 확보
  - Prometheus/Grafana 기반 시스템 모니터링
- 주요 기술 스택: 
  - FastAPI, Uvicorn, Flask
  - LangChain, LangGraph, FAISS
  - OpenAI, Together AI
  - Docker, Docker Compose

### 2. [socket/](02_LLM/socket/)
- WebSocket 기반 실시간 스트리밍 채팅 시스템
  - 대규모 동시 접속과 실시간 메시지 처리를 위한 확장 가능한 아키텍처
  - WebSocket 기반 지연 시간을 최소화한 양방향 통신
  - AI 기반 대화 기능 통합 (OpenAI GPT)
  - 샤딩 아키텍처와 메시지 큐잉을 통한 성능 최적화
  - 유저 인증, 채팅방 관리, 시스템 모니터링, 통계 수집 등
- 주요 기술 스택: 
  - WebSocket, FastAPI, SQLAlchemy
  - JWT & bcrypt, OpenAI API
  - Locust (부하 테스트)
  - psutil (시스템 모니터링)

## [03_cv-multimodal/](03_cv-multimodal/)
### 1. [deepfake/](03_cv-multimodal/deepfake/)
- CLIP 유사도 기반 Multimodal RAG 검증 기법 구현
  - 멀티모달 모델(CLIP, LLaVA)을 활용한 이미지-텍스트 의미적 유사도 분석
  - GradCAM++, LayerCAM을 통한 AI 모델의 판단 근거 시각화
  - YOLOv8 기반 객체 탐지와 연계된 특징 분석
  - 멀티모달 RAG 시스템의 응답 신뢰도 검증
- 주요 기술 스택:
  - PyTorch, transformers, together-cli
  - CLIP, LLaVA, YOLOv8
  - GradCAM++, LayerCAM, EigenGradCAM
  - pandas, numpy, captum

### 2. [OCR/](03_cv-multimodal/OCR/)
- 소매점 상품 정보 OCR 및 데이터 추출 자동화 시스템
  - 두 가지 독립 시스템으로 구성:
    1. 테이블 이미지 CSV 변환 시스템: 정형화된 상품 목록 테이블에서 CSV 파일로 직접 변환
    2. 가격표 인식 및 데이터 추출 시스템: 매장 가격표를 자동 인식하고 상품 정보 추출
  - 프롬프트 엔지니어링을 통한 OCR 데이터 구조화
  - YOLOv5를 활용한 가격표 영역 자동 인식 (mAP@0.5 = 0.91)
  - GPT-4o, o3-mini, Gemini 모델 활용 및 성능 비교
- 주요 기술 스택: 
  - YOLOv5, PyTorch, ultralytics
  - OpenCV, Pillow, torchvision
  - Tesseract OCR, Gemini, GPT-4V
  - LangChain, scipy, numpy, pandas


## [04_data-science/](04_data-science/)
  - 데이터 전처리, 분석 및 시각화, 예측 모델 구현
  ### 1. [vacation/](04_data-science/vacation/)
  - 연차 기록 크롤링 및 Dash 기반 대시보드 구성
  - Selenium, Dash
  ### 2. [travel_time/](04_data-science/travel_time/)
  - 5개의 근무지를 할당받은 경우, 최적 경로 추천 프로젝트
  - Naver Maps API, Geocoding API 활용
  - 캐싱을 통한 연산 속도 및 자원 최적화
  - 자체적인 TSP (Traveling Salesman Problem) 알고리즘 구현
  ### 3. [HR_Analytics/](04_data-science/HR_Analytics/) 
  - IBM HR Analytics Employee Attrition & Performance 데이터 기반 퇴사 예측 프로젝트
  - 데이터 전처리 및 분석 프로세스 구현 (seaborn, matplotlib, plotly)
  - Scikit-learn 기반 이직 확률 예측 모델 구현
    - 하이퍼파라미터 최적화 (hyperopt)
    - 모델 성능 평가 (ROC-AUC, F1-score)
    - 중요 변수 분석 (SHAP)
  - 대전광역시 자치구별 신용카드 매출 데이터 분석
    - GeoPandas/folium 기반 지도 시각화
    - 구·카테고리별 매출 패턴 분석
    - Dash를 통한 대시보드 구성
  ### 4. [demo/](04_data-science/demo/) 
  - 더미데이터를 생성하고, 시각화 하는 프로젝트
  - 파견업체에서 기록한 근무 직원들의 근무 내용에 대한 데이터를 상정하고 생성
  - 주요 기술: bootstrap, dash
  - 주요 알고리즘: 가우시안 함수를 사용한 데이터 분포 조절, 직원과 근무 시간, 피드백 점수에 따른 판매량 등 변수를 고려한 독창적인 생성 알고리즘 구현
  ### 5. [otour/](04_data-science/otour/)
  - 여행사 데이터를 기반으로, 데이터 분석 및 ML & DL 모델 구현
  - 주요 기능 : 트리맵 시각화(squarify), SVR, GradientBoostingRegressor, Sequential 모델, Adam 옵티마이저
  - 주요 기술 스택:  scikit-learn, TensorFlow/Keras, Optuna, Flask, pandas, numpy, matplotlib, seaborn, plotly, etc.

## [99_archive/](99_archive/)
  ### 1. [cua/](99_archive/cua/)
  - Computer using agent 활용 예제
  - AI가 사용자의 화면을 인식하고, 좌표를 기반으로 마우스 클릭, 키 입력등의 작업을 수행할 수 있도록 하는 프로젝트

  ### 2. [DDL/](99_archive/DDL/)
  - Data Definition Language 의 약자
  - 데이터베이스 스키마를 정의하는 일련의 SQL 명령
  - AI를 통해 DDL 기반의  **Domain(Entity) 클래스**와 **Repository 인터페이스**를 생성
  - 회사 보안 관련 내용 포함으로 삭제

  ### 3. [dify/](99_archive/dify/)
  - Dify 프로젝트
  - Made by Teddynote
  - dify 와 Openwebui를 활용하여 웹 애플리케이션 구현

  ### 4. [MCP_example/](99_archive/MCP_example/)
  - MCP 프로젝트 예제
  - Made by Teddynote
  - smithery 에서 가져온 도구들을 바인딩하는 예제 


### 8. 기타 파일
- `.cursorrules`: cursor 규칙
- `.gitignore`: git 무시 규칙
- `README.md`: 프로젝트 설명
- `.env`: 환경 변수
