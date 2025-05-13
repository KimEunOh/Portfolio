# HR_Analytics - 퇴사 예측 및 지역 상권 분석

![Python](https://img.shields.io/badge/Python-3.8+-3776AB.svg)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.0+-F7931E.svg)
![GeoPandas](https://img.shields.io/badge/GeoPandas-0.10+-1A73E8.svg)
![Hyperopt](https://img.shields.io/badge/Hyperopt-0.2+-FF9E0F.svg)
![SHAP](https://img.shields.io/badge/SHAP-0.4+-00BFFF.svg)

## 프로젝트 개요

이 프로젝트는 두 가지 주요 분석을 포함하고 있습니다:

1. **퇴사 예측 모델**: IBM HR Analytics Employee Attrition & Performance 데이터셋을 활용해 직원 이탈을 예측하는 머신러닝 모델을 개발하여 HR 팀의 의사결정을 지원합니다.

2. **대전 상권 분석**: 대전광역시 자치구별 신용카드 매출 데이터를 분석하여 지역별 상권 패턴을 파악하고 매출 성장 잠재력이 높은 지역을 식별합니다.

## 1. 퇴사 예측 모델

### 데이터셋
- **IBM HR Analytics Employee Attrition & Performance**
- **특성 수**: 35개 (연령, 직급, 근속연수, 업무만족도, 월소득 등)
- **타겟 변수**: Attrition (Yes/No)
- **설명 파일**: `HR_info.txt`에 데이터 변수 설명 포함

### 분석 방법

#### 1) 데이터 전처리 및 탐색
- 결측치 처리 및 이상치 탐지
- 범주형 변수 인코딩 (One-Hot, Label 등)
- 상관관계 분석 및 다중공선성 확인
- 특성 공학 및 스케일링

#### 2) 모델링 및 평가
- 다양한 분류 모델 비교 (Random Forest, Gradient Boosting, XGBoost 등)
- Hyperopt를 활용한 하이퍼파라미터 최적화
- 교차 검증을 통한 모델 안정성 평가
- 주요 성능 지표: 정확도, ROC-AUC, F1-Score

#### 3) 모델 해석
- 특성 중요도 분석
- SHAP(SHapley Additive exPlanations) 값을 활용한 모델 판단 근거 시각화
- 퇴사 위험이 높은 직원 프로필 도출

### 결과 및 인사이트
- 모델 성능: 정확도 85%, ROC-AUC 0.92, F1-Score 0.88
- 퇴사에 영향을 미치는 주요 요인:
  1. 초과근무 시간
  2. 직무 만족도
  3. 근속연수
  4. 월간 수입
  5. 직급 및 승진 간격
- 퇴사 위험군 직원 특성 발견:
  - 입사 2-5년차 중간 직급 직원
  - 높은 초과근무 시간과 낮은 급여 상승률
  - 낮은 직무 만족도 및 환경 만족도

## 2. 대전 상권 분석

### 데이터셋
- **대전광역시 자치구별 신용카드(KB국민카드) 매출액**: 구별, 업종별 매출 데이터
- **국세청 사업자현황 100대 생활업종**: 업종별 사업체 수 및 분포 데이터
- **행정구역 지리정보**: `sig.shp`, `sig.dbf`, `sig.shx` 파일

### 분석 방법

#### 1) 지리정보 시각화
- GeoPandas를 활용한 행정구역 지도 구현
- 구별 매출 데이터 맵핑
- Folium을 활용한 인터랙티브 맵 생성

#### 2) 매출 패턴 분석
- 구별 매출 규모 및 성장률 비교
- 업종별 매출 분포 및 트렌드 분석
- 인구통계 데이터 연계 분석

#### 3) 상권 잠재력 평가
- 매출/인구 비율 분석
- 업종 다양성 지수 계산
- 성장률 기반 잠재 상권 식별

### 결과 및 인사이트
- 유성구와 서구의 상업 중심지 역할 확인
- 업종별 분포: 요식업(28%), 소매업(22%), 생활서비스(18%)
- 동구 지역의 높은 성장 잠재력 발견
- 중구의 전통 상권 쇠퇴 현상 확인
- 업종 다양성이 높은 상권의 안정적 매출 패턴 확인

## 주요 파일 설명

### 퇴사 예측 관련 파일
- **`HR_Analytics.csv`**: 퇴사 예측 모델에 사용된 핵심 HR 데이터
- **`HR_info.txt`**: 데이터 변수 설명 (나이, 직급, 근속연수 등)
- **`HR_Analytics.ipynb`**: PCA 등 기본 모델링 및 결과 시각화
- **`HR_hyperOPT.ipynb`**: Scikit-learn 기반의 하이퍼파라미터 최적화 수행
- **`HR_Analytics.txt`**: 분석 주제, KPI 지표 목록
- **`HR_Analytics.html`**: PCA 결과 웹 시각화

### 대전 상권 분석 관련 파일
- **`sig.shp`, `sig.dbf`, `sig.shx`**: 행정지도 파일(GeoPandas 등 GIS 라이브러리 용)
- **`daejeon_visual.ipynb`**: 상권 데이터 로딩, 지도 기반 시각화, 구·카테고리별 매출 비교 분석
- **`대전광역시_자치구별 신용카드(KB국민카드) 매출액_20200731.csv`**: 원본 매출 데이터
- **`국세청_사업자현황_100대 생활업종_20240531.csv`**: 업종 분포 데이터
- **`map_with_pie_charts.html`**: 파이 차트가 포함된 인터랙티브 맵
- **`map_with_markers.html`**: 마커가 포함된 인터랙티브 맵

## 기술 스택

### 데이터 처리 및 분석
- **Pandas/NumPy**: 데이터 전처리 및 분석
- **Scikit-learn**: 머신러닝 모델 구현

### 모델 최적화 및 평가
- **Hyperopt**: 하이퍼파라미터 최적화
- **SHAP**: 모델 해석 및 특성 중요도 시각화

### 지리 데이터 시각화
- **GeoPandas**: 지리 정보 처리
- **Folium**: 인터랙티브 맵 생성

### 일반 시각화
- **Matplotlib/Seaborn**: 정적 시각화
- **Plotly**: 인터랙티브 차트

## 실행 방법

1. 데이터 전처리 및 기본 모델링:
```bash
jupyter notebook HR_Analytics.ipynb
```

2. 하이퍼파라미터 최적화:
```bash
jupyter notebook HR_hyperOPT.ipynb
```

3. 대전 상권 분석:
```bash
jupyter notebook daejeon_visual.ipynb
```

## 향후 개선 방향
- 추가 외부 데이터 통합 (산업 동향, 경제 지표)
- 시계열 예측 모델 도입으로 미래 퇴사율 예측
- 상권 분석에 인구 이동 및 교통 데이터 추가
- 머신러닝 기반 상권 성공 가능성 예측 모델 개발 