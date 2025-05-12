# GW Agent API 예제

## 채팅 API 흐름

### 1. 초기 요청
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "연차 신청",
    "session_id": "26793581-bbda-4918-b7cc-b23b9e1ba990",
    "session_state": {},
    "agent_type": "general"
  }'
```

### 2. 세션 초기화 응답
```json
{
  "response": "연차 신청을 도와드리겠습니다.",
  "session_id": "26793581-bbda-4918-b7cc-b23b9e1ba990",
  "session_state": {
    "messages": [],
    "vacation_info": {
      "drafterId": "01180001",
      "mstPid": 1
    },
    "next": "supervisor",
    "thread_id": "26793581-bbda-4918-b7cc-b23b9e1ba990"
  },
  "metadata": {
    "thread_id": "26793581-bbda-4918-b7cc-b23b9e1ba990"
  }
}
```

### 3. 연차 정보 수집 요청
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "4월 20일 연차 신청하고 싶어요",
    "session_id": "26793581-bbda-4918-b7cc-b23b9e1ba990",
    "session_state": {
      "messages": [],
      "vacation_info": {
        "drafterId": "01180001",
        "mstPid": 1
      },
      "next": "supervisor",
      "thread_id": "26793581-bbda-4918-b7cc-b23b9e1ba990"
    },
    "agent_type": "general"
  }'
```

### 4. 연차 정보 추출 응답
```json
{
  "response": "다음 정보로 연차를 신청하시겠습니까?\n\n연차 종류: 연차\n시작일: 2025-04-20\n종료일: 2025-04-20",
  "session_id": "26793581-bbda-4918-b7cc-b23b9e1ba990",
  "session_state": {
    "messages": [...],
    "vacation_info": {
      "drafterId": "01180001",
      "mstPid": 1,
      "dvType": "연차",
      "start_date": "2025-04-20",
      "end_date": "2025-04-20",
      "dayList": [
        {
          "reqYmd": "2025-04-20",
          "dvType": "DAY"
        }
      ]
    },
    "next": "vacation_confirmer",
    "thread_id": "26793581-bbda-4918-b7cc-b23b9e1ba990"
  },
  "metadata": {
    "thread_id": "26793581-bbda-4918-b7cc-b23b9e1ba990"
  }
}
```

### 5. 최종 확인 요청
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "네, 신청해주세요",
    "session_id": "26793581-bbda-4918-b7cc-b23b9e1ba990",
    "session_state": {
      "messages": [...],
      "vacation_info": {
        "drafterId": "01180001",
        "mstPid": 1,
        "dvType": "연차",
        "start_date": "2025-04-20",
        "end_date": "2025-04-20",
        "dayList": [
          {
            "reqYmd": "2025-04-20",
            "dvType": "DAY"
          }
        ]
      },
      "next": "vacation_confirmer",
      "thread_id": "26793581-bbda-4918-b7cc-b23b9e1ba990"
    },
    "agent_type": "general"
  }'
```

### 6. 신청 완료 응답
```json
{
  "response": "연차 신청이 완료되었습니다.",
  "session_id": "26793581-bbda-4918-b7cc-b23b9e1ba990",
  "session_state": {
    "messages": [...],
    "vacation_info": {
      "drafterId": "01180001",
      "mstPid": 1,
      "dvType": "연차",
      "start_date": "2025-04-20",
      "end_date": "2025-04-20",
      "dayList": [
        {
          "reqYmd": "2025-04-20",
          "dvType": "DAY"
        }
      ]
    },
    "next": "supervisor",
    "thread_id": "26793581-bbda-4918-b7cc-b23b9e1ba990"
  },
  "metadata": {
    "thread_id": "26793581-bbda-4918-b7cc-b23b9e1ba990"
  }
}
```

## API 문서

실행 중인 서버에서 다음 URL을 통해 전체 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 