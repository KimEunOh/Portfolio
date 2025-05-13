import pandas as pd
import numpy as np
import shutil
from datetime import datetime
import os

# 현재 작업 디렉토리 확인
print(f"현재 작업 디렉토리: {os.getcwd()}")

# 1. 엑셀 파일 읽기
print("1. 원본 데이터 파일 읽기 중...")
file_path = "2024.01.01 ~2024.12.31 종료된 회원.xlsx"
df = pd.read_excel(file_path)
print(f"   - 종료 회원 데이터 크기: {df.shape[0]}행 x {df.shape[1]}열")

# 현재 활성 회원 데이터 읽기
active_members_file = "현재 이용중인 회원.xlsx"
try:
    active_df = pd.read_excel(active_members_file)
    print(
        f"   - 활성 회원 데이터 크기: {active_df.shape[0]}행 x {active_df.shape[1]}열"
    )
    has_active_data = True
except FileNotFoundError:
    print(f"   - 현재 이용중인 회원 파일을 찾을 수 없습니다: {active_members_file}")
    has_active_data = False

# 2. 고유한 회원 목록 생성 (종료 회원 + 활성 회원)
print("2. 모든 회원 데이터 통합 중...")
# 이름과 휴대폰번호를 기준으로 중복 제거
all_members = df[["이름", "휴대폰번호"]].drop_duplicates()
if has_active_data:
    active_members = active_df[["이름", "휴대폰번호"]].drop_duplicates()
    all_members = pd.concat([all_members, active_members]).drop_duplicates()

print(f"   - 총 고유 회원 수: {len(all_members)}명")

# 3. 새로운 형식의 고유회원ID 생성 (D-YYYYMM-NNN)
print("3. 새로운 형식의 고유회원ID 생성 중...")

# 현재 연월 가져오기
current_yyyymm = datetime.now().strftime("%Y%m")

# 회원 데이터에 새 ID 형식 부여
all_members = all_members.reset_index(drop=True)
all_members["고유회원ID"] = all_members.index.map(
    lambda x: f"D-{current_yyyymm}-{str(x+1).zfill(3)}"
)

# 출력 확인
print("\n새 고유회원ID 형식 예시 (처음 5개):")
print(all_members.head().to_string(index=False))

# 4. 종료 회원 데이터에 새 ID 적용
print("\n4. 종료 회원 데이터에 새 ID 형식 적용 중...")
df_improved = df.merge(all_members, on=["이름", "휴대폰번호"], how="left")

# 열 순서 재정렬 - 고유회원ID를 앞쪽으로 배치
new_column_order = ["고유회원ID", "회원번호", "이름", "휴대폰번호"] + [
    col
    for col in df_improved.columns
    if col not in ["고유회원ID", "회원번호", "이름", "휴대폰번호"]
]
df_improved = df_improved[new_column_order]

# 원본 백업
backup_file = file_path.replace(
    ".xlsx", f'_backup_{datetime.now().strftime("%Y%m%d")}.xlsx'
)
shutil.copy2(file_path, backup_file)
print(f"   - 원본 파일 백업 완료: {backup_file}")

# 개선된 데이터 저장
new_file = file_path.replace(".xlsx", "_개선됨_새ID.xlsx")
df_improved.to_excel(new_file, index=False)
print(f"   - 개선된 종료 회원 파일 저장 완료: {new_file}")

# 5. 활성 회원 데이터에 새 ID 적용
if has_active_data:
    print("\n5. 활성 회원 데이터에 새 ID 형식 적용 중...")
    active_df_improved = active_df.merge(
        all_members, on=["이름", "휴대폰번호"], how="left"
    )

    # 열 순서 재정렬
    new_column_order = ["고유회원ID", "회원번호", "이름", "휴대폰번호"] + [
        col
        for col in active_df_improved.columns
        if col not in ["고유회원ID", "회원번호", "이름", "휴대폰번호"]
    ]
    active_df_improved = active_df_improved[new_column_order]

    # 백업
    active_backup_file = active_members_file.replace(
        ".xlsx", f'_backup_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )
    shutil.copy2(active_members_file, active_backup_file)

    # 개선된 활성 회원 데이터 저장
    active_new_file = active_members_file.replace(".xlsx", "_개선됨_새ID.xlsx")
    active_df_improved.to_excel(active_new_file, index=False)
    print(f"   - 개선된 활성 회원 파일 저장 완료: {active_new_file}")

# 6. 회원 ID 매핑 테이블 저장
print("\n6. 회원 ID 매핑 테이블 저장 중...")
mapping_file = "회원_ID_매핑_새형식.xlsx"
all_members.to_excel(mapping_file, index=False)
print(f"   - 전체 회원 ID 매핑 테이블 저장 완료: {mapping_file}")

# 7. 요약 출력
print("\n작업이 완료되었습니다! 다음 파일들을 확인하세요:")
print(f"1. 개선된 종료 회원 데이터: {new_file}")
print(f"2. 원본 백업 파일: {backup_file}")
if has_active_data:
    print(f"3. 개선된 활성 회원 데이터: {active_new_file}")
    print(f"4. 활성 회원 원본 백업: {active_backup_file}")
print(f"5. 새 형식의 회원 ID 매핑 테이블: {mapping_file}")

print("\n새 고유회원ID 형식: D-YYYYMM-NNN")
print("  - D: 구분자 (지정한 D 사용)")
print("  - YYYYMM: 현재 연월 (예: 202505)")
print("  - NNN: 일련번호 (001부터 시작)")
print("  - 예시: D-202505-001")
