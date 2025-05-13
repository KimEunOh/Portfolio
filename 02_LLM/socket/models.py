from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    func,
    Float,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import os
import json

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    nickname = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    messages = relationship("Message", back_populates="user")
    room_stats = relationship("RoomStats", back_populates="user")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: os.urandom(16).hex())
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)
    room_id = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'user', 'admin', 'system'
    timestamp = Column(DateTime, default=datetime.now)
    user = relationship("User", back_populates="messages")


class RoomStats(Base):
    __tablename__ = "room_stats"

    id = Column(String, primary_key=True, default=lambda: os.urandom(16).hex())
    room_id = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    join_count = Column(Integer, default=0)  # 입장 횟수
    message_count = Column(Integer, default=0)  # 메시지 수
    total_time = Column(Integer, default=0)  # 총 체류 시간(초)
    last_join = Column(DateTime)  # 마지막 입장 시간
    last_active = Column(DateTime)  # 마지막 활동 시간
    user = relationship("User", back_populates="room_stats")


class DailyStats(Base):
    __tablename__ = "daily_stats"

    id = Column(String, primary_key=True, default=lambda: os.urandom(16).hex())
    date = Column(DateTime, nullable=False)
    room_id = Column(String, nullable=False)
    total_messages = Column(Integer, default=0)
    unique_users = Column(Integer, default=0)
    admin_messages = Column(Integer, default=0)
    peak_users = Column(Integer, default=0)
    active_time_distribution = Column(String)  # JSON 형식으로 시간대별 활동량 저장

    # 새로운 통계 필드들
    avg_message_length = Column(Integer, default=0)  # 평균 메시지 길이
    response_times = Column(String, default="{}")  # JSON: 메시지 응답 시간 분포
    user_participation = Column(String, default="{}")  # JSON: 사용자별 참여도
    room_transitions = Column(String, default="{}")  # JSON: 채팅방 간 이동 패턴
    error_counts = Column(String, default="{}")  # JSON: 오류 발생 통계
    keywords = Column(String, default="{}")  # JSON: 주요 키워드/토픽
    performance_metrics = Column(String, default="{}")  # JSON: 성능 관련 메트릭


class SystemMetrics(Base):
    __tablename__ = "system_metrics"

    id = Column(String, primary_key=True, default=lambda: os.urandom(16).hex())
    timestamp = Column(DateTime, default=datetime.now)
    room_id = Column(String, nullable=False)

    # WebSocket 연결 관련
    connected_clients = Column(Integer, default=0)
    connection_errors = Column(Integer, default=0)
    avg_latency = Column(Float, default=0.0)  # 밀리초 단위

    # 메시지 처리 관련
    messages_per_second = Column(Float, default=0.0)
    message_queue_size = Column(Integer, default=0)
    failed_messages = Column(Integer, default=0)

    # 시스템 리소스
    cpu_usage = Column(Float, default=0.0)  # 퍼센트
    memory_usage = Column(Float, default=0.0)  # 메가바이트

    # 오류 통계
    error_count = Column(Integer, default=0)
    error_types = Column(String, default="{}")  # JSON 형식으로 오류 유형 저장


# 데이터베이스 파일 경로
DB_FILE = "chat.db"

# 데이터베이스 연결 설정
engine = create_engine(
    f"sqlite:///{DB_FILE}",
    pool_size=20,  # 커넥션 풀 크기 증가
    max_overflow=30,  # 최대 오버플로우 증가
    pool_timeout=60,  # 타임아웃 시간 증가
    pool_recycle=1800,  # 30분마다 커넥션 재활용
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 데이터베이스 테이블 생성
def init_db():
    """데이터베이스 초기화 및 테이블 생성"""
    # 기존 데이터베이스 파일이 있다면 삭제
    if os.path.exists(DB_FILE):
        print(f"기존 데이터베이스 파일 삭제: {DB_FILE}")
        os.remove(DB_FILE)

    # 테이블 생성
    print("데이터베이스 테이블 생성...")
    Base.metadata.create_all(bind=engine)
    print("데이터베이스 초기화가 완료되었습니다.")


# 데이터베이스 세션 관리
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
