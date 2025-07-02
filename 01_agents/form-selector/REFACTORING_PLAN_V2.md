# 📋 Form Selector 리팩토링 계획 V2

## 🎯 개요
여러 양식 지원 과정에서 `service.py`(2025줄)와 `index.html`의 JavaScript 코드가 과도하게 길어져 유지보수성과 가독성이 저하되었습니다. 이 문서는 체계적인 리팩토링 방안을 제시합니다.

## 🚨 현재 문제점 분석

### 1. service.py 문제점
- **`fill_slots_in_template` 함수**: 500+ 줄, 모든 양식의 처리 로직이 하나의 함수에 집중
- **변환 함수 중복**: 8개 양식별 `_convert_*_to_payload` 함수들이 유사한 구조 반복
- **날짜 처리 로직**: 여러 곳에 산재된 날짜 파싱 및 변환 코드
- **아이템 처리 로직**: 각 양식마다 개별 HTML 필드 분해 로직 중복
- **단일 책임 원칙 위배**: 하나의 모듈이 너무 많은 기능 담당

### 2. index.html JavaScript 문제점
- **Processor 함수 길이**: 각 양식당 50-100줄의 유사한 로직
- **필드 수집 로직 중복**: `getElementValueOrSlotFunc` 반복 호출
- **검증 로직 중복**: 각 양식마다 유사한 필수값 검증
- **데이터 변환 로직 중복**: 숫자 변환, 배열 생성 등

## 🏗️ 리팩토링 전략

### Phase 1: service.py 모듈 분리

#### 1.1 새로운 모듈 구조
```
form_selector/
├── service.py                    # 메인 서비스 (분류, 조회)
├── processors/                   # 양식별 처리기
│   ├── __init__.py
│   ├── base_processor.py         # 기본 처리기 클래스
│   ├── annual_leave_processor.py
│   ├── dinner_expense_processor.py
│   ├── transportation_processor.py
│   ├── dispatch_report_processor.py
│   ├── inventory_processor.py
│   ├── purchase_approval_processor.py
│   ├── personal_expense_processor.py
│   └── corporate_card_processor.py
├── converters/                   # 데이터 변환기
│   ├── __init__.py
│   ├── base_converter.py         # 기본 변환기 클래스
│   ├── date_converter.py         # 날짜 변환 전담
│   ├── item_converter.py         # 아이템 리스트 변환 전담
│   └── field_converter.py        # 필드 매핑 변환 전담
└── validators/                   # 검증기
    ├── __init__.py
    ├── base_validator.py
    └── form_validators.py
```

#### 1.2 기본 처리기 클래스 설계
```python
# processors/base_processor.py
class BaseFormProcessor:
    def __init__(self, form_config):
        self.form_config = form_config
        self.date_converter = DateConverter()
        self.item_converter = ItemConverter()
        
    def process_slots(self, slots_dict, current_date_iso):
        """슬롯 처리 템플릿 메서드"""
        slots = self.preprocess_slots(slots_dict)
        slots = self.convert_dates(slots, current_date_iso)
        slots = self.convert_items(slots)
        slots = self.postprocess_slots(slots)
        return slots
    
    def convert_to_payload(self, form_data):
        """API Payload 변환 템플릿 메서드"""
        payload = self.create_base_payload(form_data)
        payload = self.populate_line_list(payload, form_data)
        payload = self.populate_day_list(payload, form_data)
        payload = self.populate_amount_list(payload, form_data)
        return payload
    
    # 추상 메서드들
    def preprocess_slots(self, slots_dict): pass
    def convert_items(self, slots): pass
    def postprocess_slots(self, slots): pass
    def populate_day_list(self, payload, form_data): pass
    def populate_amount_list(self, payload, form_data): pass
```

#### 1.3 날짜 변환기 분리
```python
# converters/date_converter.py
class DateConverter:
    def convert_date_fields(self, slots, current_date_iso):
        """일반 날짜 필드 변환"""
        
    def convert_date_range(self, start_date, end_date, current_date_iso):
        """날짜 범위 변환"""
        
    def convert_item_dates(self, items, current_date_iso):
        """아이템 내 날짜 필드 변환"""
        
    def convert_datetime_to_time(self, datetime_str):
        """datetime을 time으로 변환 (야근시간 등)"""
```

#### 1.4 아이템 변환기 분리
```python
# converters/item_converter.py
class ItemConverter:
    def decompose_to_html_fields(self, items, prefix, max_count):
        """아이템 배열을 개별 HTML 필드로 분해"""
        
    def calculate_totals(self, items, amount_field):
        """총액 계산"""
        
    def map_item_fields(self, items, field_mapping):
        """필드명 매핑 (item_purpose → item_notes 등)"""
```

### Phase 2: JavaScript 리팩토링

#### 2.1 공통 처리기 클래스 설계
```javascript
// static/js/form-processor.js
class BaseFormProcessor {
    constructor(formConfig) {
        this.formConfig = formConfig;
        this.validator = new FormValidator(formConfig);
    }
    
    process(activeForm, slots, getElementValueOrSlotFunc) {
        const formData = this.collectFormData(activeForm, slots, getElementValueOrSlotFunc);
        const validationResult = this.validator.validate(formData);
        
        if (validationResult.hasError) {
            return { error: true, message: validationResult.message };
        }
        
        return this.buildResult(formData);
    }
    
    collectFormData(activeForm, slots, getElementValueOrSlotFunc) {
        const data = {};
        
        // 기본 필드 수집
        for (const field of this.formConfig.basicFields) {
            data[field.name] = getElementValueOrSlotFunc(
                activeForm, field.elementId, field.slotKey, slots
            );
        }
        
        // 아이템 필드 수집 (있는 경우)
        if (this.formConfig.itemFields) {
            data[this.formConfig.itemFields.arrayName] = 
                this.collectItemFields(activeForm, slots, getElementValueOrSlotFunc);
        }
        
        return data;
    }
    
    collectItemFields(activeForm, slots, getElementValueOrSlotFunc) {
        // 공통 아이템 수집 로직
    }
    
    buildResult(formData) {
        // 결과 구성 로직
    }
}
```

#### 2.2 양식별 설정 외부화
```javascript
// static/js/form-configs.js
const FORM_CONFIGS = {
    "연차 신청서": {
        basicFields: [
            { name: "title", elementId: "title", slotKey: "title" },
            { name: "start_date", elementId: "start_date", slotKey: "start_date" },
            { name: "end_date", elementId: "end_date", slotKey: "end_date" },
            { name: "reason", elementId: "reason", slotKey: "reason" }
        ],
        requiredFields: ["start_date", "reason"],
        dvType: "ANNUAL_LEAVE"
    },
    
    "구매 품의서": {
        basicFields: [
            { name: "title", elementId: "title", slotKey: "title" },
            { name: "draft_date", elementId: "draft_date", slotKey: "draft_date" },
            // ... 기타 필드들
        ],
        itemFields: {
            arrayName: "purchase_items",
            maxCount: 3,
            fieldMapping: [
                { name: "item_name", prefix: "item_name_" },
                { name: "item_spec", prefix: "item_spec_" },
                // ... 기타 아이템 필드들
            ],
            requiredFields: ["item_name", "item_total_price"]
        },
        requiredFields: ["draft_date"]
    }
    // ... 기타 양식들
};
```

### Phase 3: 실행 계획

#### 3.1 1주차: 기반 구조 구축
- [ ] 새로운 디렉토리 구조 생성
- [ ] `BaseFormProcessor`, `DateConverter`, `ItemConverter` 기본 클래스 구현
- [ ] 기존 코드에서 공통 로직 추출

#### 3.2 2주차: 백엔드 리팩토링
- [ ] 연차 신청서 processor 분리 및 테스트
- [ ] 야근 식대, 교통비 processor 분리
- [ ] 파견/출장, 비품구매 processor 분리

#### 3.3 3주차: 프론트엔드 리팩토링
- [ ] JavaScript `BaseFormProcessor` 구현
- [ ] 양식별 설정 외부화
- [ ] 연차, 야근식대, 교통비 적용 및 테스트

#### 3.4 4주차: 나머지 양식 및 최적화
- [ ] 구매품의서, 개인경비, 법인카드 적용
- [ ] 통합 테스트 및 성능 최적화
- [ ] 문서화 업데이트

## 📊 예상 효과

### 코드 길이 감소
- `service.py`: 2025줄 → 약 800줄 (60% 감소)
- 각 processor: 100-150줄
- JavaScript: 각 양식당 20-30줄 (80% 감소)

### 유지보수성 향상
- 새로운 양식 추가: 설정 파일 + processor 클래스만 추가
- 버그 수정: 해당 processor만 수정
- 공통 로직 변경: 기본 클래스만 수정

### 가독성 향상
- 단일 책임 원칙 준수
- 명확한 모듈 분리
- 설정과 로직의 분리

## 🛡️ 마이그레이션 전략

### 1. 점진적 전환
- 기존 코드는 유지하면서 새로운 구조 병행 개발
- 양식별로 하나씩 새로운 구조로 전환
- 충분한 테스트 후 기존 코드 제거

### 2. 백워드 호환성
- 기존 API 엔드포인트는 그대로 유지
- 내부 구현만 새로운 구조로 교체
- 클라이언트 측 변경 최소화

### 3. 테스트 전략
- 각 processor별 단위 테스트
- 통합 테스트로 전체 플로우 검증
- 기존 테스트 케이스 재활용

## 🔧 도구 및 리소스

### 개발 도구
- IDE 리팩토링 기능 활용
- 정적 분석 도구로 코드 품질 검증
- 타입 힌트로 인터페이스 명확화

### 문서화
- 각 모듈별 README 작성
- API 문서 업데이트
- 마이그레이션 가이드 작성

이 리팩토링을 통해 코드의 가독성, 유지보수성, 확장성을 크게 개선할 수 있을 것입니다. 단계별로 진행하여 서비스 중단 없이 안전하게 전환할 수 있습니다. 