from flask import Flask, render_template
import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


# 데이터베이스 연결 설정
def connect_to_database():
    # 데이터베이스 연결 정보를 환경 변수에서 가져옴
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")
    hostname = os.getenv("DB_HOSTNAME")
    port = int(os.getenv("DB_PORT", "3306"))
    database = os.getenv("DB_NAME")

    if not all([username, password, hostname, database]):
        raise ValueError("Missing database configuration. Please check your .env file.")

    # SQLAlchemy 엔진 생성
    engine = create_engine(
        f"mysql+pymysql://{username}:{password}@{hostname}:{port}/{database}"
    )
    return engine


app = Flask(__name__)

# DB 연결
engine = connect_to_database()


@app.route("/")
def index():
    # SQL 쿼리를 실행하여 데이터 불러오기
    query = "SELECT * FROM HANA_TOTAL_RESERVATION"  # 예시 쿼리
    df = pd.read_sql(query, engine)

    """
    유형별 판매량
    """
    # 데이터 전처리: 'H'로 시작하는 것은 '호텔', 그 외는 '패키지', 결측값은 'etc'로 분류
    df["PRODUCT_TYPE"] = df["TYPE"].apply(
        lambda x: (
            "Hotel"
            if isinstance(x, str) and x.startswith("H")
            else ("Package" if isinstance(x, str) else "etc")
        )
    )

    # 제품 유형별 비율 계산
    product_type_counts = df["PRODUCT_TYPE"].value_counts().to_dict()

    """
    국가별 판매량
    """
    top_10_sold_products = df["COUNTRYCODE"].value_counts().nlargest(10)
    # 상위 9개 국가코드와 '기타'로 나머지 국가들 처리
    top_9_sold_products = top_10_sold_products.iloc[:9]  # 상위 9개
    other_sold_count = top_10_sold_products.iloc[9:].sum()  # 10번째 이후는 기타로 합산

    # '기타'를 추가한 데이터프레임 생성
    top_9_sold_products["Other"] = other_sold_count

    # Pie chart 데이터 준비
    labels = top_9_sold_products.index.tolist()
    values = top_9_sold_products.values.tolist()
    print(product_type_counts, labels[1], values[1])

    # 분석 결과를 템플릿에 전달
    return render_template(
        "index.html",
        product_type_counts=product_type_counts,
        labels=labels,
        values=values,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)
