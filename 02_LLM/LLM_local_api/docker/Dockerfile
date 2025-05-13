FROM python:3.9-slim

WORKDIR /app

# 필요한 시스템 라이브러리 설치
RUN apt-get update && apt-get install -y poppler-utils

# 필요한 파이썬 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 파일 복사
COPY . .

# .env 파일이 없는 경우 빈 파일 생성
RUN touch .env

# 앱 시작 포트
EXPOSE 8000
EXPOSE 8080

# 컨테이너 시작 시 실행할 명령
CMD ["python", "chat_with_image.py"] 