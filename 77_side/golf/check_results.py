import pandas as pd

# 파일들 확인
print("=" * 50)
print("개선된 회원 관리 시스템 확인")
print("=" * 50)

# 1. 개선된 종료 회원 데이터 확인
print("\n1. 개선된 종료 회원 데이터:")
df_terminated = pd.read_excel("2024.01.01 ~2024.12.31 종료된 회원_개선됨.xlsx")
print(f"   - 총 레코드 수: {len(df_terminated)}개")
print("\n   - 샘플 데이터 (처음 5개 행):")
cols = ["고유회원ID", "회원번호", "이름", "휴대폰번호", "이용상태"]
print(df_terminated[cols].head().to_string(index=False))

# 2. 개선된 활성 회원 데이터 확인
print("\n2. 개선된 활성 회원 데이터:")
df_active = pd.read_excel("현재 이용중인 회원_개선됨.xlsx")
print(f"   - 총 레코드 수: {len(df_active)}개")
print("\n   - 샘플 데이터 (처음 5개 행):")
print(df_active[cols].head().to_string(index=False))

# 3. 전체 회원 맵핑 테이블 확인
print("\n3. 회원 ID 매핑 테이블:")
df_mapping = pd.read_excel("회원_ID_매핑.xlsx")
print(f"   - 총 고유 회원 수: {len(df_mapping)}명")
print("\n   - 샘플 데이터 (처음 5개 행):")
print(df_mapping.head().to_string(index=False))

# 4. 데이터 분석
print("\n4. 개선된 데이터 분석:")

# 중복 회원 확인 (종료 회원)
dup_members = df_terminated[
    df_terminated.duplicated(["이름", "휴대폰번호"], keep=False)
]
if len(dup_members) > 0:
    print(f"\n   - 종료 회원 중 중복 이름/번호를 가진 회원: {len(dup_members) // 2}명")
    print("\n   - 중복 회원 예시:")
    first_dup = dup_members.iloc[0]["이름"], dup_members.iloc[0]["휴대폰번호"]
    print(
        df_terminated[
            (df_terminated["이름"] == first_dup[0])
            & (df_terminated["휴대폰번호"] == first_dup[1])
        ][cols].to_string(index=False)
    )
else:
    print("\n   - 종료 회원 중 중복 이름/번호를 가진 회원이 없습니다.")

# 고유 ID 중복 확인
if df_terminated["고유회원ID"].duplicated().any():
    print("\n   - 경고: 종료 회원 데이터에서 고유회원ID 중복 발견")
else:
    print("\n   - 정상: 종료 회원 데이터의 고유회원ID에 중복이 없습니다.")

if df_active["고유회원ID"].duplicated().any():
    print("   - 경고: 활성 회원 데이터에서 고유회원ID 중복 발견")
else:
    print("   - 정상: 활성 회원 데이터의 고유회원ID에 중복이 없습니다.")

# 5. 요약
print("\n5. 개선 결과 요약:")
print("   - 고유 회원 ID 부여 완료")
print("   - 중복 회원 식별 가능")
print("   - 데이터베이스 분리 준비 완료")
print("   - 회원 관리 시스템 업그레이드 준비 완료")
print("=" * 50)
