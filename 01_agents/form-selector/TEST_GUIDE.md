# 양식 테스트 가이드

## 준비사항
1. 서버가 실행 중인지 확인: `python main.py`
2. 서버 주소: `http://localhost:8000`

## 개별 양식 테스트

### 1. 교통비 신청서
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/form-selector" -Method POST -ContentType "application/json" -InFile "test_transportation.json"
```
**테스트 내용**: 강남역↔여의도역 지하철 왕복, 2900원

### 2. 파견 및 출장 보고서
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/form-selector" -Method POST -ContentType "application/json" -InFile "test_dispatch_trip.json"
```
**테스트 내용**: 부산 출장 5일간, 시스템 구축 프로젝트

### 3. 비품/소모품 구입내역서
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/form-selector" -Method POST -ContentType "application/json" -InFile "test_inventory.json"
```
**테스트 내용**: A4용지, 볼펜, 포스트잇 구매, 총 68,000원

### 4. 구매 품의서
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/form-selector" -Method POST -ContentType "application/json" -InFile "test_purchase_approval.json"
```
**테스트 내용**: 맥북 프로 2대 구매, 총 700만원

### 5. 개인 경비 사용내역서
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/form-selector" -Method POST -ContentType "application/json" -InFile "test_personal_expense.json"
```
**테스트 내용**: 식대, 택시비, 커피 구입, 총 28,000원

### 6. 법인카드 사용 내역서
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/form-selector" -Method POST -ContentType "application/json" -InFile "test_corporate_card.json"
```
**테스트 내용**: 커피, 접대비, 주차비, 총 97,000원

## 전체 테스트 실행
```powershell
.\run_all_tests.ps1
```

## 검증 포인트
1. **양식 분류**: 올바른 양식 타입으로 분류되는가?
2. **슬롯 추출**: 핵심 정보가 정확히 추출되는가?
3. **날짜 파싱**: 상대적 날짜 표현이 정확한 ISO 날짜로 변환되는가?
4. **시간 변환**: 자연어 시간이 HH:MM 형식으로 변환되는가?
5. **HTML 템플릿**: 추출된 정보가 폼 필드에 올바르게 채워지는가?
6. **결재 정보**: 결재라인이 정상적으로 조회되는가?

## 실패 시 확인사항
1. 서버 로그 확인
2. LLM API 키 및 연결 상태 확인
3. 데이터베이스 연결 상태 확인
4. 프롬프트 파일 존재 여부 확인 