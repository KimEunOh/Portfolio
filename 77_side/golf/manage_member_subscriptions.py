import pandas as pd
import numpy as np
from datetime import datetime
import os

print("=" * 70)
print("회원별 이용권 정보 관리 시스템")
print("=" * 70)

# 1. 개선된 파일 읽기
print("\n1. 개선된 회원 데이터 파일 읽기")
improved_file = "2024.01.01 ~2024.12.31 종료된 회원_개선됨_새ID.xlsx"
active_file = "현재 이용중인 회원_개선됨_새ID.xlsx"

try:
    df_terminated = pd.read_excel(improved_file)
    print(f"   - 종료 회원 데이터: {len(df_terminated)}개 레코드")

    df_active = pd.read_excel(active_file)
    print(f"   - 활성 회원 데이터: {len(df_active)}개 레코드")

    # 두 데이터 합치기
    all_members = pd.concat([df_terminated, df_active])
    print(f"   - 전체 회원 데이터: {len(all_members)}개 레코드")
except FileNotFoundError as e:
    print(f"   - 오류: {e}")
    exit(1)

# 2. 이용권 관련 열 추출
print("\n2. 이용권 관련 정보 추출 중...")

# 이용권 관련 열 목록
subscription_columns = [
    "고유회원ID",
    "이름",
    "휴대폰번호",
    "타석정기권",
    "타석정기권종료일",
    "타석정기권이용상태",
    "타석쿠폰",
    "타석쿠폰종료일",
    "타석쿠폰이용상태",
    "시설정기권",
    "시설정기권종료일",
    "시설정기권이용상태",
    "시설쿠폰",
    "시설쿠폰종료일",
    "시설쿠폰이용상태",
    "예약정기권",
    "예약정기권종료일",
    "예약정기권이용상태",
    "예약쿠폰",
    "예약쿠폰종료일",
    "예약쿠폰이용상태",
    "레슨상품",
    "레슨상품종료일",
    "레슨상품이용상태",
    "이용상태",
]

# 필요한 열만 추출
subscriptions_df = all_members[subscription_columns].copy()

# 3. 회원별 이용권 현황 분석
print("\n3. 회원별 이용권 현황 분석 중...")

# 이용권 종류 목록
subscription_types = [
    "타석정기권",
    "타석쿠폰",
    "시설정기권",
    "시설쿠폰",
    "예약정기권",
    "예약쿠폰",
    "레슨상품",
]

# 이용권 보유 현황 계산
has_subscription = pd.DataFrame({"고유회원ID": subscriptions_df["고유회원ID"].unique()})
has_subscription = has_subscription.set_index("고유회원ID")

for sub_type in subscription_types:
    # 이용권 보유 회원 수 계산
    has_sub = subscriptions_df[subscriptions_df[sub_type].notna()].drop_duplicates(
        "고유회원ID"
    )
    print(f"   - {sub_type} 보유 회원 수: {len(has_sub)}명")

    # 회원별 이용권 보유 여부 표시
    has_subscription[f"{sub_type}_보유"] = False
    has_subscription.loc[has_sub["고유회원ID"], f"{sub_type}_보유"] = True

# 4. 이용권별 상세 정보 추출 - 한 회원이 여러 이용권을 가질 수 있음
print("\n4. 이용권별 상세 정보 추출 중...")


# 이용권 데이터 생성 함수
def extract_subscription_details(row, sub_type):
    if pd.isna(row[sub_type]):
        return None

    return {
        "고유회원ID": row["고유회원ID"],
        "이름": row["이름"],
        "휴대폰번호": row["휴대폰번호"],
        "이용권종류": sub_type,
        "이용권명": row[sub_type],
        "종료일": (
            row[f"{sub_type}종료일"] if not pd.isna(row[f"{sub_type}종료일"]) else None
        ),
        "이용상태": (
            row[f"{sub_type}이용상태"]
            if not pd.isna(row[f"{sub_type}이용상태"])
            else "알 수 없음"
        ),
        "회원상태": row["이용상태"],
    }


# 모든 이용권 데이터 추출
all_subscriptions = []

for _, row in subscriptions_df.iterrows():
    for sub_type in subscription_types:
        sub_data = extract_subscription_details(row, sub_type)
        if sub_data:
            all_subscriptions.append(sub_data)

# 이용권 데이터프레임 생성
subscriptions_details_df = pd.DataFrame(all_subscriptions)
print(f"   - 총 이용권 수: {len(subscriptions_details_df)}개")

# 5. 회원별 이용권 요약 생성
print("\n5. 회원별 이용권 요약 생성 중...")

# 회원별 이용권 수 계산
member_summary = (
    subscriptions_details_df.groupby("고유회원ID")
    .agg(
        이용권수=("이용권종류", "count"),
        이름=("이름", "first"),
        휴대폰번호=("휴대폰번호", "first"),
        보유이용권=("이용권명", lambda x: ", ".join(x.dropna().unique())),
        회원상태=("회원상태", "first"),
    )
    .reset_index()
)

print(f"   - 이용권을 보유한 회원 수: {len(member_summary)}명")
print("\n   - 회원별 이용권 요약 (상위 5명):")
print(member_summary.head().to_string(index=False))

# 6. 파일로 저장
print("\n6. 이용권 데이터 저장 중...")

# 저장할 파일명
subscription_file = "회원별_이용권_정보.xlsx"
summary_file = "회원별_이용권_요약.xlsx"

# 엑셀 파일로 저장
with pd.ExcelWriter(subscription_file) as writer:
    subscriptions_details_df.to_excel(writer, sheet_name="이용권상세", index=False)
    has_subscription.reset_index().to_excel(
        writer, sheet_name="이용권보유현황", index=False
    )

print(f"   - 이용권 상세 정보 저장 완료: {subscription_file}")

member_summary.to_excel(summary_file, index=False)
print(f"   - 회원별 이용권 요약 저장 완료: {summary_file}")

# 7. 이용권 통계 분석
print("\n7. 이용권 통계 분석:")

# 이용권 종류별 통계
subscription_stats = subscriptions_details_df["이용권종류"].value_counts().reset_index()
subscription_stats.columns = ["이용권종류", "개수"]
print("\n   - 이용권 종류별 통계:")
print(subscription_stats.to_string(index=False))

# 이용상태별 통계
status_stats = subscriptions_details_df["이용상태"].value_counts().reset_index()
status_stats.columns = ["이용상태", "개수"]
print("\n   - 이용상태별 통계:")
print(status_stats.to_string(index=False))

# 회원상태별 통계
member_stats = subscriptions_details_df["회원상태"].value_counts().reset_index()
member_stats.columns = ["회원상태", "개수"]
print("\n   - 회원상태별 통계:")
print(member_stats.to_string(index=False))

# 8. 이용권 검색 기능 함수 제공
print("\n8. 이용권 검색 함수 제공:")
print(
    """
다음 파이썬 코드를 사용하여 특정 회원의 이용권 정보를 검색할 수 있습니다:

```python
# 회원 검색 함수
def search_member_subscriptions(member_id=None, name=None, phone=None):
    \"\"\"
    회원ID, 이름 또는 휴대폰번호로 회원의 이용권 정보를 검색합니다.
    
    Args:
        member_id (str): 고유회원ID (예: 'D-202505-001')
        name (str): 회원 이름 (예: '홍길동')
        phone (str): 휴대폰번호 (예: '01012345678')
        
    Returns:
        DataFrame: 검색된 회원의 이용권 정보
    \"\"\"
    if member_id:
        return subscriptions_details_df[subscriptions_details_df['고유회원ID'] == member_id]
    elif name:
        return subscriptions_details_df[subscriptions_details_df['이름'].str.contains(name)]
    elif phone:
        return subscriptions_details_df[subscriptions_details_df['휴대폰번호'].str.contains(phone)]
    else:
        return pd.DataFrame()  # 빈 결과 반환

# 사용 예시:
# 고유회원ID로 검색
result1 = search_member_subscriptions(member_id='D-202505-001')

# 이름으로 검색
result2 = search_member_subscriptions(name='김')

# 휴대폰번호로 검색
result3 = search_member_subscriptions(phone='1023')
```
"""
)

# 9. 권장사항
print("\n9. 효과적인 이용권 관리를 위한 권장사항:")
print(
    """
   a) 이용권 관리 테이블 구조 개선:
      - 회원 기본 정보, 이용권 정보, 이용 내역을 별도 테이블로 분리
      - 회원-이용권 간 1:N 관계 설정으로 다양한 이용권 관리 가능
      
   b) 이용권 유효기간 모니터링:
      - 만료 예정인 이용권에 대한 알림 기능 구현
      - 회원별 이용권 갱신 시점 예측 및 관리
      
   c) 데이터 일관성 유지:
      - 신규 이용권 등록 시 표준화된 형식 사용
      - 이용권 상태 변경 이력 관리
      
   d) 고급 분석 기능:
      - 회원별 이용 패턴 분석
      - 인기 이용권 종류 추적
      - 매출 기여도 분석
"""
)

print("\n" + "=" * 70)
print("이용권 관리 시스템 설정 완료")
print("=" * 70)
