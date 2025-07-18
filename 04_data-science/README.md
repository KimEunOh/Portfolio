# 데이터 사이언스 프로젝트 포트폴리오

![Python](https://img.shields.io/badge/Python-3.8+-3776AB.svg)
![Pandas](https://img.shields.io/badge/Pandas-1.3+-150458.svg)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.0+-F7931E.svg)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.0+-FF6F00.svg)
![Dash](https://img.shields.io/badge/Dash-2.0+-008DE4.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-000000.svg)

이 디렉토리는 데이터 분석, 머신러닝 및 시각화 프로젝트를 포함하는 데이터 사이언스 포트폴리오입니다. 각 프로젝트는 실무에서 발생할 수 있는 다양한 문제를 해결하기 위한 접근 방식과 기술적 역량을 보여줍니다.

## 목차
1. [HR_Analytics - 퇴사 예측 및 지역 상권 분석](#1-hr_analytics---퇴사-예측-및-지역-상권-분석)
2. [Travel_Time - 최적 경로 추천 시스템](#2-travel_time---최적-경로-추천-시스템)
3. [Vacation - 휴가 관리 대시보드](#3-vacation---휴가-관리-대시보드)
4. [Demo - 더미데이터 생성 및 시각화](#4-demo---더미데이터-생성-및-시각화)
5. [Otour - 여행 상품 분석 시스템](#5-otour---여행-상품-분석-시스템)

---

## 1. HR_Analytics - 퇴사 예측 및 지역 상권 분석

### 프로젝트 개요
이 프로젝트는 두 개의 핵심 분석으로 구성되어 있습니다:

1. **퇴사 예측 모델**: IBM HR Analytics Employee Attrition & Performance 데이터셋을 활용하여 직원 이탈을 예측하는 머신러닝 모델 개발
2. **대전 상권 분석**: 대전광역시 자치구별 신용카드 매출 데이터를 분석하여 지역별 상권 패턴 파악

### 주요 기능
- **데이터 전처리 및 탐색적 분석**
  - 결측치 처리, 이상치 탐지, 특성 공학
  - 상관관계 분석 및 변수 중요도 시각화
  - 차원 축소(PCA) 및 특성 분석

- **머신러닝 모델링**
  - Hyperopt를 활용한 하이퍼파라미터 최적화
  - 앙상블 기법 적용(Random Forest, Gradient Boosting)
  - SHAP 값을 통한 모델 해석 및 의사결정 근거 시각화

- **지리 데이터 시각화**
  - GeoPandas 및 Folium을 활용한 지도 기반 시각화
  - 구별, 카테고리별 매출 패턴 분석
  - 인터랙티브 맵 생성으로 지역별 상권 특성 표현

### 기술 스택
- **데이터 처리**: Pandas, NumPy
- **모델링**: Scikit-learn, Hyperopt
- **시각화**: Matplotlib, Seaborn, Plotly
- **지리 시각화**: GeoPandas, Folium
- **대시보드**: Dash

### 결과물 및 성과
- 직원 이탈 예측 모델 정확도 85% 달성
- ROC-AUC 0.92, F1-Score 0.88 확보
- 이탈 가능성이 높은 직원 특성 파악을 통한 HR 정책 제안
- 대전 지역 중 매출 성장 잠재력이 높은 상권 식별

---

## 2. Travel_Time - 최적 경로 추천 시스템

### 프로젝트 개요
다수의 근무지를 방문해야 하는 직원들에게 최적의 이동 경로를 추천하는 시스템입니다. 외근 직원의 이동 효율성을 극대화하기 위해 여러 지점 간 최단 경로를 찾는 TSP(Traveling Salesman Problem) 알고리즘을 구현했습니다.

### 주요 기능
- **위치 데이터 관리**
  - 지점 주소를 좌표로 변환(Geocoding)
  - 좌표 데이터 캐싱으로 API 호출 최소화

- **거리 행렬 계산**
  - Naver Maps API를 활용한 실제 이동 거리 및 시간 계산
  - 행렬 연산 최적화로 계산 속도 향상

- **최적 경로 알고리즘**
  - 자체 개발한 TSP 알고리즘 구현
  - 출발지 기준 다양한 방문 조합 평가

- **결과 시각화**
  - 지도 상 최적 경로 표시
  - 이동 시간 및 거리 정보 제공

### 기술 스택
- **API**: Naver Maps API, Geocoding API
- **데이터 처리**: Pandas, NumPy
- **알고리즘**: 커스텀 TSP 알고리즘
- **캐싱**: 파일 기반 캐싱 시스템
- **시각화**: Folium, Matplotlib

### 결과물 및 성과
- 일일 5개 지점 방문 시 평균 이동 시간 20% 단축
- API 호출 90% 감소로 비용 절감
- 직관적인 경로 시각화로 사용자 경험 개선

---

## 3. Vacation - 휴가 관리 대시보드

### 프로젝트 개요
전자결재 시스템의 휴가 신청 데이터를 자동으로 수집하고 분석하는 대시보드입니다. 부서별/유형별 휴가 사용 현황을 실시간으로 모니터링하고 승인 상태를 추적하여 효율적인 인력 운영을 지원합니다.

### 주요 기능
- **데이터 수집 자동화**
  - Selenium을 활용한 전자결재 시스템 크롤링
  - 문서 번호 기반 중복 제거 및 증분 업데이트
  
- **실시간 대시보드**
  - 부서별 휴가 사용량 시각화
  - 휴가 유형별 분포(연차/반차/특별휴가)
  - 월별/분기별 사용 추이 및 요일별 패턴
  
- **필터링 및 검색**
  - 부서/기간/휴가 유형별 필터
  - 동적 날짜 범위 선택
  - 다중 조건 검색

- **성능 최적화**
  - Flask-Caching을 통한 데이터 캐싱
  - 5분 주기 자동 갱신

### 기술 스택
- **웹 프레임워크**: Dash, Flask
- **데이터 수집**: Selenium, BeautifulSoup4
- **데이터 처리**: Pandas, NumPy
- **시각화**: Plotly Express, Dash Table
- **스타일링**: Bootstrap (MINTY 테마)
- **성능 최적화**: Flask-Caching

### 결과물 및 성과
- 데이터 수집 및 분석 시간 90% 단축
- 부서별 휴가 사용 패턴 파악으로 인력 운영 효율화
- 휴가 승인 프로세스 모니터링 개선

---

## 4. Demo - 더미데이터 생성 및 시각화

### 프로젝트 개요
파견 직원들의 근무 데이터를 시뮬레이션하고 시각화하는 프로젝트입니다. 현실적인 근무 패턴을 반영한 더미데이터를 생성하고 이를 웹 기반 대시보드로 시각화하여 인력 운영 최적화에 활용할 수 있는 통찰을 제공합니다.

### 주요 기능
- **더미데이터 생성**
  - 가우시안 분포를 활용한 현실적인 데이터 생성
  - 직원 속성과 성과 지표 간 관계 모델링
  - 시간대별, 요일별 패턴 반영

- **대시보드 구현**
  - Bootstrap 기반 반응형 웹 인터페이스
  - 실시간 데이터 필터링 및 정렬
  - 다양한 시각화 차트(막대, 선, 파이, 히트맵)

- **분석 기능**
  - 성과 지표 상관관계 분석
  - 근무 패턴 효율성 평가
  - 피크 타임 인력 배치 최적화

### 기술 스택
- **데이터 생성**: Pandas, NumPy, SciPy
- **웹 대시보드**: Dash, Flask
- **UI 프레임워크**: Bootstrap
- **시각화**: Plotly
- **데이터 관리**: SQLite

### 결과물 및 성과
- 10,000+ 레코드의 현실적인 근무 데이터셋 생성
- 직관적인 대시보드로 복잡한 데이터 패턴 시각화
- 인력 배치 시뮬레이션 기반 의사결정 지원

---

## 5. Otour - 여행 상품 분석 시스템

### 프로젝트 개요
여행사 데이터를 분석하여 고객 선호도와 구매 패턴을 파악하고 최적의 상품 추천을 제공하는 시스템입니다. 머신러닝과 딥러닝 모델을 활용하여 여행 상품 가격 예측 및 고객 세그먼트 분석을 수행합니다.

### 주요 기능
- **데이터 분석 및 시각화**
  - 트리맵 시각화를 통한 상품 카테고리 분석
  - 계절별, 지역별 판매 추이 파악
  - 고객 세그먼트 클러스터링

- **예측 모델링**
  - SVR 및 GradientBoostingRegressor를 통한 가격 예측
  - Sequential 모델(TensorFlow/Keras)을 활용한 수요 예측
  - Adam 옵티마이저 적용 딥러닝 모델

- **웹 애플리케이션**
  - Flask 기반 분석 결과 제공 인터페이스
  - 대화형 데이터 탐색 도구
  - 실시간 예측 API

### 기술 스택
- **데이터 분석**: Pandas, NumPy
- **머신러닝**: Scikit-learn(SVR, GradientBoostingRegressor)
- **딥러닝**: TensorFlow/Keras
- **하이퍼파라미터 최적화**: Optuna
- **웹 서버**: Flask
- **시각화**: Matplotlib, Seaborn, Plotly, Squarify

### 결과물 및 성과
- 고객 세그먼트 기반 맞춤형 상품 추천 시스템 구축
- 트렌드 분석을 통한 신규 상품 기획 지원

---

## 기술 역량 요약

### 프로그래밍 언어
- **Python**: 데이터 처리, 분석, 모델링, 웹 애플리케이션 개발

### 데이터 처리 및 분석
- **Pandas & NumPy**: 대용량 데이터 처리 및 분석
- **SciPy**: 통계 분석 및 과학적 컴퓨팅

### 머신러닝 & 딥러닝
- **Scikit-learn**: 분류, 회귀, 클러스터링 모델
- **TensorFlow & Keras**: 딥러닝 모델 구현
- **Hyperopt & Optuna**: 하이퍼파라미터 최적화

### 시각화
- **Matplotlib & Seaborn**: 정적 시각화
- **Plotly & Dash**: 인터랙티브 시각화 및 대시보드
- **GeoPandas & Folium**: 지리 데이터 시각화
- **Squarify**: 트리맵 시각화

### 웹 개발
- **Flask**: 백엔드 API 및 웹 서버
- **Dash**: 데이터 대시보드 구현
- **Bootstrap**: 반응형 웹 디자인

### 데이터 수집
- **Selenium & BeautifulSoup**: 웹 크롤링 및 스크래핑
- **API 연동**: Naver Maps API, Geocoding API

### 데이터베이스
- **SQLite**: 경량 데이터베이스 관리

## 결론

이 포트폴리오는 데이터 수집부터 전처리, 모델링, 시각화, 웹 애플리케이션 개발까지 데이터 사이언스의 전체 파이프라인을 다루는 종합적인 역량을 보여줍니다. 각 프로젝트는 실제 비즈니스 문제를 해결하기 위한 실용적인 접근 방식을 담고 있으며, 다양한 기술 스택을 활용하여 효과적인 솔루션을 제공합니다.
