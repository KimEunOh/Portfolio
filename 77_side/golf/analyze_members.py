import pandas as pd

# 엑셀 파일 읽기
df = pd.read_excel("2024.01.01 ~2024.12.31 종료된 회원.xlsx")

# 기본 정보 출력
print("데이터 형태:", df.shape)
print("\n열 목록:", list(df.columns))
print("\n데이터 샘플 (5개):")
print(df.head().to_string())

# 중복 회원 확인
print("\n\n중복 회원 분석:")
# 이름과 휴대폰번호로 그룹화하여 중복 확인
duplicates = df.groupby(["이름", "휴대폰번호"]).size().reset_index(name="중복수")
duplicates = duplicates[duplicates["중복수"] > 1].sort_values("중복수", ascending=False)

if not duplicates.empty:
    print(f"중복된 회원 수: {len(duplicates)}")
    print("\n가장 많이 중복된 회원 (상위 10명):")
    print(duplicates.head(10))
