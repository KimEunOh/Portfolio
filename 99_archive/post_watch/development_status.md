# 개발 상태 및 진행 상황

이 문서는 Post Watch AI 프로젝트의 개발 상태와 각 모듈의 구현 현황을 추적합니다.

## 개발 로드맵

- [x] **Phase 0: 설계 및 초기 설정**
  - [x] `design-document.md` 작성
  - [x] `architecture.md` 작성
  - [x] 프로젝트 구조 생성
  - [x] 기본 파일 생성 (`.gitignore`, `requirements.txt`, `README.md` 등)

- [x] **Phase 1: 핵심 기능 구현**
  - [x] `src/utils/config.py`: 설정 로딩 모듈 구현
  - [x] `src/db/database.py`: 데이터베이스 관리 모듈 구현
  - [x] `tests/db/test_database.py`: 데이터베이스 모듈 단위 테스트 작성
  - [x] `src/core/crawler.py`: 크롤러 모듈 구현
  - [x] `tests/core/test_crawler.py`: 크롤러 모듈 단위 테스트 작성

- [x] **Phase 2: 비즈니스 로직 및 AI 연동**
  - [x] `src/core/detector.py`: 신규 게시물 감지 로직 구현
  - [x] `tests/core/test_detector.py`: 감지 로직 단위 테스트 작성
  - [ ] `src/core/summarizer.py`: AI 요약 모듈 구현
  - [ ] `tests/core/test_summarizer.py`: 요약 모듈 단위 테스트 작성

- [ ] **Phase 3: 메신저 연동 및 통합**
  - [x] `src/messenger/discord_sender.py`: 디스코드 전송 모듈 구현
  - [ ] `tests/messenger/test_discord_sender.py`: 전송 모듈 단위 테스트 작성
  - [ ] `src/__main__.py`: 전체 시스템 통합 및 실행 로직 구현

- [ ] **Phase 4: 배포 및 안정화**
  - [ ] 최종 테스트 및 버그 수정
  - [ ] `README.md` 문서 최종 업데이트
  - [ ] 배포

## 모듈별 상세 현황

| 모듈 경로                      | 상태       | 담당자 | 비고 |
| ------------------------------ | ---------- | ------ | ---- |
| `src/utils/config.py`          | `Done`     | -      | 완료 |
| `src/db/database.py`           | `Done`     | -      | 완료 |
| `src/core/crawler.py`          | `Done`     | -      | 완료 |
| `tests/core/test_crawler.py`   | `Done`     | -      | 완료 |
| `src/core/detector.py`         | `Done`     | -      | 완료 |
| `tests/core/test_detector.py`  | `Done`     | -      | 완료 |
| `src/core/summarizer.py`       | `To Do`    | -      |      |
| `tests/core/test_summarizer.py`| `To Do`    | -      |      |
| `src/messenger/discord_sender.py`| `Done`   | -      | 완료 |
| `tests/messenger/test_discord_sender.py`| `To Do` | - |      |
| `src/__main__.py`              | `To Do`    | -      |      | 