# Form Selector 클라이언트 테스트 가이드

## 개요
이 가이드는 Form Selector API의 8가지 양식에 대한 클라이언트 테스트 케이스를 실행하는 방법을 설명합니다.

## 테스트 케이스 파일
- `client_test_cases.json`: 모든 테스트 케이스를 포함한 JSON 파일
- 총 24개의 테스트 케이스 (각 양식당 3개씩)

## 지원하는 양식
1. **연차 신청서** (annual_leave)
2. **야근식대비용 신청서** (dinner_expense)
3. **교통비 신청서** (transportation_expense)
4. **파견 및 출장 보고서** (dispatch_business_trip)
5. **비품/소모품 구입내역서** (inventory_purchase)
6. **구매 품의서** (purchase_approval)
7. **개인경비 사용내역서** (personal_expense)
8. **법인카드 지출내역서** (corporate_card)

## API 엔드포인트
- **URL**: `/api/form-recommendation`
- **메서드**: POST
- **Content-Type**: application/json

## 요청 형식
```json
{
  "input": "자연어 입력 텍스트",
  "drafterId": "기안자ID"
}
```

## 테스트 케이스 예시

### 1. 연차 신청서 테스트 케이스
```json
{
  "case_name": "연차 신청 - 기본 케이스",
  "input": "다음 주 금요일부터 3일간 연차 신청합니다. 7월 4일부터 7월 6일까지 개인 용무로 휴가를 사용하겠습니다.",
  "drafterId": "01240006",
  "expected_form": "annual_leave"
}
```

### 2. 야근식대 테스트 케이스
```json
{
  "case_name": "야근식대 - 기본 케이스",
  "input": "어제 늦게까지 야근했습니다. 서버 점검 작업으로 밤 10시까지 일했고 야근 식대 15000원 신청합니다. 회사에서 치킨 시켜 먹었습니다.",
  "drafterId": "01240006",
  "expected_form": "dinner_expense"
}
```

### 3. 교통비 테스트 케이스
```json
{
  "case_name": "교통비 - 지하철 이용",
  "input": "어제 출장 다녀왔습니다. 강남역에서 여의도역까지 지하철 이용했고 왕복 2900원 사용했습니다. 고객사 미팅 참석이 목적이었습니다.",
  "drafterId": "01240006",
  "expected_form": "transportation_expense"
}
```

## 수동 테스트 방법

### 1. curl을 사용한 테스트
```bash
curl -X POST http://localhost:5000/api/form-recommendation \
  -H "Content-Type: application/json" \
  -d '{
    "input": "다음 주 금요일부터 3일간 연차 신청합니다. 7월 4일부터 7월 6일까지 개인 용무로 휴가를 사용하겠습니다.",
    "drafterId": "01240006"
  }'
```

### 2. PowerShell을 사용한 테스트
```powershell
$body = @{
    "input" = "다음 주 금요일부터 3일간 연차 신청합니다. 7월 4일부터 7월 6일까지 개인 용무로 휴가를 사용하겠습니다."
    "drafterId" = "01240006"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:5000/api/form-recommendation" -Method POST -Body $body -ContentType "application/json"
$response
```

### 3. Python을 사용한 테스트
```python
import requests
import json

# 테스트 케이스 데이터 로드
with open('client_test_cases.json', 'r', encoding='utf-8') as f:
    test_data = json.load(f)

# API 호출 함수
def test_form_recommendation(input_text, drafter_id):
    url = "http://localhost:5000/api/form-recommendation"
    payload = {
        "input": input_text,
        "drafterId": drafter_id
    }
    
    response = requests.post(url, json=payload)
    return response.json()

# 테스트 실행
for form_type, cases in test_data["test_cases"].items():
    print(f"\n=== {form_type} 테스트 ===")
    for case in cases:
        print(f"테스트: {case['case_name']}")
        result = test_form_recommendation(case["input"], case["drafterId"])
        print(f"결과: {result}")
        print("-" * 50)
```

## 예상 응답 형식
```json
{
  "form_type": "annual_leave",
  "keywords": ["연차", "휴가", "3일"],
  "slots": {
    "leave_type": "연차",
    "start_date": "7월 4일",
    "end_date": "7월 6일",
    "duration": "3일",
    "leave_days": "3"
  },
  "html_template": "annual_leave.html",
  "original_input": "다음 주 금요일부터 3일간 연차 신청합니다...",
  "message_to_user": "연차 신청서가 준비되었습니다.",
  "approver_info": {
    "drafterName": "홍길동",
    "drafterDepartment": "개발팀",
    "approvers": [...]
  }
}
```

## 전체 테스트 실행

### 서버 시작
```bash
python main.py
```

### 각 양식별 테스트 케이스 실행
각 양식에 대해 3개씩의 테스트 케이스가 준비되어 있습니다:

1. **연차 신청서**: 기본 케이스, 반차 케이스, 장기 휴가
2. **야근식대**: 기본 케이스, 긴급 작업, 프로젝트 마감
3. **교통비**: 지하철 이용, 택시 이용, 버스+지하철
4. **출장 보고**: 국내 출장, 기술 교육, 프로젝트 점검
5. **비품 구입**: 사무용품, IT 장비, 소모품
6. **구매 승인**: 노트북, 서버 장비, 소프트웨어
7. **개인경비**: 현금 사용, 카드 사용, 혼합 사용
8. **법인카드**: 월 정산, 프로젝트 관련, 출장 관련

## 테스트 검증 포인트
1. **양식 분류 정확도**: 입력된 텍스트가 올바른 양식으로 분류되는지
2. **슬롯 추출 정확도**: 필요한 정보가 올바르게 추출되는지
3. **응답 시간**: API 응답 시간이 적절한지
4. **오류 처리**: 잘못된 입력에 대한 오류 처리가 적절한지
5. **한국어 처리**: 한국어 자연어 처리가 정확한지

## 문제 해결
- **서버 연결 실패**: 서버가 실행 중인지 확인
- **응답 지연**: 네트워크 상태 및 서버 성능 확인
- **분류 오류**: 입력 텍스트가 명확한지 확인
- **슬롯 추출 오류**: 필요한 정보가 입력에 포함되었는지 확인

## 추가 테스트 케이스 작성
새로운 테스트 케이스를 추가하려면 `client_test_cases.json` 파일에 다음 형식으로 추가하세요:

```json
{
  "case_name": "테스트 케이스 이름",
  "input": "자연어 입력 텍스트",
  "drafterId": "기안자ID",
  "expected_form": "예상_양식_타입"
}
``` 