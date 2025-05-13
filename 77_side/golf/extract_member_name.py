import pandas as pd
import re
import os


def extract_base_name(full_name):
    """
    이름(추가정보) 형식에서 순수 이름 부분만 추출합니다.
    예: '박민규(상무)' -> '박민규'
    """
    # 괄호가 있는 경우
    if "(" in full_name and ")" in full_name:
        base_name = full_name.split("(")[0].strip()
        return base_name
    # 괄호가 없는 경우 원래 이름 반환
    return full_name


# 파일 경로 정의
terminated_file = "2024.01.01 ~2024.12.31 종료된 회원_개선됨_새ID.xlsx"
active_file = "현재 이용중인 회원_개선됨_새ID.xlsx"
mapping_file = "회원_ID_매핑_새형식.xlsx"

print("=" * 70)
print("회원 이름 순수 추출 및 고유 ID 재매핑")
print("=" * 70)

# 파일 존재 확인
files_exist = True
for file_path in [terminated_file, active_file, mapping_file]:
    if not os.path.exists(file_path):
        print(f"오류: 파일을 찾을 수 없습니다: {file_path}")
        files_exist = False

if not files_exist:
    print("필요한 모든 파일이 존재하지 않습니다. 프로그램을 종료합니다.")
    exit(1)

# 1. 매핑 테이블 읽기
print("\n1. 기존 ID 매핑 테이블 읽기")
mapping_df = pd.read_excel(mapping_file)
print(f"   - 매핑 테이블 크기: {len(mapping_df)}개 레코드")

# 2. 이름에서 괄호 부분 제거한 순수 이름 추출
print("\n2. 순수 이름 추출 중...")
mapping_df["순수이름"] = mapping_df["이름"].apply(extract_base_name)

# 예시 출력
print("\n   - 이름 변환 예시:")
sample_names = mapping_df[["이름", "순수이름"]].head(10)
print(sample_names.to_string(index=False))

# 3. 순수이름과 휴대폰번호로 새로운 고유ID 매핑 생성
print("\n3. 순수이름과 휴대폰번호 기준으로 고유ID 재매핑 중...")

# 순수이름과 휴대폰 번호를 기준으로 그룹화
grouped = mapping_df.groupby(["순수이름", "휴대폰번호"]).first().reset_index()
print(f"   - 순수이름 기준 고유회원 수: {len(grouped)}명")

# 변경된 사례 찾기
changes = len(mapping_df) - len(grouped)
print(f"   - 동일인으로 통합된 회원 수: {changes}명")

if changes > 0:
    # 변경 사례 예시 찾기
    print("\n4. 동일인으로 통합된 사례:")
    # 순수이름과 전화번호가 같은데 원래 이름이 다른 경우 찾기
    duplicates = mapping_df.groupby(["순수이름", "휴대폰번호"]).filter(
        lambda x: len(x) > 1
    )

    if len(duplicates) > 0:
        # 처음 5개 변경 사례만 출력
        examples = duplicates.sort_values(["순수이름", "휴대폰번호"]).head(10)
        for idx, (name, phone) in enumerate(
            examples[["순수이름", "휴대폰번호"]].drop_duplicates().values
        ):
            if idx >= 5:
                break
            same_persons = mapping_df[
                (mapping_df["순수이름"] == name) & (mapping_df["휴대폰번호"] == phone)
            ]
            print(f"\n   사례 {idx+1}: {name}, {phone}")
            print(f"   동일인으로 확인된 레코드:")
            print(
                same_persons[["이름", "휴대폰번호", "고유회원ID"]].to_string(
                    index=False
                )
            )

    # 통합 매핑 테이블 생성 - 순수이름과 휴대폰번호 기준으로 새 ID 부여
    print("\n5. 새로운 매핑 테이블 생성 중...")
    # 기존 ID 형식(D-YYYYMM-NNN) 유지하면서 새로운 매핑 생성
    import datetime

    current_yyyymm = datetime.datetime.now().strftime("%Y%m")

    # 새로운 ID 부여
    grouped["새고유회원ID"] = grouped.reset_index().index.map(
        lambda x: f"D-{current_yyyymm}-{str(x+1).zfill(3)}"
    )

    # 원본 매핑 테이블에 새 ID 병합
    id_mapping = grouped[["순수이름", "휴대폰번호", "새고유회원ID"]]

    # 매핑 테이블 저장
    new_mapping_file = "회원_ID_매핑_순수이름.xlsx"
    id_mapping.to_excel(new_mapping_file, index=False)
    print(f"   - 새 매핑 테이블 저장 완료: {new_mapping_file}")

    # 6. 종료 회원 데이터에 새 ID 적용
    print("\n6. 종료 회원 데이터에 새 ID 적용 중...")
    terminated_df = pd.read_excel(terminated_file)

    # 순수이름 추출
    terminated_df["순수이름"] = terminated_df["이름"].apply(extract_base_name)

    # 새 ID 적용
    terminated_df = terminated_df.merge(
        id_mapping, on=["순수이름", "휴대폰번호"], how="left"
    )

    # 기존 ID 컬럼 교체
    terminated_df["기존고유회원ID"] = terminated_df["고유회원ID"]
    terminated_df["고유회원ID"] = terminated_df["새고유회원ID"]

    # 불필요한 컬럼 삭제
    terminated_df = terminated_df.drop(["순수이름", "새고유회원ID"], axis=1)

    # 저장
    new_terminated_file = "2024.01.01 ~2024.12.31 종료된 회원_순수이름.xlsx"
    terminated_df.to_excel(new_terminated_file, index=False)
    print(f"   - 새 종료 회원 파일 저장 완료: {new_terminated_file}")

    # 7. 활성 회원 데이터에 새 ID 적용
    print("\n7. 활성 회원 데이터에 새 ID 적용 중...")
    active_df = pd.read_excel(active_file)

    # 순수이름 추출
    active_df["순수이름"] = active_df["이름"].apply(extract_base_name)

    # 새 ID 적용
    active_df = active_df.merge(id_mapping, on=["순수이름", "휴대폰번호"], how="left")

    # 기존 ID 컬럼 교체
    active_df["기존고유회원ID"] = active_df["고유회원ID"]
    active_df["고유회원ID"] = active_df["새고유회원ID"]

    # 불필요한 컬럼 삭제
    active_df = active_df.drop(["순수이름", "새고유회원ID"], axis=1)

    # 저장
    new_active_file = "현재 이용중인 회원_순수이름.xlsx"
    active_df.to_excel(new_active_file, index=False)
    print(f"   - 새 활성 회원 파일 저장 완료: {new_active_file}")

    print("\n작업 완료! 다음 파일들을 확인하세요:")
    print(f"1. 새 매핑 테이블: {new_mapping_file}")
    print(f"2. 새 종료 회원 데이터: {new_terminated_file}")
    print(f"3. 새 활성 회원 데이터: {new_active_file}")
else:
    print("\n변경된 사항이 없습니다. 모든 회원이 이미 고유하게 식별되어 있습니다.")

print("\n" + "=" * 70)
