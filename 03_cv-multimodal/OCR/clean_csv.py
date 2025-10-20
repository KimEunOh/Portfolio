import sys
import re
import csv
from pathlib import Path


def remove_thousand_separators(text: str) -> str:
    # 숫자 사이의 쉼표만 제거 (예: 12,345 -> 12345)
    return re.sub(r"(?<=\d),(?=\d)", "", text)


def clean_line_triple_quoted(line: str):
    # 각 필드가 """...""" 형태일 때 내용을 추출
    fields = re.findall(r'"""(.*?)"""', line)
    if not fields:
        return None
    cleaned = []
    for f in fields:
        # 내부 중첩된 쌍따옴표 제거 후 숫자 쉼표 제거
        f2 = f.replace('"', "")
        f2 = remove_thousand_separators(f2)
        cleaned.append(f2.strip())
    return cleaned


def clean_csv(path_str: str, out_path_str: str | None = None) -> Path:
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # 항상 새로운 파일로 저장해 편집기 잠금 충돌 회피
    out_path = (
        Path(out_path_str) if out_path_str else path.with_name(path.stem + "_clean.csv")
    )

    out_rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")
            if not line.strip():
                continue
            parsed = clean_line_triple_quoted(line)
            if parsed is not None:
                out_rows.append(parsed)
                continue
            # fallback: 일반 CSV 파싱 시도
            for row in csv.reader([line]):
                cleaned = [remove_thousand_separators(col) for col in row]
                out_rows.append(cleaned)

    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(out_rows)

    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clean_csv.py <path-to-csv> [output-path]")
        sys.exit(1)
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    out = clean_csv(input_path, output_path)
    print(f"Wrote cleaned CSV to: {out}")
