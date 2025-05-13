# LLM Local API

## 환경 설정

### 1. 환경 변수 설정
프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# OpenAI API 설정
OPENAI_API_KEY=your-api-key-here

# Grafana 설정
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=your-secure-password-here
GF_USERS_ALLOW_SIGN_UP=false
GF_INSTALL_PLUGINS=grafana-piechart-panel

# 애플리케이션 설정
PROMETHEUS_URL=http://prometheus:9090
ALLOW_DANGEROUS_DESERIALIZATION=True

# 메모리 설정
MEMORY_LIMIT=4G
MEMORY_RESERVATION=2G
```

### 2. 보안 주의사항
- `.env` 파일을 절대로 Git에 커밋하지 마세요
- 실제 운영 환경에서는 더 강력한 비밀번호를 사용하세요
- API 키는 정기적으로 순환하세요 