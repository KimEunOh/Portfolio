## 프로젝트 구조

## [00_docs/](00_docs/)
- 프로젝트 관련 문서
  - 1. 발표자료 : AI 컨퍼런스 관련 자료
  - 2. 테스트 결과 : 모니터링 관련 자료

## [01_agents/](01_agents/)
### 1. [approval_agent/](01_agents/approval_agent/) (전자결재 처리 통합 에이전트)
- **단일 AI 에이전트를 통해 일반적인 대화형 문의 응대는 물론, 복잡한 전자결재 프로세스 전반을 처리**하는 통합 챗봇 시스템.
- 사용자는 이 에이전트와의 자연어 대화만으로 **결재 요청 시작부터 최종 승인/반려까지의 모든 단계를 원스톱으로 진행** 가능.
- API 연동 및 LangGraph의 상태 기반 워크플로우를 통해 연차 신청과 같은 HR 프로세스의 정보 수집, 검증, 제출 및 상태 추적을 완벽히 자동화하여, **기업 내 결재 업무의 패러다임을 혁신**하고 관련 부서의 효율성을 극대화.
- 주요 기술 스택: 
  - FastAPI, Uvicorn, Jinja2
  - LangChain, LangGraph, OpenAI

### 2. [form-selector/](01_agents/form-selector/) (지능형 양식 추천 및 자동 완성 시스템)
- 사용자의 자연어 요청으로부터 **가장 적합한 전자결재 양식을 지능적으로 분류하고, 내용을 자동으로 완성**해주는 시스템.
- 단순 키워드 매칭을 넘어, **LLM 기반 키워드 추출과 FAISS를 활용한 RAG(Retrieval Augmented Generation) 검색을 결합**하여 양식 분류의 정확도를 극대화.
- 분류된 양식에는 사용자의 요청에서 추출된 핵심 정보(날짜, 사유, 품목 등)가 자동으로 입력되어, **문서 작성 시간 단축 및 오류 감소에 직접적으로 기여**하며, 이는 다양한 부서의 행정 업무 부담을 크게 경감.
- 주요 기술 스택:
  - Python, FastAPI, Uvicorn, HTML, CSS, JavaScript
  - LangChain, OpenAI GPT-4o, Pydantic, FAISS (RAG)
  - python-dateutil, httpx

## [02_LLM/](02_LLM/)
- Large Language Model 관련 프로젝트
### 1. [LLM_local_api/](02_LLM/LLM_local_api/) (RAG 기반 문서 질의응답 시스템)
- 기업 내부의 **PDF 문서(매뉴얼, 기술 문서, 보고서 등)를 지식 베이스로 활용**하여, 사용자가 자연어 질문을 통해 필요한 정보를 신속하고 정확하게 찾을 수 있도록 지원하는 **RAG(Retrieval Augmented Generation) 기반 질의응답 시스템**.
- PDF 내 텍스트뿐만 아니라 **이미지 정보까지 추출 및 통합 분석**하여 멀티모달 컨텍스트를 이해하고, 이를 통해 보다 풍부하고 정확한 답변을 생성.
- FAISS 벡터 DB를 활용한 시맨틱 검색으로 문서 내 **의미 기반의 지능형 검색**을 수행하며, Docker 컨테이너화를 통해 **배포 용이성 및 확장성을 확보**하고 Prometheus/Grafana 기반 모니터링으로 **운영 안정성**을 향상.
- 이는 **기업의 지식 관리 효율화, 정보 접근성 향상, 직원 생산성 증대**에 직접적으로 기여하며, 특히 기술 지원, 연구 개발, 법무 등 **전문 지식 의존 부서의 업무 효율화**에 효과적.
- 주요 기술 스택: 
  - Python, FastAPI, LangChain, FAISS, OpenAI Embeddings, Together AI LLMs
  - PyPDF, pdf2image, Docker, Docker Compose, Prometheus, Grafana

### 2. [socket/](02_LLM/socket/) (WebSocket 기반 실시간 스트리밍 채팅 시스템)
- WebSocket 기술을 활용하여 **대규모 동시 접속 환경에서도 안정적인 실시간 메시지 스트리밍**을 지원하는 고성능 채팅 시스템.
- 다중 채팅방 관리, 사용자 인증 기능을 제공하며, **OpenAI GPT 모델을 통합**하여 AI 기반의 지능형 대화 기능을 구현.
- 단일 서버 내 샤딩, 메시지 배치 처리, 비동기 아키텍처를 통해 **메모리 관리 및 응답 속도를 최적화**하여, **온라인 커뮤니티, 라이브 스트리밍, 고객 지원, 협업 도구** 등 다양한 실시간 소통 서비스의 기반 기술로 활용 가능.
- AI 챗봇 통합은 **사용자 문의 자동 응답, 콘텐츠 추천 등을 통해 서비스 운영 효율화 및 사용자 참여도 증진**에 기여할 잠재력 보유.
- 주요 기술 스택: 
  - Python, FastAPI, WebSocket, SQLAlchemy, Alembic, Bcrypt
  - HTML, CSS, JavaScript, Bootstrap, Jinja2, OpenAI API, Locust

## [03_cv-multimodal/](03_cv-multimodal/)
### 1. [deepfake/](03_cv-multimodal/deepfake/) (CLIP 유사도 기반 Multimodal RAG 검증 기법)
- **딥페이크 탐지 모델의 신뢰도 및 설명 가능성 향상**을 목표로, CLIP과 같은 멀티모달 모델을 활용하여 이미지-텍스트 간 의미 유사도를 분석하고, 이를 RAG 시스템에 통합하여 검증하는 기법을 연구/구현.
- LLaVA, YOLOv8 등을 활용하여 이미지 내 특징을 분석하고 텍스트 설명과 연계하여 딥페이크 의심 영역의 판단 근거를 마련하며, GradCAM++ 등의 시각화 기법을 실험적으로 적용하여 모델 판단의 **시각적 근거를 직관적으로 제시**함으로써 투명성 확보를 시도 (구현상 기술적 한계 직면).
- 이는 **뉴스 미디어, 콘텐츠 플랫폼 등 딥페이크로 인한 피해가 우려되는 산업**에서 AI 탐지 시스템의 신뢰성을 높이고, **설명 가능한 AI(XAI) 연구**에 기여 가능.
- 주요 기술 스택:
  - PyTorch, transformers, together-cli, CLIP, LLaVA, YOLOv8
  - GradCAM++, LayerCAM, EigenGradCAM (실험적)
  - pandas, numpy, captum

### 2. [OCR/](03_cv-multimodal/OCR/) (소매점 상품 정보 OCR 및 데이터 추출 자동화)
- **소매 유통 분야의 상품 정보 관리 자동화**를 위한 시스템으로, 두 가지 OCR 및 데이터 추출 파이프라인(테이블 이미지 CSV 변환, 매장 가격표 자동 인식/정보 추출)을 구현.
- 테이블 형태의 상품 목록 이미지를 CSV로 변환하고, YOLOv5로 매장 내 가격표를 자동 감지 후 상품명, 코드, 가격 등을 추출하여 정형화.
- 다양한 LLM(GPT-4o, o3-mini, Gemini)과 프롬프트 엔지니어링을 활용하여 OCR 데이터의 정확도를 높이고 일관된 구조로 변환함으로써, **상품 정보 디지털화, 수작업 오류 감소, 정보 업데이트 시간 단축**에 기여.
- 이는 **경쟁사 가격 분석, 프로모션 관리, 재고 관리 시스템 연동** 등 소매업 비즈니스 인텔리전스를 지원.
- 주요 기술 스택: 
  - Python, YOLOv5, PyTorch, ultralytics, OpenCV, Pillow, torchvision
  - Upstage OCR, OpenAI GPT-4o, o3-mini, Google Gemini, LangChain

## [04_data-science/](04_data-science/)
- 데이터 전처리, 분석, 시각화 및 예측 모델 구현을 통해 비즈니스 인사이트를 도출하고 의사결정을 지원하는 프로젝트 모음.

### 1. [vacation/](04_data-science/vacation/) (기업용 휴가 관리 대시보드)
- Selenium을 활용하여 **사내 전자결재 시스템의 휴가 신청 데이터를 자동으로 크롤링**하고, Dash 및 Plotly Express를 사용하여 **부서별/유형별 휴가 사용 현황을 실시간으로 시각화**하는 대시보드.
- 휴가 사용 패턴 분석, 잔여 휴가 추적, 휴가 소진율 모니터링 기능을 통해 **인사팀의 효율적인 인력 운영 및 휴가 관리 정책 수립을 지원**. Flask-Caching을 적용하여 대규모 데이터 조회 시에도 빠른 응답 속도를 보장.
- 주요 기술 스택: Python, Dash, Plotly Express, Pandas, Selenium, Flask-Caching, Bootstrap

### 2. [travel_time/](04_data-science/travel_time/) (다중 방문지 최적 경로 추천 시스템)
- **외근이 잦은 직원(예: 영업, 배송, 현장 서비스)이 다수의 근무지를 방문해야 할 때, 이동 시간 및 비용을 최소화하는 최적 경로를 추천**하는 시스템. 
- Naver Maps API (Geocoding, Directions)를 연동하여 실제 도로망 기반의 거리/시간을 계산하고, 자체 구현한 TSP(Traveling Salesman Problem) 해결 알고리즘(완전 탐색 및 휴리스틱)을 적용. 
- 경로 결과는 Folium을 통해 인터랙티브 지도로 시각화되며, 캐싱 시스템을 통해 반복적인 API 호출을 최소화하여 **운영 효율성 증대 및 유류비 등 비용 절감**에 기여.
- 주요 기술 스택: Python, Pandas, NumPy, Folium, Naver Maps API, TSP 알고리즘

### 3. [HR_Analytics/](04_data-science/HR_Analytics/) (HR 분석: 퇴사 예측 및 지역 상권 분석)
- **1) 직원 퇴사 예측 모델**: IBM HR 데이터를 활용, Scikit-learn 기반의 머신러닝 모델(Random Forest, XGBoost 등)과 Hyperopt를 이용한 하이퍼파라미터 최적화를 통해 **직원 이탈 가능성을 예측**. SHAP 값으로 모델 판단 근거를 시각화하여 **HR팀이 선제적으로 인재 유출 방지 전략을 수립**하는 데 필요한 인사이트를 제공. (주요 퇴사 영향 요인: 초과근무, 직무 만족도, 근속년수 등)
- **2) 대전 지역 상권 분석**: 신용카드 매출 데이터와 공공 데이터를 결합, GeoPandas와 Folium을 사용하여 **자치구별/업종별 매출 패턴 및 상권 잠재력을 시각적으로 분석**. 이는 **신규 출점 전략 수립, 마케팅 지역 선정 등 소상공인 및 기업의 의사결정을 지원**.
- 주요 기술 스택: Python, Pandas, Scikit-learn, Hyperopt, SHAP, GeoPandas, Folium, Matplotlib, Seaborn, Plotly

### 4. [demo/](04_data-science/demo/) (파견 근무 데이터 시뮬레이션 및 시각화 대시보드)
- **파견 인력 운영 최적화를 위한 의사결정 지원**을 목표로, 현실적인 근무 패턴(가우시안 분포 기반 근무 시간/성과, 직원 속성 연관)을 반영한 더미데이터를 생성하고, 이를 Dash와 Plotly 기반의 반응형 웹 대시보드로 시각화.
- 생성된 데이터는 판매량, 고객 만족도, 처리 시간 등 다양한 KPI를 포함하며, 대시보드를 통해 **시간대/요일별 성과 패턴 분석, 인력 배치 효율성 검토, 성과 예측 모델링의 기초 자료 확보** 등 인력 관리 전략 수립에 활용될 수 있는 통찰을 제공.
- 주요 기술 스택: Python, Pandas, NumPy, SciPy, Dash, Plotly, Bootstrap

### 5. [otour/](04_data-science/otour/) (여행 상품 분석 및 예측 시스템)
- **여행사의 상품 기획 및 마케팅 전략 수립을 지원**하기 위해, 여행사 데이터를 분석하여 고객 선호도, 구매 패턴, 상품 가격 및 수요를 예측하는 종합 분석 시스템.
- 트리맵 시각화(Squarify)로 상품 카테고리별 매출/인기도를 분석하고, Scikit-learn(SVR, GradientBoostingRegressor) 및 TensorFlow/Keras(Sequential 모델)를 활용하여 **여행 상품의 적정 가격과 판매량을 예측**. Optuna로 모델 하이퍼파라미터를 최적화하며, Flask 기반 웹 대시보드를 통해 분석 결과 및 실시간 예측 기능을 제공.
- 주요 기술 스택: Python, Pandas, Scikit-learn, TensorFlow/Keras, Optuna, Flask, Matplotlib, Seaborn, Plotly, Squarify, SQLite

## [99_archive/](99_archive/)
### 1. [cua/](99_archive/cua/)
- AI가 사용자 화면을 인식하여 마우스 클릭, 키 입력 등 GUI 자동화 작업을 수행하는 **Computer Using Agent (CUA) 기술 활용 예제**. RPA(Robotic Process Automation)나 사용자 인터페이스 테스트 자동화 분야의 기초 연구.

### 2. [DDL/](99_archive/DDL/)
- AI를 활용하여 데이터베이스 스키마(DDL)로부터 **도메인(Entity) 클래스 및 Repository 인터페이스 코드를 자동 생성**하는 실험적 프로젝트. (내부 민감 정보 포함으로 현재는 주요 코드 비공개)

### 3. [dify/](99_archive/dify/)
- 오픈소스 LLM 애플리케이션 개발 플랫폼 **Dify와 OpenWebUI를 연동하여 웹 기반 AI 애플리케이션을 구축**하는 활용 사례 연구. (Teddynote님의 가이드를 참고하여 진행)

### 4. [MCP_example/](99_archive/MCP_example/)
- LangChain의 에이전트 기능 확장 라이브러리 또는 프레임워크(예: Smithery)에서 제공하는 **다양한 외부 도구(tools)를 커스텀 에이전트에 통합(바인딩)하고 활용하는 방법을 실험**한 예제 코드. (Teddynote님의 자료 참고)

### 8. 기타 파일
- `.cursorrules`: cursor 규칙
- `.gitignore`: git 무시 규칙
- `README.md`: 프로젝트 설명
- `.env`: 환경 변수
