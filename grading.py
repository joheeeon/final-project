import re
from io import BytesIO

import pandas as pd
import pdfplumber


def extract_answer_key(pdf_bytes: bytes) -> pd.DataFrame:
    """정답 PDF에서 문항번호, 정답, 배점을 추출한다."""

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        text = "\n".join(
            page.extract_text() or ""
            for page in pdf.pages
        )

    if not text.strip():
        raise ValueError("PDF에서 텍스트를 읽지 못했어요.")

    if not re.search(r"정답\s*표", text):
        raise ValueError("정답표 PDF인지 확인해 주세요.")

    pattern = re.compile(
        r"(?<!\d)(\d{1,3})\s*([①②③④⑤])\s*(\d+(?:\.\d+)?)(?!\d)"
    )
    matches = pattern.findall(text)

    if not matches:
        raise ValueError("문항번호·정답·배점을 추출하지 못했어요.")

    choice_numbers = {
        symbol: number
        for number, symbol in enumerate("①②③④⑤", start=1)
    }
    questions = {}

    for number_text, symbol, points_text in matches:
        number = int(number_text)
        answer = choice_numbers[symbol]
        points = float(points_text)

        if number < 1 or points <= 0:
            raise ValueError("문항번호 또는 배점이 올바르지 않아요.")

        current = {
            "문항번호": number,
            "정답": answer,
            "배점": points,
        }

        if number in questions and questions[number] != current:
            raise ValueError(
                f"{number}번의 정답이나 배점이 서로 다르게 추출됐어요."
            )

        questions[number] = current

    result = pd.DataFrame(questions.values())
    result = result.sort_values("문항번호").reset_index(drop=True)

    expected = set(
        range(1, int(result["문항번호"].max()) + 1)
    )
    missing = expected - set(result["문항번호"])

    if missing:
        raise ValueError(
            f"정답 추출에서 누락된 문항이 있어요: {sorted(missing)}"
        )

    return result


def grade_omr(excel_bytes: bytes, answer_key: pd.DataFrame) -> dict:
    """OMR 엑셀을 채점하고 학생별 결과와 전체 통계를 반환한다."""

    with pd.ExcelFile(BytesIO(excel_bytes), engine="openpyxl") as workbook:
        if "OMR_응답" not in workbook.sheet_names:
            raise ValueError("엑셀에 'OMR_응답' 시트가 없어요.")

        data = pd.read_excel(workbook, sheet_name="OMR_응답")

    data = data.dropna(how="all").reset_index(drop=True)

    if data.empty:
        raise ValueError("엑셀에 학생 응답이 없어요.")

    if "학생명" not in data.columns:
        raise ValueError("엑셀에 '학생명' 열이 필요해요.")

    names = data["학생명"].fillna("").astype(str).str.strip()

    if names.eq("").any():
        raise ValueError("응답이 있는데 학생명이 비어 있는 행이 있어요.")

    if names.duplicated().any():
        raise ValueError("중복된 학생명이 있어요. 학생을 구분해 주세요.")

    question_columns = {}

    for column in data.columns:
        match = re.fullmatch(
            r"Q(\d+)",
            str(column).strip(),
            flags=re.IGNORECASE,
        )

        if match:
            number = int(match.group(1))

            if number in question_columns:
                raise ValueError(f"{number}번 응답 열이 중복돼요.")

            question_columns[number] = column

    key_numbers = set(answer_key["문항번호"])
    omr_numbers = set(question_columns)

    if key_numbers != omr_numbers:
        missing = sorted(key_numbers - omr_numbers)
        extra = sorted(omr_numbers - key_numbers)

        raise ValueError(
            f"정답지와 OMR 문항이 달라요. "
            f"OMR 누락: {missing}, 추가: {extra}"
        )

    numbers = sorted(key_numbers)

    raw = data[[question_columns[n] for n in numbers]].copy()
    raw = raw.replace(r"^\s*$", pd.NA, regex=True)
    responses = raw.apply(pd.to_numeric, errors="coerce")

    invalid = raw.notna() & ~responses.isin([1, 2, 3, 4, 5])

    if invalid.any().any():
        bad = invalid.stack()
        row, column = bad[bad].index[0]

        raise ValueError(
            f"{names.iloc[row]}의 {column} 응답은 "
            "1~5 또는 빈칸이어야 해요."
        )

    responses = responses.astype("Int64")
    responses.columns = numbers
    responses.index = names.to_list()
    responses.index.name = "학생명"

    key = answer_key.set_index("문항번호").reindex(numbers)

    correctness = (
        responses.eq(key["정답"], axis="columns")
        .fillna(False)
        .astype(bool)
    )

    scores = correctness.mul(
        key["배점"], axis="columns"
    ).sum(axis=1)

    student_results = pd.DataFrame({
        "학생명": names.to_numpy(),
        "점수": scores.to_numpy(),
        "정답수": correctness.sum(axis=1).to_numpy(),
        "오답수": (~correctness).sum(axis=1).to_numpy(),
    })

    question_results = answer_key.copy()

    question_results["오답수"] = question_results["문항번호"].map(
        (~correctness).sum(axis=0)
    )

    question_results["오답률(%)"] = (
        question_results["오답수"] / len(data) * 100
    )

    top_wrong = (
        question_results
        .sort_values(
            ["오답수", "문항번호"],
            ascending=[False, True],
        )
        .head(3)["문항번호"]
        .to_list()
    )

    return {
        "scores": student_results,
        "correctness": correctness,
        "responses": responses,
        "questions": question_results,
        "summary": {
            "students": len(data),
            "questions": len(numbers),
            "total_points": float(key["배점"].sum()),
            "mean": float(scores.mean()),
            "median": float(scores.median()),
            "std": float(scores.std(ddof=0)),
            "top_wrong": top_wrong,
            "blank_responses": int(
                responses.isna().sum().sum()
            ),
        },
    }