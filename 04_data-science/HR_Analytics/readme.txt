퇴사 예측 : IBM HR Analytics Employee Attrition & Performance 데이터를 활용해 퇴사 여부에 영향을 미치는 요인들을 분석하고 있습니다.  
- **HR_Analytics.csv** : 퇴사 예측 모델에 사용되는 핵심 HR 데이터  
- **HR_info.txt** : 나이, 직급, 근속연수 등 데이터 변수 설명  
- **HR_Analytics.ipynb** : PCA 등 기본 모델링 및 결과 시각화  
- **HR_hyperOPT.ipynb** : Scikit-learn 기반의 하이퍼파라미터 최적화 수행  
- **HR_Analytics.txt** : 분석 주제, KPI 지표 목록  
- **HR_Analytics.html** : PCA 결과 웹 시각화  

---

대전 상권 분석 : 대전광역시 자치구별 신용카드 매출 데이터를 분석하여 지역별 매출 패턴을 파악하고 있습니다.  
- **sig.shp**, **sig.dbf**, **sig.shx** : 행정지도 파일(GeoPandas 등 GIS 라이브러리를 통해 지도 시각화)  
- **daejeon_visual.ipynb** : 상권 데이터 로딩, 지도 기반 시각화, 구·카테고리별 매출 비교 분석  

---

### 사용된 기술 스택
1. **Python 3**  
2. **Pandas**, **NumPy**를 통한 데이터 전처리  
3. **Scikit-learn** 기반 모델링 및 Hyperparameter Tuning  
4. **Matplotlib/Seaborn**으로 시각적 결과 확인  
5. **GeoPandas/folium** 등 GIS 라이브러리로 지도 시각화  
6. **dash**를 통한 대시보드 구성성
---

위 분석 프로젝트들은 인사·경영 의사결정 및 지역 상권 분석에 직접 활용될 수 있도록,  
다양한 시각화 결과와 요약 지표를 제공하는 것을 목표로 합니다.