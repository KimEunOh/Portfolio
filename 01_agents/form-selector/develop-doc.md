# 간접 표현 → 명시적 양식 매핑

## 방법 1. LLM 기반 Intent Classifier 추가 (RAG 전처리 전 단계)

자연어 입력을 먼저 LLM에 던져서 **결재 유형**을 분류하거나 요약한 후, 그 결과를 벡터 검색에 사용합니다.

### 처리 흐름 예시

**입력:**  
"나 이번주에 가족여행을 가려고 해."

**LLM 프롬프트:**
```
다음 사용자의 발화가 어떤 결재 문서와 가장 관련이 있습니까?
```

**LLM 응답:**
```
연차 신청서
```

**RAG 또는 템플릿 라우팅:**  
연차 신청서 HTML 반환

#### 프롬프트 예시

```python
SYSTEM:
당신은 사내 전자결재 문서를 추천하는 비서입니다.
다음 사용자의 입력이 어떤 결재 양식과 가장 관련이 있을지 판단해주세요.
양식 종류: 연차 신청서, 출장비 신청서, 회의비 지출결의서, 기타 비용 청구서

USER:
나 이번주에 가족여행을 가려고 해.
```
**출력:**
"연차 신청서"

---

## 시스템 아키텍처: 결재 양식 판별 + HTML 카드 제공

### 🎯 목표

- 사용자의 자연어 입력을 기반으로 적절한 전자 결재 양식 HTML 카드를 제공
- LLM은 전처리 및 양식 선택 용도로만 사용 (문서 생성은 아님)
- 클릭 또는 확인 시 결재 흐름 시작 (예: 제출, 승인자 지정 등은 외부 시스템에 위임 가능)

---

## 🧩 구성요소별 세부 설계

### ① 사용자 입력 처리 (LLM 활용)

**자연어 요청 예시:**
- "출장비 결재 올려줘"
- "연차 신청하려고"
- "회의비 지출이 있어"

**LLM 활용 방식:**
- 입력을 intent + slot 형태로 분류 (양식 유형 판별)

**예시 Output (LLM 또는 함수 호출):**
```json
{
  "form_type": "출장비_신청서",
  "keywords": ["출장", "교통비", "비용"]
}
```

**도구 추천:**
- OpenAI Function Calling
- Pydantic 기반 schema validation
- LangChain Output Parser (optional)

---

### ② HTML 카드 양식 반환

- 분류된 form_type에 따라 사전에 준비된 HTML 양식 템플릿 반환

**예시 카드:**
```html
<div class="card">
  <h2>출장비 신청서</h2>
  <form>
    <label>출장 목적:</label><br>
    <input type="text" name="purpose"><br>
    <label>출장 기간:</label><br>
    <input type="date" name="start_date"> ~ <input type="date" name="end_date"><br>
    <label>경비 내역:</label><br>
    <textarea name="expenses"></textarea><br>
    <button type="submit">제출</button>
  </form>
</div>
```

**카드 반환 방식**
- 프론트엔드: 사용자 메시지 하단에 HTML 삽입
- 백엔드: API에서 HTML string 혹은 JSON 구조로 반환

---

## 📦 사용 예시 시나리오

**입력:**  
"3일간 대전 출장 가는 비용 결재 올릴래요"

**LLM 응답:**  
form_type: 출장비_신청서

**HTML 카드 반환:**  
프론트에 출장비 신청 HTML 카드 표시

**사용자 입력 후 제출:**  
결재 시스템에 POST (외부 API 연동 또는 내부 처리)



1. 현재 계획 평가
장점
LLM Intent Classifier를 통해 사용자의 자연어 입력을 명확한 form_type(의도)로 변환 → RAG나 템플릿 매핑의 정확도 향상
LLM이 slot/key 추출까지 해주면, downstream 시스템이 단순해지고, 템플릿/DB/RAG에서의 검색 효율이 높아짐
확장성(양식 추가, 키워드 추가 등)이 뛰어남
단점/고려점
LLM 호출 비용 및 응답 속도(실시간성 요구 시)
LLM이 잘못된 form_type을 반환할 경우 fallback 필요
form_type이 모호하거나 복합적인 경우(예: 출장+연차) 처리 정책 필요
2. 더 좋은 대안이 있는가?
(1) LLM + Rule 기반 하이브리드
LLM이 1차 분류, 이후 rule 기반(키워드 매칭 등)으로 보정/보완
장점: LLM의 실수 보완, 예측 불가 상황에서 fallback 가능
(2) LLM Output에 Confidence Score 추가
LLM이 form_type과 함께 신뢰도(혹은 Top-N 후보)를 반환
신뢰도 낮으면 사용자에게 재질문/선택지 제공
(3) RAG를 LLM 이전에 활용
벡터 DB에서 유사한 과거 양식/예시를 먼저 검색 → LLM에 context로 제공
장점: LLM의 분류 정확도 향상, 예시 기반 reasoning 가능
(4) Slot Filling/Entity Extraction
form_type뿐 아니라, 필요한 slot(날짜, 금액 등)도 LLM이 추출 → 템플릿 자동 채움
결론:
현재 계획(LLM → form_type/slot 추출 → 템플릿/RAG)은 가장 실용적이고 확장성 높은 구조입니다.
다만, (1) rule fallback, (2) confidence score, (3) RAG context 보강, (4) slot filling 등은 실제 서비스 품질을 높이기 위해 추가 고려할 만합니다.
3. 세부 구현 방안
1단계: LLM 기반 Intent Classifier
입력: 사용자 자연어
출력: form_type, keywords, (optionally) slots
구현: LangChain + PydanticOutputParser
2단계: RAG/템플릿 매핑
form_type, keywords를 기반으로 템플릿/DB/RAG에서 적합한 양식 검색
템플릿은 파일/DB/VectorStore 등에서 관리 가능
3단계: Fallback 및 예외 처리
LLM이 불확실하거나 미지원 form_type 반환 시, rule 기반 보정 또는 사용자 재질문
4단계: (선택) Slot 자동 채움
LLM이 추출한 slot 정보를 템플릿에 미리 채워서 반환
4. 예시 플로우
사용자 입력: "3일간 대전 출장 가는 비용 결재 올릴래요"
LLM →
Apply to develop-doc....
템플릿/RAG에서 "출장비 신청서" 템플릿 반환, 필요시 slot 값 자동 채움
사용자에게 HTML 카드 제공
5. 추천 구현 순서
LLM Intent Classifier 체인 완성 (form_type, keywords, slots 추출)
템플릿/DB/RAG에서 form_type 기반 템플릿 반환 로직 구현
(선택) slot 정보 템플릿에 자동 채움
Fallback 및 예외 처리 추가