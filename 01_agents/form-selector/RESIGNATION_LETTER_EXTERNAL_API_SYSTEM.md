# 사직서 외부 API 템플릿 시스템

## 개요

이 문서는 사직서 양식을 외부 API를 통해 제공하는 시스템의 아키텍처와 구현 방법을 설명합니다. 기존의 로컬 파일 기반 템플릿 시스템을 확장하여 외부 API URL을 통해 HTML 템플릿을 동적으로 가져오는 구조로 설계되었습니다.

## 시스템 아키텍처

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   클라이언트     │    │   메인 서버      │    │  템플릿 API 서버 │
│  (브라우저)      │    │  (FastAPI)       │    │   (Flask)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │ 1. 사직서 요청        │                       │
         ├───────────────────────┤                       │
         │                       │ 2. 양식 분류          │
         │                       ├───────────────────────┤
         │                       │ 3. RAG 템플릿 검색    │
         │                       ├───────────────────────┤
         │                       │ 4. 외부 API 호출      │
         │                       ├───────────────────────┤
         │                       │ 5. 슬롯 추출         │
         │                       ├───────────────────────┤
         │                       │ 6. 템플릿 채우기      │
         │                       ├───────────────────────┤
         │ 7. 완성된 사직서      │                       │
         └───────────────────────┘                       │
```

## 핵심 컴포넌트

### 1. 템플릿 API 서버 (`template_api_server.py`)

**목적**: 사직서 HTML 템플릿을 HTTP API로 제공

**주요 기능**:
- Flask 기반 HTTP 서버
- `/resignation_letter` 엔드포인트로 사직서 HTML 템플릿 제공
- UTF-8 인코딩으로 한글 지원
- 개발/프로덕션 환경 구분

**실행 방법**:
```bash
python template_api_server.py
```

**API 엔드포인트**:
- `GET /resignation_letter`: 사직서 HTML 템플릿 반환
- `GET /health`: 서버 상태 확인
- `GET /`: API 정보 및 엔드포인트 목록

### 2. 양식 설정 (`form_configs.py`)

**사직서 설정**:
```python
"사직서": FormConfig(
    model=ResignationLetterSlots,
    prompt_template_path="resignation_letter_slots_prompt.txt",
    html_template_path="http://localhost:5000/resignation_letter",  # 외부 API URL
    mstPid=10,
    english_id="resignation_letter",
    is_external_template=True,  # 외부 API 플래그
),
```

**주요 변경사항**:
- `html_template_path`: 로컬 파일 경로 → 외부 API URL
- `is_external_template`: `False` → `True`

### 3. RAG 시스템 (`rag.py`)

**외부 API 지원 확장**:
```python
def fetch_template_from_api(template_url: str) -> Optional[str]:
    """외부 API에서 HTML 템플릿을 가져옵니다."""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(template_url)
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.error(f"Error fetching template from {template_url}: {e}")
        return None
```

**VectorStore 구성**:
- 로컬 파일과 외부 API URL 모두 지원
- FAISS 인덱스에 외부 API 템플릿 포함
- 메타데이터에 `source` 필드로 URL 정보 저장

## 데이터 흐름

### 1. 사용자 요청 처리

```
사용자 입력: "홍길동입니다. 개발팀 사원으로 일하고 있는데, 개인적인 사정으로 1월 31일에 사직하고 싶습니다. 연락처는 010-1234-5678입니다."
```

### 2. 양식 분류

```
LLM 분류 결과:
- form_type: "사직서"
- keywords: ["사직", "개인적인 사정", "1월 31일"]
```

### 3. RAG 템플릿 검색

```
검색 쿼리: "사직서 사직 개인적인 사정 1월 31일"
결과: http://localhost:5000/resignation_letter
```

### 4. 외부 API 호출

```
GET http://localhost:5000/resignation_letter
응답: 사직서 HTML 템플릿 (UTF-8 인코딩)
```

### 5. 슬롯 추출

```
추출된 정보:
- employee_name: "홍길동"
- department: "개발팀"
- position: "사원"
- resignation_date: "2024-01-31"
- resignation_reason: "개인적인 사정"
- contact_info: "010-1234-5678"
```

### 6. 템플릿 채우기

```
완성된 사직서 HTML:
- 모든 슬롯이 실제 데이터로 채워짐
- 서명 및 날짜 자동 생성
- 반응형 디자인 적용
```

## 구현 세부사항

### 1. 오류 처리

**네트워크 오류**:
```python
except httpx.RequestError as e:
    logger.error(f"Request error fetching template from {template_url}: {e}")
    return None
```

**HTTP 오류**:
```python
except httpx.HTTPStatusError as e:
    logger.error(f"HTTP error fetching template from {template_url}: {e.response.status_code}")
    return None
```

### 2. 타임아웃 설정

```python
with httpx.Client(timeout=10.0) as client:
    response = client.get(template_url)
```

### 3. 인코딩 처리

```python
return RESIGNATION_LETTER_TEMPLATE, 200, {'Content-Type': 'text/html; charset=utf-8'}
```

## 장점

### 1. 유연성
- 로컬 파일과 외부 API 모두 지원
- 동적 템플릿 업데이트 가능
- 분산 시스템 구성 가능

### 2. 확장성
- 새로운 템플릿 서버 추가 용이
- 마이크로서비스 아키텍처 지원
- 로드 밸런싱 가능

### 3. 유지보수성
- 템플릿과 로직 분리
- 독립적인 배포 가능
- 버전 관리 용이

## 테스트 방법

### 1. API 서버 테스트

```bash
# 템플릿 API 서버 시작
python template_api_server.py

# API 테스트
curl http://localhost:5000/resignation_letter
```

### 2. 통합 테스트

```bash
# 메인 서버 시작
python main.py

# API 엔드포인트 테스트
curl -X POST "http://localhost:8000/form-selector" \
  -H "Content-Type: application/json" \
  -d '{"input": "홍길동입니다. 개발팀 사원으로 일하고 있는데, 개인적인 사정으로 1월 31일에 사직하고 싶습니다. 연락처는 010-1234-5678입니다."}'
```

### 3. 브라우저 테스트

```
URL: http://localhost:8000/ui/index.html
입력: "홍길동입니다. 개발팀 사원으로 일하고 있는데, 개인적인 사정으로 1월 31일에 사직하고 싶습니다. 연락처는 010-1234-5678입니다."
```

## 모니터링 및 로깅

### 1. 로그 레벨

- `INFO`: 정상 처리 과정
- `WARNING`: 템플릿 검색 실패
- `ERROR`: 네트워크 오류, HTTP 오류

### 2. 주요 로그 메시지

```
INFO:form_selector.rag:RAG Retrieved: http://localhost:5000/resignation_letter for form_type '사직서'
INFO:root:Retrieved template for form_type: 사직서
INFO:root:Template filled successfully by DefaultFormProcessor
```

## 향후 개선 방향

### 1. 캐싱 시스템
- Redis를 활용한 템플릿 캐싱
- 캐시 무효화 전략

### 2. 보안 강화
- API 인증/인가
- HTTPS 적용
- Rate Limiting

### 3. 모니터링 강화
- Prometheus 메트릭 수집
- Grafana 대시보드
- 알림 시스템

### 4. 컨테이너화
- Docker 컨테이너 배포
- Kubernetes 오케스트레이션
- CI/CD 파이프라인

## 결론

외부 API를 통한 템플릿 제공 시스템은 기존 로컬 파일 기반 시스템의 한계를 극복하고, 더욱 유연하고 확장 가능한 아키텍처를 제공합니다. 이 시스템을 통해 템플릿의 동적 업데이트, 분산 배포, 그리고 마이크로서비스 아키텍처로의 전환이 가능해집니다.

---

**작성일**: 2025년 8월 7일  
**버전**: 1.0  
**작성자**: AI Assistant 