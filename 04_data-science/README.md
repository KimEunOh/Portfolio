# /c:/keo/salesup 디렉토리 구조 (최신)

## 1. 최상위 파일
1. **README.md** (약 76줄)  
   - 저장소 소개

2. **cache_progress.npy** (289B, 2줄)  
   - NumPy 캐시 진행 상황 기록

---

## 2. 폴더 구조

- **HR_Analytics/**  
  - 인사(HR) 분석 프로젝트 폴더  
  - 주요 파일 및 폴더  
    - `readme.txt`: 퇴사 예측, 대전 상권 분석 내용 요약  
    - `HR_info.txt`: 데이터 변수 설명  
    - `HR_Analytics.csv`, `HR_hyperOPT.ipynb`, `HR_Analytics.ipynb` 등  
    - `daejeon_visual.ipynb`: 대전 상권 분석  
  - 퇴사 예측(IBM HR 데이터), 대전 지역 매출 분석 포함

- **.vscode/**  
  - VSCode 설정 폴더  
    - `settings.json`: Java 빌드 구성 (3줄)

- **chat/**  
  - 채팅/대화 관련 기능 폴더 (세부 미확인)

- **travel_time/**  
  - 출장/여행 시간 분석 가능성 있음 (세부 미확인)

- **vacation/**  
  - 휴가 관리나 일정 분석 추정 (세부 미확인)

- **cache/**  
  - 캐시 데이터 폴더 (세부 미확인)

- **cache-directory/**  
  - 추가 캐시 폴더 (세부 미확인)

- **demo/**  
  - 예제 코드 및 테스트용 프로젝트 폴더  
  - 주요 파일 및 폴더  
    - `readme.txt`: 더미데이터 생성, Dash 웹 시각화 내용  
      - `dummy_data.ipynb`: 더미데이터 생성  
      - `final_schedule_data_with_metrics2.csv`: 최종 더미데이터  
      - `visual_app/`: Dash 시각화 앱  
        - `main.py`: 웹 앱 메인 실행  
        - `data_processing.py`: 데이터 로드/전처리 로직
        - `__pycache__/`, `assets/`, `page/` 등

---

## 3. 하위 코드 파일 주요 기능
- `debug_data.py`: 현재 디렉토리 및 `data` 폴더 구조를 점검하고, 엑셀 파일 내용을 확인하는 디버그용 스크립트.  
- `data_processing.py` (demo/visual_app 내부): 데이터 로드를 담당하고, 변경 사항 감지 기능(`watch_file()`) 존재.

---

## 4. 정리
- `.vscode`, `HR_Analytics`, `demo` 폴더는 이미 주요 파일 분석 완료.
- `.git`, `chat`, `travel_time`, `vacation`, `cache`, `cache-directory` 폴더는 여전히 세부 구조 미확인 상태.
