from models import User, init_db, SessionLocal
import uuid
import hashlib
import os


def hash_password(password: str) -> str:
    """비밀번호 해싱"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_admin_account():
    print("데이터베이스 초기화 시작...")

    # 기존 데이터베이스 파일이 있다면 삭제
    if os.path.exists("sqlite.db"):
        print("기존 데이터베이스 파일 삭제...")
        os.remove("sqlite.db")

    # 데이터베이스 초기화
    print("새 데이터베이스 생성...")
    init_db()

    # 데이터베이스 세션 생성
    print("데이터베이스 세션 생성...")
    db = SessionLocal()

    try:
        # 관리자 계정 생성
        admin_id = str(uuid.uuid4())
        admin_password = hash_password("admin123")

        print(f"관리자 계정 생성 시도...")
        print(f"관리자 ID: {admin_id}")
        print(f"해시된 비밀번호: {admin_password}")

        admin_user = User(
            id=admin_id,
            nickname="관리자",
            username="admin",
            password=admin_password,
            is_admin=True,
        )

        # 데이터베이스에 저장
        print("데이터베이스에 관리자 계정 저장...")
        db.add(admin_user)
        db.commit()

        # 저장된 계정 확인
        saved_user = db.query(User).filter(User.username == "admin").first()
        if saved_user:
            print("\n관리자 계정이 성공적으로 생성되었습니다.")
            print(f"관리자 ID: {saved_user.id}")
            print(f"관리자 사용자명: {saved_user.username}")
            print(f"관리자 닉네임: {saved_user.nickname}")
            print(f"관리자 여부: {saved_user.is_admin}")
            print(f"해시된 비밀번호: {saved_user.password}")
            print("\n로그인 정보:")
            print("사용자명: admin")
            print("비밀번호: admin123")
        else:
            print("오류: 관리자 계정이 데이터베이스에 저장되지 않았습니다.")

    except Exception as e:
        print(f"관리자 계정 생성 중 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_account()
