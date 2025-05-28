# 새로운 전자결재 양식 추가 매뉴얼

이 문서는 `form-selector` 시스템에 새로운 전자결재 양식을 추가하는 방법을 안내합니다.
새로운 양식을 추가하는 작업은 주로 Python 코드 수정과 프롬프트 파일 작성으로 이루어집니다.

## 사전 준비

- 추가하려는 새로운 전자결재 양식의 HTML 템플릿 파일
- 해당 양식에서 사용자가 입력해야 할 정보 항목(슬롯) 목록

## 추가 단계

새로운 양식(예: "근태 조정 신청서")을 시스템에 통합하는 과정은 다음과 같습니다.

### 1. HTML 템플릿 파일 준비 및 배치

1.  새로운 양식의 HTML 파일을 준비합니다.
    *   각 입력 필드(input, textarea, select 등)에는 JavaScript로 값을 채울 수 있도록 **고유한 `id` 속성**을 반드시 부여해야 합니다.
    *   예시: `<input type="text" id="employee_name">`
2.  준비된 HTML 파일을 `form_selector/templates/` 디렉터리에 저장합니다.
    *   파일 이름은 가급적 양식의 내용을 유추할 수 있도록 영문 소문자와 언더스코어(`_`)를 사용합니다. (예: `attendance_correction_form.html`)

### 2. Pydantic 모델 정의

1.  `form_selector/form_selector/schema.py` 파일을 엽니다.
2.  새로운 양식에서 추출할 정보 항목(슬롯)들을 정의하는 Pydantic 모델 클래스를 추가합니다.
    *   클래스 이름은 `양식명Slots` 규칙을 따릅니다. (예: `AttendanceCorrectionSlots`)
    *   각 필드는 `Optional[str]` 또는 필요에 따라 `Optional[List[str]]` 등으로 정의하고, `Field`를 사용하여 설명을 추가합니다.
    *   LLM이 자연어 그대로 추출하도록 유도하고, 후처리(날짜 변환 등)는 `service.py`에서 담당하는 것을 염두에 둡니다.

    ```python
    # form_selector/form_selector/schema.py 예시

    from pydantic import BaseModel, Field
    from typing import List, Optional, Any

    # ... (기존 모델들) ...

    class AttendanceCorrectionSlots(BaseModel):
        """근태 조정 신청서 슬롯"""
        target_date: Optional[str] = Field(default=None, description="조정 대상 날짜 (자연어 형태, 예: 어제, 2023-12-25)")
        original_time_in: Optional[str] = Field(default=None, description="원래 출근 시간 (자연어 형태, 예: 오전 9시)")
        original_time_out: Optional[str] = Field(default=None, description="원래 퇴근 시간 (자연어 형태, 예: 오후 6시)")
        requested_time_in: Optional[str] = Field(default=None, description="조정 요청 출근 시간 (자연어 형태)")
        requested_time_out: Optional[str] = Field(default=None, description="조정 요청 퇴근 시간 (자연어 형태)")
        reason: Optional[str] = Field(default=None, description="조정 사유")
        # ... 기타 필요한 슬롯들 ...
    ```

### 3. 슬롯 추출 프롬프트 생성

1.  `form_selector/form_selector/prompts/` 디렉터리에 새로운 프롬프트 파일을 생성합니다.
    *   파일 이름은 `양식명_slots_prompt.txt` 규칙을 따릅니다. (예: `attendance_correction_slots_prompt.txt`)
2.  프롬프트 파일 내용은 다음 구조를 따릅니다.
    *   **지시문**: LLM의 역할과 주요 지침 (JSON 출력, 누락 정보 처리, 날짜/시간 형식 등)을 명시합니다.
    *   **추출 대상 슬롯**: `schema.py`에 정의한 Pydantic 모델의 각 필드명과 해당 필드에 대한 상세 설명, 추출 예시를 제공합니다.
    *   **예시**: 실제 사용자 입력 예시와 그에 따른 예상 출력 JSON (Pydantic 모델 구조에 맞게)을 제공하여 LLM이 형식을 더 잘 이해하도록 돕습니다. `{format_instructions}` 플레이스홀더를 포함해야 합니다.

    ```text
    # form_selector/form_selector/prompts/attendance_correction_slots_prompt.txt 예시

    # 지시문:
    당신은 사용자의 자연어 입력으로부터 "근태 조정 신청서"에 필요한 정보 항목들을 추출하는 AI 어시스턴트입니다.
    다음은 사용자가 입력할 수 있는 정보 항목들과 그 설명입니다. 각 항목에 대해 정확한 값을 추출해주세요.
    주어진 형식 지침을 엄격히 따라야 합니다. 날짜 및 시간 정보는 사용자의 표현 그대로 추출해주세요. (예: "어제 오전 9시", "12월 25일 18:00")
    만약 특정 정보가 사용자의 입력에 없다면, 해당 항목은 누락된 것으로 간주하고 출력 JSON에서 해당 키를 제외해주세요.

    # 추출 대상 슬롯:
    - target_date: 조정 대상 날짜 (예: "어제", "12월 25일", "지난주 월요일")
    - original_time_in: 원래 출근 시간 (예: "오전 9시", "09:00")
    - original_time_out: 원래 퇴근 시간 (예: "오후 6시", "18:00")
    - requested_time_in: 조정 요청 출근 시간 (예: "오전 9시 30분", "09:30")
    - requested_time_out: 조정 요청 퇴근 시간 (예: "오후 6시 30분", "18:30")
    - reason: 조정 사유 (예: "병원 방문으로 인한 지각", "오전 업무 집중")

    # 예시:
    사용자 입력: "어제 병원 다녀오느라 늦어서 근태 조정 신청합니다. 원래 9시 출근인데 10시에 도착했고, 퇴근은 6시 정시에 했어요."
    출력 형식: {format_instructions}
    예상 출력 (Pydantic 모델에 맞게):
    {{
        "target_date": "어제",
        "original_time_in": "9시",
        "requested_time_in": "10시",
        "original_time_out": "6시",
        "reason": "병원 방문으로 인한 지각"
    }}
    ```

### 4. 양식 설정 파일 업데이트

1.  `form_selector/form_selector/form_configs.py` 파일을 엽니다.
2.  `FORM_CONFIGS` 딕셔너리에 새로운 양식에 대한 설정을 추가합니다.
    *   **키**: 양식의 이름 (사용자에게 표시되고, LLM이 분류할 이름. 예: `"근태 조정 신청서"`)
    *   **값 (딕셔너리)**:
        *   `"pydantic_model"`: `schema.py`에 정의한 Pydantic 모델 클래스 (예: `AttendanceCorrectionSlots`)
        *   `"prompt_file_name"`: `prompts/` 디렉터리에 생성한 프롬프트 파일명 (예: `"attendance_correction_slots_prompt.txt"`)
        *   `"template_file_name"`: `templates/` 디렉터리에 저장한 HTML 파일명 (예: `"attendance_correction_form.html"`)

    ```python
    # form_selector/form_selector/form_configs.py 예시

    from .schema import (
        AnnualLeaveSlots,
        # ... (기존 모델 임포트) ...
        AttendanceCorrectionSlots, # 새로 추가한 모델 임포트
    )

    FORM_CONFIGS = {
        # ... (기존 양식 설정) ...
        "근태 조정 신청서": {
            "pydantic_model": AttendanceCorrectionSlots,
            "prompt_file_name": "attendance_correction_slots_prompt.txt",
            "template_file_name": "attendance_correction_form.html",
        },
        # 새로운 양식 추가 시 여기에 항목만 추가
    }

    # AVAILABLE_FORM_TYPES와 TEMPLATE_FILENAME_MAP은 자동으로 업데이트됩니다.
    ```
    **중요**: `form_configs.py` 상단에 새로 만든 Pydantic 모델을 임포트하는 것을 잊지 마세요.

### 5. RAG 인덱스 업데이트 (필요시)

새로운 HTML 템플릿이 RAG 검색 결과에 포함되도록 벡터 스토어를 업데이트해야 합니다.

*   만약 `create_vector_store.py` 와 같이 벡터 스토어를 생성/업데이트하는 스크립트가 프로젝트 내에 있다면, 해당 스크립트를 실행합니다.
    ```bash
    # 예시 (가상환경 활성화 후 프로젝트 루트에서 실행)
    python -m form_selector.create_vector_store
    ```
*   별도의 스크립트가 없다면, 수동으로 FAISS 인덱스를 재생성하거나 관련 로직을 실행해야 합니다. (현재 `rag.py`는 모듈 로드 시 자동으로 `templates` 폴더를 스캔하여 인덱스를 빌드하거나 로드하므로, FastAPI 서버를 재시작하면 대부분 자동으로 반영될 수 있습니다. 단, `faiss_index` 폴더가 이미 존재하고 변경 사항을 감지하지 못하는 경우 수동으로 해당 폴더를 삭제 후 서버를 재시작해야 할 수 있습니다.)

### 6. 테스트

FastAPI 애플리케이션을 실행하고, 새로운 양식이 올바르게 분류되고 해당 양식의 슬롯들이 사용자의 자연어 입력으로부터 정확하게 추출되어 HTML 필드에 채워지는지 테스트합니다.

- 양식 분류 테스트: "근태 조정 신청하고 싶어"
- 슬롯 추출 테스트: "어제 병원 다녀와서 10시 출근했어. 근태 조정 신청할게."

## 문제 해결

- **양식이 분류되지 않는 경우**:
    - `form_selector/prompts/form_classifier_prompt.txt` 의 예시나 설명을 확인하여 LLM이 새로운 양식명을 잘 학습할 수 있도록 조정합니다.
    - `form_selector/form_configs.py` 의 `FORM_CONFIGS` 딕셔너리 키 (양식명)가 정확한지 확인합니다.
- **슬롯이 제대로 추출되지 않는 경우**:
    - 해당 양식의 `_slots_prompt.txt` 파일의 지시문, 슬롯 설명, 예시 등을 검토하고 수정합니다.
    - `schema.py` 에 정의된 Pydantic 모델의 필드명과 프롬프트의 슬롯명이 일치하는지 확인합니다.
- **HTML 필드에 값이 채워지지 않는 경우**:
    - HTML 템플릿 파일의 해당 입력 필드에 `id` 속성이 올바르게 부여되었는지 확인합니다.
    - `service.py`의 `fill_slots_in_template` 함수에서 특정 슬롯에 대한 후처리 로직이 필요한 경우 (예: 복잡한 시간 조합) 해당 로직을 추가하거나 수정합니다. (대부분의 날짜/시간 관련 슬롯은 `utils.py`의 파서와 `service.py`의 기존 로직으로 처리됩니다.)
    - LLM이 추출한 슬롯 값(예: "오전 반차")이 HTML `<select>` 태그의 `<option>`에 있는 `value` 속성 값(예: "half_day_morning")과 다른 경우가 있을 수 있습니다. 이 경우, `service.py`의 `fill_slots_in_template` 함수 내에서 해당 슬롯 값을 HTML `value`에 맞게 변환하는 로직을 추가해야 합니다. 예를 들어, 특정 슬롯 값에 대한 매핑 테이블(Python 딕셔너리)을 정의하고, `processed_slots` 딕셔너리의 해당 슬롯 값을 이 매핑 테이블을 참조하여 업데이트할 수 있습니다 (`LEAVE_TYPE_TEXT_TO_VALUE_MAP` 및 관련 처리 로직 참고).

---

위 단계를 따르면 새로운 전자결재 양식을 시스템에 성공적으로 추가하고 관리할 수 있습니다. 