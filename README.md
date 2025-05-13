## 프로젝트 구조

## 00_docs ('00_docs/')
- 프로젝트 관련 문서
  - 1. 발표자료 : AI 컨퍼런스 관련 자료

## 01_agents ('01_agents/')
### 1. approval_agent ('approval_agent/')
- 전자결재 챗봇 구현
  - API 통신 기반 결재 정보 불러오기 및 전송 프로세스 구현
- 주요 기술 스택: 
  - FastAPI, Uvicorn, Jinja2
  - LangChain, LangGraph, OpenAI


## 02_LLM ('02_LLM/')
- Large Language Model 관련 프로젝트
### 1. LLM_local_api ('LLM_local_api/')
- togetherai를 활용하여 GPU 클라우드 서버와 연동한 챗봇. 
  - 문서에서 관련 높은 페이지의 이미지를 추출하여 답변으로 활용하는 지식 기반 챗봇.
  - 사용량 및 자원 관리를 위한 Prometheus, Grafana 활용
  - 배포 및 모니터링을 위한 Docker, Docker Compose 활용
- 주요 기술 스택: 
  - FastAPI, Uvicorn, Flask
  - LangChain, LangGraph, FAISS
  - OpenAI, Together AI
  - Docker, Docker Compose

### 2. socket ('socket/')
- 소켓 통신을 활용한 실시간 채팅방 구현
  - 1:1 채팅, 스트리밍 채팅, AI와의 채팅 구현
  - 사용자 인증, 채팅방 관리, 시스템 모니터링, 통계 수집 등
- 주요 기술 스택: 
  - WebSocket, JWT & bcrypt, psutil

## 03_cv-multimodal ('03_cv-multimodal/')
### 1. deepfake ('deepfake/')
- Fine-tuning을 통한 도메인 특화 모델 구현(딥페이크 탐지)
- CLIP 유사도 기반 Multimodal RAG 검증 기법 구현
- 주요 기능:
  - CLIP 기반 분석
    - 이미지-텍스트 간 의미적 유사도 계산
    - 멀티모달 임베딩 추출 및 비교
    - GradCAM++, LayerCAM을 통한 판단 근거 시각화
  - LLaVA 모델 활용
    - 이미지 내용 자연어 설명 생성
    - 커스텀 데이터셋 기반 파인튜닝
    - 설명 생성 결과의 신뢰도 평가
  - RAG 파이프라인
    - 멀티모달 검색 및 검증
    - 텍스트 중심의 RAG를 멀티모달 환경으로 확장
    - 재현율 향상을 통한 탐지 누락 방지
- 주요 기술 스택:
  - PyTorch, transformers, together-cli
  - CLIP, LLaVA, YOLOv8
  - GradCAM++, LayerCAM, EigenGradCAM
  - pandas, numpy, captum

### 2. OCR ('OCR/')
- 촬영된 테이블 이미지를 다시 엑셀(csv)로 추출하는 프로젝트
- 주요 기능:
  - 마트 가격표를 멀티모달 모델을 이용하여 가격, 제품명, 상품 코드 등을 추출하여 csv 파일 변환 및 저장
  - 바운딩 박스를 통한 모델 학습
  - YOLOv5를 활용하여 가격표 영역 바운딩 박스 검출 및 좌표 추출
  - 추출된 좌표를 기반으로 가격표 영역 추출 및 엑셀(csv)로 저장
  - 혹은 LMM을 활용한 테이블 이미지 or 가격표 영역 검출 및 추출(gemini, gpt-4o, etc.)
  - 이를 위한 다양한 프롬프트 엔지니어링 적용
- 주요 기술 스택: 
  - YOLOv5, PyTorch, ultralytics
  - OpenCV, Pillow, torchvision
  - Tesseract OCR, Gemini, GPT-4V
  - scipy, numpy, pandas


## 04_data-science ('04_data-science/')
  - 데이터 전처리, 분석 및 시각화, 예측 모델 구현
  ### 1. vacation ('vacation/')
  - 연차 기록 크롤링 및 Dash 기반 대시보드 구성
  - Selenium, Dash
  ### 2. travel_time ('travel_time/')
  - 5개의 근무지를 할당받은 경우, 최적 경로 추천 프로젝트
  - Naver Maps API, Geocoding API 활용
  - 캐싱을 통한 연산 속도 및 자원 최적화
  - 자체적인 TSP (Traveling Salesman Problem) 알고리즘 구현
  ### 3. HR_Analytics ('HR_Analytics/') 
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
  ### 4. demo ('demo/') 
  - 더미데이터를 생성하고, 시각화 하는 프로젝트
  - 파견업체에서 기록한 근무 직원들의 근무 내용에 대한 데이터를 상정하고 생성
  - 주요 기술: bootstrap, dash
  - 주요 알고리즘: 가우시안 함수를 사용한 데이터 분포 조절, 직원과 근무 시간, 피드백 점수에 따른 판매량 등 변수를 고려한 독창적인 생성 알고리즘 구현
  ### 5. otour ('otour/')
  - 여행사 데이터를 기반으로, 데이터 분석 및 ML & DL 모델 구현
  - 주요 기능 : 트리맵 시각화(squarify), SVR, GradientBoostingRegressor, Sequential 모델, Adam 옵티마이저
  - 주요 기술 스택:  scikit-learn, TensorFlow/Keras, Optuna, Flask, pandas, numpy, matplotlib, seaborn, plotly, etc.

## 99_archive ('99_archive/')
  ### 1. cua ('cua/')
  - Computer using agent 활용 예제
  - AI가 사용자의 화면을 인식하고, 좌표를 기반으로 마우스 클릭, 키 입력등의 작업을 수행할 수 있도록 하는 프로젝트

  ### 2. DDL ('DDL/')
  - Data Definition Language 의 약자
  - 데이터베이스 스키마를 정의하는 일련의 SQL 명령
  - AI를 통해 DDL 기반의  **Domain(Entity) 클래스**와 **Repository 인터페이스**를 생성

  ### 3. dify ('dify/')
  - Dify 프로젝트
  - Made by Teddynote
  - dify 와 Openwebui를 활용하여 웹 애플리케이션 구현

  ### 6. MCP_example ('MCP_example/')
  - MCP 프로젝트 예제
  - Made by Teddynote
  - smithery 에서 가져온 도구들을 바인딩하는 예제 

### 8. 기타 파일
- `.cursorrules`: cursor 규칙
- `.gitignore`: git 무시 규칙
- `README.md`: 프로젝트 설명
- `.env`: 환경 변수
