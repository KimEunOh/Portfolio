# API Payload 명세서

이 문서는 결재 시스템에서 사용하는 표준 API Payload의 구조를 정의합니다.

## 1. 최상위 파라미터 (Root Parameters)

모든 결재 요청의 기본이 되는 최상위 레벨의 데이터 구조입니다.

| Name         | Type              | Description                      | Required | Example/Comments                               |
|--------------|-------------------|----------------------------------|----------|------------------------------------------------|
| `mstPid`     | `string`          | 마스터 PID (문서 고유 ID)        | True     | `"ANNUAL-LEAVE-202507-001"`                    |
| `aprvNm`     | `string`          | 결재명 (문서 제목)               | True     | `"개인 사유 연차 사용 신청"`                   |
| `drafterId`  | `string`          | 기안자 ID                        | True     | `"user0123"`                                   |
| `docCn`      | `string`          | 문서 내용 (양식별 주요 사유)     | True     | `"가족 행사 참석으로 인한 연차 사용"`          |
| `apdInfo`    | `string` (JSON)   | 양식별 추가 정보 (JSON 문자열)   | False    | `"{\\"bank_account\\": \\"우리은행...\\"}"`       |
| `lineList`   | `Array<Object>`   | 결재선 리스트                    | True     | 아래 **2. lineList 구조** 참조                 |
| `dayList`    | `Array<Object>`   | 신청일자 리스트 (주로 연차용)    | True     | 연차 신청이 아닐 경우 빈 배열 `[]`             |
| `amountList` | `Array<Object>`   | 결재금액 리스트 (주로 비용 정산용) | True     | 비용 정산이 아닐 경우 빈 배열 `[]`             |

---

## 2. `lineList` 구조

결재선을 정의하는 객체 리스트입니다.

| Name        | Type     | Description    | Required | Example/Comments            |
|-------------|----------|----------------|----------|-----------------------------|
| `aprvPslId` | `string` | 결재자 ID      | True     | `"manager01"`               |
| `aprvDvTy`  | `string` | 결재 구분 타입 | True     | `"APPROVAL"`, `"AGREEMENT"` |
| `ordr`      | `int`    | 결재 순서      | True     | `1`                         |

---

## 3. `dayList` 구조

연차, 반차 등 날짜 기반의 신청 항목을 정의하는 객체 리스트입니다.

| Name     | Type     | Description | Required | Example/Comments                       |
|----------|----------|-------------|----------|----------------------------------------|
| `reqYmd` | `date`   | 연차 날짜   | True     | `"2025-07-21"`                         |
| `dvType` | `string` | 연차 종류   | True     | `"DAY"`, `"HALF_AM"`, `"HALF_PM"` 등 |

---

## 4. `amountList` 구조

각종 비용 항목의 상세 내역을 정의하는 객체 리스트입니다.

| Name        | Type     | Description        | Required                            | Example/Comments                           |
|-------------|----------|--------------------|-------------------------------------|--------------------------------------------|
| `useYmd`    | `date`   | 사용일자           | True                                | `"2025-07-20"`                             |
| `dvNm`      | `string` | 사용 구분 (계정과목) | True                                | `"식대"`, `"교통비"`, `"사무용품"`       |
| `useRsn`    | `string` | 사용 사유 (상세내역) | True                                | `"팀원들과 함께 저녁 식사"`                |
| `amount`    | `number` | 결재 금액          | True                                | `85000`                                    |
| `unit`      | `string` | 단위               | False (비품/구매 양식에서 사용) | `"박스"`, `"개"`                           |
| `quantity`  | `number` | 수량               | False (비품/구매 양식에서 사용) | `2`                                        |
| `unitPrice` | `number` | 단가               | False (비품/구매 양식에서 사용) | `25000`                                    |

</rewritten_file> 