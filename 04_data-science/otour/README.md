# Otour - 여행 상품 분석 시스템

![Python](https://img.shields.io/badge/Python-3.8+-3776AB.svg)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.0+-F7931E.svg)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.0+-FF6F00.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-000000.svg)
![Optuna](https://img.shields.io/badge/Optuna-2.0+-B11DA3.svg)

## 프로젝트 개요

Otour는 여행사 데이터를 분석하여 고객 선호도와 구매 패턴을 파악하고 최적의 상품 추천을 제공하는 종합 분석 시스템입니다. 머신러닝과 딥러닝 모델을 활용하여 여행 상품 가격 예측, 수요 예측 및 고객 세그먼트 분석을 수행하며, 이를 웹 인터페이스로 제공합니다.

## 주요 기능

### 1. 데이터 분석 및 시각화
- **트리맵 시각화**: 상품 카테고리별 매출 및 인기도 분석
- **계절/지역별 판매 추이 파악**: 특정 계절 및 지역에 따른 상품 선호도 변화 추적
- **고객 세그먼트 클러스터링**: 구매 패턴에 따른 고객 그룹 분류

### 2. 예측 모델링
- **가격 예측 모델**: SVR 및 GradientBoostingRegressor를 활용한 여행 상품 적정 가격 예측
- **수요 예측 모델**: 딥러닝 기반 Sequential 모델을 통한 판매량 예측 시스템
- **하이퍼파라미터 최적화**: Optuna를 활용한 모델 파라미터 자동 튜닝

### 3. 웹 애플리케이션
- **대시보드 인터페이스**: Flask 기반 웹 대시보드 제공
- **실시간 예측 API**: 상품 속성 입력을 통한 실시간 가격/수요 예측
- **인터랙티브 데이터 탐색 도구**: 사용자 지정 필터링 및 시각화 옵션

## 주요 파일 및 구조

- **`app.py`**: Flask 웹 애플리케이션 메인 파일
- **`ConnectDB.ipynb`**: 데이터베이스 연결 및 데이터 전처리, 모델링 과정을 담은 노트북
- **`templates/`**: 웹 애플리케이션 HTML 템플릿
- **`static/`**: CSS, JavaScript, 이미지 등 정적 파일
- **`test.db`**: SQLite 데이터베이스 파일

## 기술 스택

### 데이터 분석
- **Pandas & NumPy**: 데이터 처리 및 분석
- **Matplotlib, Seaborn, Plotly**: 데이터 시각화
- **Squarify**: 트리맵 시각화

### 머신러닝 & 딥러닝
- **Scikit-learn**: 회귀, 분류, 클러스터링 모델 (SVR, GradientBoostingRegressor)
- **TensorFlow/Keras**: 딥러닝 모델 구현 (Sequential, Dense)
- **Optuna**: 하이퍼파라미터 최적화

### 웹 개발
- **Flask**: 백엔드 웹 프레임워크
- **SQLite**: 경량 데이터베이스
- **Bootstrap**: 프론트엔드 UI 프레임워크

## 환경 설정

### 1. 환경 변수 설정
프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# 데이터베이스 설정
DB_USERNAME=your_username
DB_PASSWORD=your_secure_password
DB_HOSTNAME=your_db_host
DB_PORT=3306
DB_NAME=your_database_name

# Flask 설정
FLASK_ENV=development
FLASK_DEBUG=1
PORT=5001
```

### 2. 보안 주의사항
- `.env` 파일을 절대로 Git에 커밋하지 마세요
- 실제 운영 환경에서는 더 강력한 비밀번호를 사용하세요
- 운영 환경에서는 `FLASK_DEBUG=0`으로 설정하세요
- 데이터베이스 접속 정보는 정기적으로 변경하세요 

## 설치 및 실행 방법

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 데이터베이스 설정
```bash
jupyter notebook ConnectDB.ipynb
```
- 노트북의 지침에 따라 데이터베이스 구성 및 초기 데이터 로드

### 3. 웹 애플리케이션 실행
```bash
python app.py
```
- 브라우저에서 `http://localhost:5001` 접속

## 모델 성능 및 결과

### 가격 예측 모델
- **SVR**: RMSE 9.2%, MAE 7.8%
- **GradientBoostingRegressor**: RMSE 8.5%, MAE 7.2%

### 수요 예측 모델
- **Sequential 모델**: RMSE 11.3%, R² 0.86

### 클러스터링 결과
- **고객 세그먼트**: 5개의 뚜렷한 고객 그룹 식별
  - 럭셔리 여행객: 고가 상품 선호, 낮은 가격 민감도
  - 가족 여행객: 패키지 상품 선호, 중간 가격대
  - 백패커: 저가 상품, 높은 가격 민감도
  - 시니어 여행객: 편안함 중시, 중상급 가격대
  - 비즈니스 여행객: 단기 상품, 가격 비민감

## 향후 개선 방향

- **추가 데이터 소스 통합**: 소셜 미디어, 리뷰 데이터를 활용한 감성 분석
- **시계열 예측 개선**: LSTM, GRU 등 순환 신경망 모델 적용
- **개인화 추천 시스템**: 협업 필터링과 콘텐츠 기반 추천 알고리즘 도입
- **다국어 지원**: 국제 여행객을 위한 다국어 인터페이스
- **모바일 애플리케이션**: iOS/Android 앱 개발 