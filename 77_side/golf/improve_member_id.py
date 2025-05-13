import pandas as pd
import numpy as np
import os
from datetime import datetime

# 엑셀 파일 읽기
file_path = "2024.01.01 ~2024.12.31 종료된 회원.xlsx"
df = pd.read_excel(file_path)

print("=" * 60)
print("데이터 기본 정보")
print("=" * 60)
print(f"데이터 크기: {df.shape[0]}행 x {df.shape[1]}열")
print(f"열 목록: {', '.join(df.columns)}")

# 이름과 휴대폰번호 데이터 확인
print("\n" + "=" * 60)
print("중복 회원 분석")
print("=" * 60)

# 중복 회원 확인
duplicates = df.groupby(["이름", "휴대폰번호"]).size().reset_index(name="등록횟수")
duplicates = duplicates.sort_values("등록횟수", ascending=False)

# 등록 횟수 통계
print(f"총 레코드 수: {len(df)}")
print(f"고유 회원 수: {len(duplicates)}")
print(f"등록 횟수 1회 이상인 회원 수: {len(duplicates[duplicates['등록횟수'] > 1])}")
print(f"최대 등록 횟수: {duplicates['등록횟수'].max()}회")

# 상위 중복 회원 출력
print("\n가장 많이 등록된 회원 (상위 10명):")
print(duplicates.head(10).to_string(index=False))

# 중복 회원 예시 확인
print("\n" + "=" * 60)
print("중복 회원 상세 예시")
print("=" * 60)

if len(duplicates[duplicates["등록횟수"] > 1]) > 0:
    # 첫 번째 중복 회원 찾기
    first_dup = duplicates[duplicates["등록횟수"] > 1].iloc[0]
    name = first_dup["이름"]
    phone = first_dup["휴대폰번호"]

    # 해당 회원의 모든 레코드 조회
    member_records = df[(df["이름"] == name) & (df["휴대폰번호"] == phone)]
    print(f"회원명: {name}, 휴대폰: {phone}, 등록 횟수: {len(member_records)}")
    print("\n상세 레코드:")

    # 필요한 열만 선택하여 출력
    cols_to_show = [
        "회원번호",
        "이름",
        "휴대폰번호",
        "타석정기권",
        "타석쿠폰",
        "시설정기권",
        "이용상태",
    ]
    print(member_records[cols_to_show].to_string(index=False))

# 개선된 데이터 구조 생성
print("\n" + "=" * 60)
print("개선된 회원 관리 방안")
print("=" * 60)

# 1. 고유 회원 ID 생성
# 이름과 휴대폰번호를 기준으로 그룹화하여 고유 ID 부여
member_id_mapping = duplicates.copy()
member_id_mapping["고유회원ID"] = np.arange(1, len(member_id_mapping) + 1)
member_id_mapping = member_id_mapping[["이름", "휴대폰번호", "고유회원ID"]]

# 고유 ID 맵핑 적용
df_improved = df.merge(member_id_mapping, on=["이름", "휴대폰번호"], how="left")

# 2. 개선된 데이터 출력
print("1. 고유 회원 ID 부여")
print(f"   - 총 {len(df_improved)}개의 레코드에 고유 회원 ID 부여 완료")
print(f"   - 고유 회원 수: {len(member_id_mapping)}")

# 샘플 데이터 출력
cols_to_show = ["회원번호", "이름", "휴대폰번호", "고유회원ID", "이용상태"]
print("\n개선된 데이터 샘플 (처음 5개 행):")
print(df_improved[cols_to_show].head().to_string(index=False))

# 3. 테이블 구조 개선 방안
print("\n2. 데이터베이스 테이블 구조 개선 방안:")
print("   a) 회원 기본 정보 테이블")
print("      - 고유회원ID (PK): 불변하는 고유 식별자")
print("      - 이름: 회원 이름")
print("      - 휴대폰번호: 회원 연락처")
print("      - 회원등급: 회원 등급 정보")
print("      - 가입일: 최초 가입 날짜")
print("      - 상태: 회원 상태 (활성/비활성)")
print("      - 기타 기본 정보 (생년월일, 성별 등)")
print("")
print("   b) 이용권/쿠폰 테이블")
print("      - 이용권ID (PK): 이용권 고유 식별자")
print("      - 고유회원ID (FK): 회원 테이블 참조")
print("      - 이용권종류: 타석정기권/시설정기권/타석쿠폰 등 구분")
print("      - 이용권명: 상품명 (예: 골프 1개월)")
print("      - 시작일: 이용 시작일")
print("      - 종료일: 이용 종료일")
print("      - 상태: 이용 상태 (이용중/종료 등)")
print("")
print("   c) 이용 내역 테이블")
print("      - 이용내역ID (PK): 이용 내역 고유 식별자")
print("      - 고유회원ID (FK): 회원 테이블 참조")
print("      - 이용권ID (FK): 이용권 테이블 참조")
print("      - 이용일시: 이용한 날짜와 시간")
print("      - 이용내용: 이용한 서비스 내용")
print("")
print("3. 개선 효과:")
print("   - 한 회원의 모든 이용 내역을 고유회원ID로 쉽게 조회 가능")
print("   - 중복 등록 방지 및 동일 회원의 이력 관리 용이")
print("   - 회원별 이용 통계 및 분석 가능")
print("   - 데이터 무결성 및 일관성 유지")

# 4. 개선된 데이터 저장 (원본 백업 후 저장)
print("\n4. 개선된 데이터 저장 방법:")
print("   다음 명령으로 개선된 데이터를 저장할 수 있습니다:")
print("   ```")
print("   # 원본 백업")
print("   # import shutil")
print(
    "   # backup_file = file_path.replace('.xlsx', f'_backup_{datetime.now().strftime(\"%Y%m%d\")}.xlsx')"
)
print("   # shutil.copy2(file_path, backup_file)")
print("   # print(f'원본 파일 백업 완료: {backup_file}')")
print("")
print("   # 개선된 데이터 저장")
print("   # new_file = file_path.replace('.xlsx', '_개선됨.xlsx')")
print("   # df_improved.to_excel(new_file, index=False)")
print("   # print(f'개선된 파일 저장 완료: {new_file}')")
print("   ```")

# 5. 추가 권장사항
print("\n5. 추가 권장사항:")
print("   - 회원번호 발급 시 기존 회원은 기존 고유회원ID 사용 권장")
print("   - 회원 정보 수정 시 고유회원ID 기준으로 수정")
print("   - 새로운 이용권/쿠폰 등록 시 고유회원ID 연결")
print("   - 데이터베이스 시스템 도입 고려 (Excel 대신 관계형 DB 사용)")
print("=" * 60)
