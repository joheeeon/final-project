from io import BytesIO
from typing import TypedDict

import pandas as pd
import pdfplumber
from langgraph.graph import END, START, StateGraph

from grading import extract_answer_key, grade_omr


class ExamState(TypedDict, total=False):
    question_pdf: bytes
    answer_pdf: bytes
    omr_excel: bytes
    answer_key: pd.DataFrame
    question_text: str
    report: dict


# 정답 PDF에서 문항번호·정답·배점 추출
def read_answer(state: ExamState) -> dict:
    return {
        "answer_key": extract_answer_key(
            state["answer_pdf"]
        )
    }


# 좌우 2단으로 구성된 문제 PDF 읽기
def read_questions(state: ExamState) -> dict:
    parts = []

    with pdfplumber.open(
        BytesIO(state["question_pdf"])
    ) as pdf:
        for page in pdf.pages:
            middle = page.width / 2

            for left, right in [
                (0, middle),
                (middle, page.width),
            ]:
                area = page.crop(
                    (left, 0, right, page.height)
                )
                parts.append(area.extract_text() or "")

    text = "\n\n".join(parts).strip()

    if not text:
        raise ValueError(
            "문제 PDF에서 텍스트를 읽지 못했어요."
        )

    return {"question_text": text}


# 추출한 정답표로 학생 응답 채점
def run_grading(state: ExamState) -> dict:
    report = grade_omr(
        state["omr_excel"],
        state["answer_key"],
    )
    report["question_text"] = state["question_text"]

    return {"report": report}


# LangGraph 채점 흐름 구성
def create_graph():
    builder = StateGraph(ExamState)

    builder.add_node("read_answer", read_answer)
    builder.add_node("read_questions", read_questions)
    builder.add_node("run_grading", run_grading)

    builder.add_edge(START, "read_answer")
    builder.add_edge("read_answer", "read_questions")
    builder.add_edge("read_questions", "run_grading")
    builder.add_edge("run_grading", END)

    return builder.compile()


GRADING_GRAPH = create_graph()


# app.py에서 호출하는 분석 함수
def analyze_exam(
    question_pdf: bytes,
    answer_pdf: bytes,
    omr_excel: bytes,
) -> dict:
    result = GRADING_GRAPH.invoke({
        "question_pdf": question_pdf,
        "answer_pdf": answer_pdf,
        "omr_excel": omr_excel,
    })

    return result["report"]


# 다운로드할 엑셀 파일 생성
def report_to_excel(report: dict) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import (
        Alignment,
        Border,
        Font,
        PatternFill,
        Side,
    )
    from openpyxl.utils import get_column_letter

    summary = report["summary"]
    scores = report["scores"]
    checks = report["correctness"]
    numbers = sorted(
        int(n)
        for n in report["questions"]["문항번호"]
    )

    book = Workbook()
    sheet = book.active
    sheet.title = "성적 분석 결과"
    sheet.sheet_view.showGridLines = False
    sheet.sheet_properties.tabColor = "8F7AA8"

    ink = "51485F"
    purple = "8F7AA8"
    pale = "EEE7F3"

    line = Side(style="thin", color="E5DFEA")
    border = Border(
        left=line,
        right=line,
        top=line,
        bottom=line,
    )

    # 개요 영역의 병합 셀 생성
    def block(
        address,
        value,
        fill="FFFFFF",
        bold=False,
        color=ink,
        size=11,
    ):
        sheet.merge_cells(address)

        for row in sheet[address]:
            for cell in row:
                cell.fill = PatternFill(
                    "solid",
                    fgColor=fill,
                )
                cell.border = border

        cell = sheet[address.split(":")[0]]
        cell.value = value

        if isinstance(value, str):
            cell.data_type = "s"

        cell.font = Font(
            name="맑은 고딕",
            size=size,
            bold=bold,
            color=color,
        )
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        )

        if isinstance(value, float):
            cell.number_format = "0.00"

    # 1. 전체 학생 성적 개요
    block(
        "A1:L2",
        "전체 학생 성적 개요",
        purple,
        True,
        "FFFFFF",
        17,
    )

    block(
        "A3:L3",
        f"시험명: {report.get('exam_name', '모의고사')}",
        "F8F4EE",
    )

    pairs = [
        (
            "A4:B4", "C4:D4",
            "응시 인원", int(summary["students"]),
        ),
        (
            "E4:F4", "G4:H4",
            "문항 수", int(summary["questions"]),
        ),
        (
            "I4:J4", "K4:L4",
            "만점", float(summary["total_points"]),
        ),
        (
            "A5:B5", "C5:D5",
            "평균", float(summary["mean"]),
        ),
        (
            "E5:F5", "G5:H5",
            "중앙값", float(summary["median"]),
        ),
        (
            "I5:J5", "K5:L5",
            "표준편차", float(summary["std"]),
        ),
    ]

    for label_range, value_range, label, value in pairs:
        block(label_range, label, pale, True)
        block(value_range, value)

    question_info = report["questions"].set_index(
        "문항번호"
    )

    top = " · ".join(
        f"{n}번 "
        f"({int(question_info.loc[n, '오답수'])}명, "
        f"{question_info.loc[n, '오답률(%)']:.1f}%)"
        for n in summary["top_wrong"]
    )

    block(
        "A6:B6",
        "오답 상위 3문항",
        pale,
        True,
    )
    block("C6:L6", top)

    block(
        "A7:L7",
        "O: 정답 / X: 오답 · 미응답은 X · "
        "표준편차는 전체 응시자 기준",
        "F8F4EE",
        size=9,
    )

    block(
        "A9:L9",
        "학생별 점수 및 각 문항별 정답 여부",
        pale,
        True,
        size=12,
    )

    # 2. 학생별 결과 표
    headers = [
        "순번",
        "학생명",
        "점수",
        "정답수",
        "오답수",
    ]
    headers += [f"{n}번" for n in numbers]

    for column, label in enumerate(headers, 1):
        cell = sheet.cell(10, column, label)
        cell.font = Font(
            name="맑은 고딕",
            size=10,
            bold=True,
            color="FFFFFF",
        )
        cell.fill = PatternFill(
            "solid",
            fgColor=purple,
        )
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )
        cell.border = border

    # 학생 한 명당 한 행씩 기록
    for order, student in enumerate(
        scores.to_dict("records"), 1
    ):
        name = student["학생명"]

        values = [
            order,
            name,
            float(student["점수"]),
            int(student["정답수"]),
            int(student["오답수"]),
        ]

        values += [
            "O" if bool(checks.at[name, n]) else "X"
            for n in numbers
        ]

        row_number = 10 + order

        for column, value in enumerate(values, 1):
            cell = sheet.cell(
                row_number,
                column,
                value,
            )

            # 학생명 등 문자열을 수식으로 실행하지 않도록 처리
            if isinstance(value, str):
                cell.data_type = "s"

            cell.font = Font(
                name="맑은 고딕",
                size=10,
                color=ink,
            )
            cell.fill = PatternFill(
                "solid",
                fgColor=(
                    "F8F4EE"
                    if order % 2
                    else "FFFFFF"
                ),
            )
            cell.border = border
            cell.alignment = Alignment(
                horizontal=(
                    "left"
                    if column == 2
                    else "center"
                ),
                vertical="center",
            )

            if column == 3:
                cell.number_format = "0.00"

            if column >= 6:
                correct = value == "O"

                cell.font = Font(
                    name="맑은 고딕",
                    size=10,
                    bold=True,
                    color=(
                        "417A69"
                        if correct
                        else "A75C68"
                    ),
                )
                cell.fill = PatternFill(
                    "solid",
                    fgColor=(
                        "EDF5F0"
                        if correct
                        else "F9EDEF"
                    ),
                )

        sheet.row_dimensions[row_number].height = 23

    # 3. 열 너비와 행 높이
    for column, width in [
        ("A", 7),
        ("B", 20),
        ("C", 11),
        ("D", 9),
        ("E", 9),
    ]:
        sheet.column_dimensions[column].width = width

    for column in range(6, len(headers) + 1):
        letter = get_column_letter(column)
        sheet.column_dimensions[letter].width = 6.5

    for row in range(1, 11):
        sheet.row_dimensions[row].height = 25

    sheet.row_dimensions[6].height = 34
    sheet.row_dimensions[7].height = 28
    sheet.row_dimensions[8].height = 10

    # 위쪽 제목과 학생 정보를 고정
    sheet.freeze_panes = "F11"

    last_column = get_column_letter(len(headers))
    last_row = 10 + len(scores)
    sheet.auto_filter.ref = (
        f"A10:{last_column}{last_row}"
    )

    buffer = BytesIO()
    book.save(buffer)

    return buffer.getvalue()