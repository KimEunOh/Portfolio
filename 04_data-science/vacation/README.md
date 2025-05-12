# 휴가 관리 대시보드

## 프로젝트 소개
이 프로젝트는 Dash를 활용한 실시간 휴가 관리 대시보드입니다. 전자결재 시스템의 휴가 신청 데이터를 자동으로 수집하고, 부서별/유형별 휴가 사용 현황을 시각화하며, 휴가 신청 및 승인 상태를 실시간으로 모니터링할 수 있습니다. Flask-Caching을 활용한 성능 최적화로 대규모 데이터도 원활하게 처리합니다.

## 주요 기능
### 데이터 수집 (`vacation_crawling.ipynb`)
- 전자결재 시스템 자동 로그인 및 데이터 크롤링
- 문서 번호 기반 중복 제거
- 증분 업데이트 (신규 문서만 수집)
- 자동화된 주기적 데이터 수집

### 대시보드 (`vacation_dash.py`)
- **휴가 현황 분석**
  - 부서별 휴가 사용량 시각화
  - 휴가 유형별 분포 (연차/반차/특별휴가)
  - 월별/분기별 사용 추이
  - 요일별 휴가 사용 패턴
- **실시간 모니터링**
  - 승인 상태별 휴가 현황
  - 잔여 휴가 포인트 추적
  - 부서별 휴가 소진율
- **데이터 필터링**
  - 부서/기간/휴가 유형별 필터
  - 동적 날짜 범위 선택
  - 다중 조건 검색

## 기술 스택
- **웹 프레임워크**
  - Dash 2.14.1
  - Flask
  - dash-bootstrap-components
- **데이터 처리**
  - pandas
  - numpy
- **시각화**
  - plotly.express
  - dash_table
- **성능 최적화**
  - Flask-Caching
  - 파일 시스템 캐싱
- **데이터 수집**
  - Selenium
  - BeautifulSoup4
- **스타일링**
  - Bootstrap (MINTY 테마)

## 설치 방법
1. 저장소 클론
```bash
git clone <repository_url>
cd vacation
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

## 프로젝트 구조
```
vacation/
├── assets/                    # 정적 파일 디렉토리
│   ├── custom.css           # 커스텀 스타일시트
│   └── n2.png              # 로고 이미지
├── data/                     # 데이터 디렉토리
│   └── 2024_vacation.csv   # 휴가 데이터
├── cache-directory/         # 캐시 저장소
├── vacation_crawling.ipynb  # 데이터 수집 스크립트
├── vacation_dash.py        # 대시보드 메인 애플리케이션
└── README.md               # 프로젝트 설명
```

## 사용 방법
1. 데이터 수집:
```python
# vacation_crawling.ipynb 실행
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd

# 크롤러 설정 및 실행
driver = webdriver.Chrome()
crawler = VacationCrawler(driver)
crawler.start()
```

2. 대시보드 실행:
```bash
python vacation_dash.py
```
- 기본 URL: http://localhost:8050
- 자동 리로드: 활성화됨
- 캐시 갱신 주기: 5분

## 주요 기능 상세
### 1. 데이터 수집 (`vacation_crawling.ipynb`)
- 자동 로그인 및 세션 관리
- 문서 번호 기반 증분 업데이트
- 에러 처리 및 재시도 메커니즘
- 데이터 정제 및 전처리
  - 날짜 형식 표준화
  - 부서명 정규화
  - 포인트 계산 로직

### 2. 대시보드 (`vacation_dash.py`)
- **데이터 처리**
  - 실시간 데이터 로딩
  - 캐시 기반 성능 최적화
  - 동적 데이터 필터링
- **시각화 컴포넌트**
  - 월별 사용량 막대 그래프
  - 휴가 유형별 파이 차트
  - 부서별 분포 히트맵
  - 상세 데이터 테이블
- **인터랙티브 기능**
  - 날짜 범위 슬라이더
  - 부서/유형 드롭다운
  - 데이터 정렬 및 필터링

## 성능 최적화
- **캐싱 전략**
  - 파일 시스템 기반 캐싱
  - 5분 주기 자동 갱신
  - 메모리 사용량 최적화
- **데이터 처리**
  - 증분 업데이트
  - 효율적인 데이터 구조
  - 병렬 처리 지원

## 보안
- 민감 정보 환경 변수 처리
- 세션 관리 및 인증
- 접근 권한 제어

## 유지보수
- 로그 기반 모니터링
- 에러 처리 및 복구
- 정기적 데이터 백업

## 참고 사항
- 데이터는 일 1회 자동 업데이트
- 캐시는 5분마다 갱신
- 브라우저 캐시 삭제 시 데이터 새로고침 필요
- 시스템 요구사항: Python 3.8+, 2GB RAM 