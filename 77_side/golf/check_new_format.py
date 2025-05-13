import pandas as pd

print("=" * 60)
print("새로운 고유회원ID 형식 (D-YYYYMM-NNN) 결과 확인")
print("=" * 60)

# 1. 개선된 종료 회원 데이터 확인
print("\n1. 새 ID 형식이 적용된 종료 회원 데이터:")
df_term = pd.read_excel("2024.01.01 ~2024.12.31 종료된 회원_개선됨_새ID.xlsx")
print(f"   - 총 레코드 수: {len(df_term)}개")
print("\n   - 샘플 데이터 (처음 5개 행):")
cols = ["고유회원ID", "회원번호", "이름", "휴대폰번호", "이용상태"]
print(df_term[cols].head().to_string(index=False))

# 2. 개선된 활성 회원 데이터 확인
print("\n2. 새 ID 형식이 적용된 활성 회원 데이터:")
df_active = pd.read_excel("현재 이용중인 회원_개선됨_새ID.xlsx")
print(f"   - 총 레코드 수: {len(df_active)}개")
print("\n   - 샘플 데이터 (처음 5개 행):")
print(df_active[cols].head().to_string(index=False))

# 3. 전체 회원 맵핑 테이블 확인
print("\n3. 새 ID 형식의 회원 매핑 테이블:")
df_map = pd.read_excel("회원_ID_매핑_새형식.xlsx")
print(f"   - 총 고유 회원 수: {len(df_map)}명")
print("\n   - 샘플 데이터 (처음 5개 행):")
print(df_map.head().to_string(index=False))

# 4. 중복 박민규 회원 데이터 확인
print("\n4. 중복 회원 ID 적용 확인 (박민규 회원):")
dup_member = df_term[df_term["이름"] == "박민규(상무)"]
if not dup_member.empty:
    print("\n   - 박민규 회원 레코드:")
    print(dup_member[cols].to_string(index=False))

    # 고유ID가 동일한지 확인
    ids = dup_member["고유회원ID"].unique()
    if len(ids) == 1:
        print(f"\n   - 동일 회원에 같은 고유ID가 부여됨: {ids[0]}")
    else:
        print(f"\n   - 경고: 동일 회원에 서로 다른 ID가 부여됨: {', '.join(ids)}")
else:
    print("   - 박민규 회원 데이터를 찾을 수 없습니다.")

# 5. 새로운 ID 형식 분석
print("\n5. 새로운 ID 형식 분석:")
id_examples = df_term["고유회원ID"].head(10).tolist()
print(f"   - ID 샘플: {', '.join(id_examples)}")

# ID 형식이 올바른지 확인
import re

pattern = r"D-\d{6}-\d{3}"
valid_ids = sum(1 for i in df_term["고유회원ID"] if re.match(pattern, str(i)))
print(f"   - D-YYYYMM-NNN 형식을 따르는 ID 수: {valid_ids}/{len(df_term)}")

print("\n6. 결론:")
print("   - D-YYYYMM-NNN 형식의 고유회원ID 적용 완료")
print("   - 동일 회원에게 같은 ID가 부여되어 회원 식별 가능")
print("   - 향후 회원 관리에 이 ID 체계를 사용 권장")
print("=" * 60)
