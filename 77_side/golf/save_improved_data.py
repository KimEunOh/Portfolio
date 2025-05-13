import pandas as pd
import numpy as np
import shutil
from datetime import datetime

# 1. 엑셀 파일 읽기
print("1. 원본 데이터 파일 읽기 중...")
file_path = "2024.01.01 ~2024.12.31 종료된 회원.xlsx"
df = pd.read_excel(file_path)
print(f"   - 데이터 크기: {df.shape[0]}행 x {df.shape[1]}열")

# 2. 고유 회원 ID 생성
print("2. 고유 회원 ID 생성 중...")
# 이름과 휴대폰번호를 기준으로 그룹화하여 고유 ID 부여
duplicates = df.groupby(["이름", "휴대폰번호"]).size().reset_index(name="등록횟수")
duplicates = duplicates.sort_values("등록횟수", ascending=False)

member_id_mapping = duplicates.copy()
member_id_mapping["고유회원ID"] = np.arange(1, len(member_id_mapping) + 1)
member_id_mapping = member_id_mapping[["이름", "휴대폰번호", "고유회원ID"]]
print(f"   - 고유 회원 수: {len(member_id_mapping)}")

# 3. 고유 ID 맵핑 적용
print("3. 고유 회원 ID 맵핑 적용 중...")
df_improved = df.merge(member_id_mapping, on=["이름", "휴대폰번호"], how="left")
print(f"   - 총 {len(df_improved)}개의 레코드에 고유 회원 ID 부여 완료")

# 4. 원본 파일 백업
print("4. 원본 파일 백업 중...")
backup_file = file_path.replace(
    ".xlsx", f'_backup_{datetime.now().strftime("%Y%m%d")}.xlsx'
)
shutil.copy2(file_path, backup_file)
print(f"   - 원본 파일 백업 완료: {backup_file}")

# 5. 개선된 데이터 저장
print("5. 개선된 데이터 저장 중...")
# 열 순서 재정렬 - 고유회원ID를 앞쪽으로 배치
new_column_order = ["고유회원ID", "회원번호", "이름", "휴대폰번호"] + [
    col
    for col in df_improved.columns
    if col not in ["고유회원ID", "회원번호", "이름", "휴대폰번호"]
]
df_improved = df_improved[new_column_order]

# 개선된 데이터 저장
new_file = file_path.replace(".xlsx", "_개선됨.xlsx")
df_improved.to_excel(new_file, index=False)
print(f"   - 개선된 파일 저장 완료: {new_file}")

# 6. 현재 활성 회원 고유 ID 목록 생성
print("6. 현재 활성 회원 목록 생성 중...")

# 현재 활성 회원 데이터 있는지 확인
active_members_file = "현재 이용중인 회원.xlsx"
try:
    active_df = pd.read_excel(active_members_file)

    # 고유 ID 맵핑
    active_df_improved = active_df.merge(
        member_id_mapping, on=["이름", "휴대폰번호"], how="left"
    )

    # 고유 ID가 없는 신규 회원 처리
    missing_ids = active_df_improved[active_df_improved["고유회원ID"].isna()]
    if len(missing_ids) > 0:
        print(f"   - 고유 ID가 없는 신규 회원 발견: {len(missing_ids)}명")
        # 신규 고유 ID 생성 (기존 ID 이후부터)
        max_id = member_id_mapping["고유회원ID"].max()

        # 신규 회원 맵핑 생성
        new_members = missing_ids[["이름", "휴대폰번호"]].drop_duplicates()
        new_members["고유회원ID"] = np.arange(max_id + 1, max_id + 1 + len(new_members))

        # 최종 매핑 테이블에 추가
        member_id_mapping = pd.concat([member_id_mapping, new_members])

        # 다시 맵핑 적용
        active_df_improved = active_df.merge(
            member_id_mapping, on=["이름", "휴대폰번호"], how="left"
        )

    # 열 순서 재정렬
    new_column_order = ["고유회원ID", "회원번호", "이름", "휴대폰번호"] + [
        col
        for col in active_df_improved.columns
        if col not in ["고유회원ID", "회원번호", "이름", "휴대폰번호"]
    ]
    active_df_improved = active_df_improved[new_column_order]

    # 개선된 활성 회원 데이터 저장
    active_new_file = active_members_file.replace(".xlsx", "_개선됨.xlsx")
    active_df_improved.to_excel(active_new_file, index=False)
    print(f"   - 개선된 활성 회원 파일 저장 완료: {active_new_file}")

    # 전체 회원 ID 매핑 테이블 저장
    mapping_file = "회원_ID_매핑.xlsx"
    member_id_mapping.to_excel(mapping_file, index=False)
    print(f"   - 전체 회원 ID 매핑 테이블 저장 완료: {mapping_file}")

except FileNotFoundError:
    print(f"   - 현재 이용중인 회원 파일을 찾을 수 없습니다: {active_members_file}")

print("\n작업이 완료되었습니다! 다음 파일들을 확인하세요:")
print(f"1. 개선된 종료 회원 데이터: {new_file}")
print(f"2. 원본 백업 파일: {backup_file}")
if "active_new_file" in locals():
    print(f"3. 개선된 활성 회원 데이터: {active_new_file}")
if "mapping_file" in locals():
    print(f"4. 전체 회원 ID 매핑 테이블: {mapping_file}")
