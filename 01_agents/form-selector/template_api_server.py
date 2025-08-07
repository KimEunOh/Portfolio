#!/usr/bin/env python3
"""
사직서 HTML 템플릿을 제공하는 간단한 HTTP API 서버
"""

from flask import Flask, render_template_string, request, jsonify
import os

app = Flask(__name__)

# 사직서 HTML 템플릿
RESIGNATION_LETTER_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>사직서</title>
    <style>
        body {
            font-family: 'Malgun Gothic', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 40px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }
        .header {
            text-align: center;
            border-bottom: 2px solid #333;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .title {
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        .date {
            font-size: 14px;
            color: #666;
        }
        .content {
            margin-bottom: 30px;
        }
        .section {
            margin-bottom: 20px;
        }
        .label {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        .value {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: #f9f9f9;
            margin-bottom: 15px;
        }
        .reason {
            min-height: 100px;
            white-space: pre-wrap;
        }
        .signature-section {
            margin-top: 40px;
            text-align: center;
        }
        .signature-box {
            display: inline-block;
            border-top: 1px solid #333;
            padding-top: 10px;
            margin-top: 50px;
            min-width: 200px;
        }
        .stamp-area {
            margin-top: 20px;
            text-align: center;
        }
        .stamp {
            display: inline-block;
            width: 60px;
            height: 60px;
            border: 2px solid #333;
            border-radius: 50%;
            line-height: 60px;
            text-align: center;
            font-weight: bold;
            color: #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">사직서</div>
            <div class="date">제출일: {submission_date}</div>
        </div>

        <div class="content">
            <div class="section">
                <div class="label">성명</div>
                <div class="value">{employee_name}</div>
            </div>

            <div class="section">
                <div class="label">부서</div>
                <div class="value">{department}</div>
            </div>

            <div class="section">
                <div class="label">직급</div>
                <div class="value">{position}</div>
            </div>

            <div class="section">
                <div class="label">사직 예정일</div>
                <div class="value">{resignation_date}</div>
            </div>

            <div class="section">
                <div class="label">사직 사유</div>
                <div class="value reason">{resignation_reason}</div>
            </div>

            <div class="section">
                <div class="label">연락처</div>
                <div class="value">{contact_info}</div>
            </div>
        </div>

        <div class="signature-section">
            <div class="signature-box">
                작성자: {employee_name} (인)
            </div>
        </div>

        <div class="stamp-area">
            <div class="stamp">인</div>
        </div>
    </div>
</body>
</html>"""


@app.route("/")
def index():
    """API 서버 상태 확인"""
    return jsonify(
        {
            "status": "running",
            "message": "사직서 템플릿 API 서버가 실행 중입니다.",
            "endpoints": {
                "/resignation_letter": "사직서 HTML 템플릿",
                "/health": "서버 상태 확인",
            },
        }
    )


@app.route("/resignation_letter")
def get_resignation_letter():
    """사직서 HTML 템플릿을 반환"""
    return (
        RESIGNATION_LETTER_TEMPLATE,
        200,
        {"Content-Type": "text/html; charset=utf-8"},
    )


@app.route("/health")
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    print("사직서 템플릿 API 서버를 시작합니다...")
    print("서버 주소: http://localhost:5000")
    print("사직서 템플릿: http://localhost:5000/resignation_letter")
    print("Ctrl+C로 서버를 종료할 수 있습니다.")

    app.run(host="0.0.0.0", port=5000, debug=True)
