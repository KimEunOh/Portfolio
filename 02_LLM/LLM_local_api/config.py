"""
이미지 RAG 챗봇 애플리케이션 설정
"""

import os
from pathlib import Path

# 기본 설정
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, "knowledge_base")
PDF_CACHE_DIR = os.path.join(KNOWLEDGE_BASE_DIR, "pdf_cache")
IMAGE_CACHE_DIR = os.path.join(KNOWLEDGE_BASE_DIR, "image_cache")
DOCUMENTS_DIR = os.path.join(BASE_DIR, "documents")

# 허용된 파일 확장자
ALLOWED_EXTENSIONS = {"pdf"}

# LLM API 설정
API_URL = os.getenv("API_URL", "http://localhost:8000/generate")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "60"))
API_MAX_RETRIES = int(os.getenv("API_MAX_RETRIES", "2"))
API_RETRY_DELAY = int(os.getenv("API_RETRY_DELAY", "5"))

# 생성 매개변수
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))

# 시스템 프롬프트
DEFAULT_SYSTEM_PROMPT = """
당신은 문서에 포함된 이미지를 기반으로 답변하는 도우미입니다.
문서에서 추출된 이미지를 분석하고 사용자의 질문에 관련된 정보를 제공해주세요.
이미지 내용을 상세히 설명하고, 이미지의 출처 정보도 함께 제공해주세요.
"""

# 캐시 설정
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "True").lower() in ("true", "1", "t")
CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "1000"))  # 최대 캐시 항목 수

# Flask 서버 설정
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
