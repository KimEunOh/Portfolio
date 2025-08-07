# API 페이로드(Payload) 전송 양식

이 문서는 각 전자결재 폼(Form)에서 API 서버로 전송되는 데이터의 최종 구조(Payload)를 정의합니다.

---

## 1. 연차 신청서 (`annual_leave_processor.py`)


- **필드 설명:**
    - `mstPid`: 마스터 PID (고정값: `"1"`)
    - `aprvNm`: 문서 제목 (예: "연차 사용 신청")
    - `drafterId`: 기안자 ID (예: "00009")
    - `docCn`: 사유 (예: "개인 사유")
    - `apdInfo`: 추가 정보 (빈 JSON 객체 `"{}"`)
    - `lineList`: 결재라인 목록
        - `aprvPsId`: 결재자 ID
        - `aprvDvTy`: 결재 구분 타입
        - `ordr`: 결재 순서
    - `dayList`: 휴가 날짜 목록
        - `reqYmd`: 휴가 날짜 (`YYYY-MM-DD`)
        - `dvType`: 휴가 종류 (`DAY`, `HALF_AM`, `HALF_PM`, `QUARTER_AM`, `QUARTER_PM`)
    - `amountList`: 비용 목록 (빈 배열 `[]`)


---

## 2. 야근 식대 신청서 (`dinner_expense_processor.py`)

- **필드 설명:**
    - `mstPid`: 마스터 PID (고정값: `"3"`)
    - `aprvNm`: 문서 제목 (예: "야근 식대 신청")
    - `drafterId`: 기안자 ID
    - `docCn`: 업무 내용
    - `apdInfo`: 추가 정보 (JSON 문자열)
        - `workLocation`: 근무지
        - `overtimeTime`: 퇴근 시간 (`HH:MM`)
        - `bankAccountForDeposit`: 입금 계좌
    - `lineList`: 결재라인 목록
    - `dayList`: 날짜 목록 (빈 배열 `[]`)
    - `amountList`: 비용 정보
        - `useYmd`: 근무일자 (`YYYY-MM-DD`)
        - `dvNm`: 구분 (고정값: "식대")
        - `useRsn`: 업무 내용
        - `qnty`: 수량 (고정값: 1)
        - `amt`: 식대 금액
        - `aditInfo`: 추가 정보 (빈 JSON 객체 `"{}"`)

---

## 3. 교통비 신청서 (`transportation_expense_processor.py`)

- **필드 설명:**
    - `mstPid`: 마스터 PID (고정값: `"4"`)
    - `aprvNm`: 신청 목적 (예: "교통비 신청")
    - `drafterId`: 기안자 ID
    - `docCn`: 신청 목적
    - `apdInfo`: 추가 정보 (JSON 문자열)
        - `notes`: 기타 특이사항
    - `lineList`: 결재라인 목록
    - `dayList`: 날짜 목록 (빈 배열 `[]`)
    - `amountList`: 교통 내역
        - `useYmd`: 출발일 (`YYYY-MM-DD`)
        - `dvNm`: 교통수단 및 경로 (예: "택시 (서울역 → 강남역)")
        - `useRsn`: 목적 및 비고
        - `qnty`: 수량 (고정값: 1)
        - `amt`: 금액
        - `aditInfo`: 추가 정보 (JSON 문자열, `item` 객체 전체)
            - `transportType`: 교통수단 (예: "지하철", "버스", "택시")
            - `origin`: 출발지
            - `destination`: 목적지
            - `amount`: 금액 (개별 항목)
            - `notes`: 비고 (개별 항목)

---

## 4. 파견 및 출장보고서 (`dispatch_report_processor.py`)

- **필드 설명:**
    - `mstPid`: 마스터 PID (고정값: `"5"`)
    - `aprvNm`: 문서 제목 (고정값: "파견/출장 보고서")
    - `drafterId`: 기안자 ID
    - `docCn`: 목적
    - `apdInfo`: 추가 정보 (JSON 문자열)
        - `destination`: 파견/출장지
        - `periodDays`: 기간(일)
        - `reportDetails`: 주요 업무 내용 및 결과 (보고사항)
        - `notes`: 기타 특이사항
    - `lineList`: 결재라인 목록
    - `dayList`: 파견/출장 날짜 목록
        - `reqYmd`: 날짜 (`YYYY-MM-DD`)
        - `dvType`: 구분 (고정값: "DAY")
    - `amountList`: 비용 목록 (빈 배열 `[]`)

---

## 5. 비품/소모품 구입내역서 (`inventory_purchase_processor.py`)

- **필드 설명:**
    - `mstPid`: 마스터 PID (고정값: `"6"`)
    - `aprvNm`: 문서 제목 (예: "비품/소모품 구입내역서")
    - `drafterId`: 기안자 ID
    - `docCn`: 특이 사항
    - `apdInfo`: 추가 정보 (JSON 문자열)
        - `requestDate`: 요청일자 (`YYYY-MM-DD`)
        - `totalAmount`: 총 합계 금액
        - `paymentMethod`: 대금 지불 방법
    - `lineList`: 결재라인 목록
    - `dayList`: 날짜 목록 (빈 배열 `[]`)
    - `amountList`: 구입 내역
        - `useYmd`: 요청일자 (`YYYY-MM-DD`)
        - `dvNm`: 품명
        - `useRsn`: 사용 목적
        - `qnty`: 수량
        - `amt`: 금액
        - `aditInfo`: 추가 정보 (JSON 문자열)
            - `unitPrice`: 단가

---

## 6. 구매 품의서 (`purchase_approval_processor.py`)

- **필드 설명:**
    - `mstPid`: 마스터 PID (고정값: `"7"`)
    - `aprvNm`: 문서 제목 (예: "구매 품의서")
    - `drafterId`: 기안자 ID
    - `docCn`: 사용 목적(html 추가 필요)
    - `apdInfo`: 추가 정보 (JSON 문자열)
        - `deliveryLocation`: 납품 장소
        - `paymentTerms`: 결제 조건
        - `totalPurchaseAmount`: 총 구매 금액
        - `specialNotes`: 특이사항
    - `lineList`: 결재라인 목록
    - `dayList`: 날짜 목록 (빈 배열 `[]`)
    - `amountList`: 구매 품목
        - `useYmd`: 납기 요청일 (`YYYY-MM-DD`)
        - `dvNm`: 품명
        - `useRsn`: 비고/목적
        - `qnty`: 수량
        - `amt`: 금액
        - `aditInfo`: 추가 정보 (JSON 문자열)
            - `spec`: 사양
            - `unitPrice`: 단가
            - `supplier`: 공급업체


---

## 7. 개인 경비 사용내역서 (`personal_expense_processor.py`)

- **필드 설명:**
    - `mstPid`: 마스터 PID (고정값: `"8"`)
    - `aprvNm`: 문서 제목 (예: "개인 경비 사용 신청")
    - `drafterId`: 기안자 ID
    - `docCn`: 지출 사유
    - `apdInfo`: 추가 정보 (JSON 문자열)
        - `usageStatus`: 정산 상태(개인카드, 개인현금)
        - `totalAmount`: 총 사용 금액
    - `lineList`: 결재라인 목록
    - `dayList`: 날짜 목록 (빈 배열 `[]`)
    - `amountList`: 비용 내역
        - `useYmd`: 사용일자 (`YYYY-MM-DD`)
        - `dvNm`: 분류 (예: "교통비", "식대")
        - `useRsn`: 내용/사용처
        - `qnty`: 수량 (고정값: 1)
        - `amt`: 금액
        - `aditInfo`: 추가 정보 (JSON 문자열)
            - `notes`: 비고




---

## 8. 법인카드 지출내역서 (`corporate_card_processor.py`)

- **필드 설명:**
    - `mstPid`: 마스터 PID (고정값: `"9"`)
    - `aprvNm`: 문서 제목 (예: "법인카드 사용 내역서")
    - `drafterId`: 기안자 ID
    - `docCn`: 지출 사유
    - `apdInfo`: 추가 정보 (JSON 문자열)
        - `cardNumber`: 카드 번호
        - `expenseReason`: 지출 사유
        - `statementDate`: 작성일자 (`YYYY-MM-DD`)
        - `totalAmount`: 총 사용 금액
    - `lineList`: 결재라인 목록
    - `dayList`: 날짜 목록 (빈 배열 `[]`)
    - `amountList`: 카드 사용 내역
        - `useYmd`: 사용일자 (`YYYY-MM-DD`)
        - `dvNm`: 사용 구분 (카테고리 매핑 값)
        - `useRsn`: 사용 내역/상점명
        - `qnty`: 수량 (고정값: 1)
        - `amt`: 사용 금액
        - `aditInfo`: 추가 정보 (JSON 문자열)
            - `notes`: 비고/메모
