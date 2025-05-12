# Otour - 여행 상품 분석 시스템

## 환경 설정

### 1. 환경 변수 설정
프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# 데이터베이스 설정
DB_USERNAME=your_username
DB_PASSWORD=your_secure_password
DB_HOSTNAME=your_db_host
DB_PORT=3306
DB_NAME=your_database_name

# Flask 설정
FLASK_ENV=development
FLASK_DEBUG=1
PORT=5001
```

### 2. 보안 주의사항
- `.env` 파일을 절대로 Git에 커밋하지 마세요
- 실제 운영 환경에서는 더 강력한 비밀번호를 사용하세요
- 운영 환경에서는 `FLASK_DEBUG=0`으로 설정하세요
- 데이터베이스 접속 정보는 정기적으로 변경하세요 