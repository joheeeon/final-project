import base64
import hashlib
from pathlib import Path

import streamlit as st

from workflow import analyze_exam, report_to_excel
from chatbot import render_chat


st.set_page_config(
    page_title="모아 | 학원 평가 도우미",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "assets" / "gachon_logo.png"


st.markdown(
    """
    <style>
    .block-container {
        max-width: 1100px;
        padding-top: 4rem;
        padding-bottom: 1rem;
    }

    [data-testid="stSidebarContent"] {
        padding-top: 1.5rem;
    }

    h1, h2, h3 {
        color: #51485F;
        line-height: 1.5;
    }

    .stButton > button {
        border-radius: 12px;
    }

    .st-key-landing [data-testid="stVerticalBlock"] {
        gap: 0.75rem;
    }

    .home-hero {
        text-align: center;
        padding: 6px 16px 4px;
    }

    .school-logo {
        height: 100px;
        width: auto;
        max-width: 200px;
        object-fit: contain;
    }

    .logo-placeholder {
        height: 100px;
        display: grid;
        place-items: center;
        color: #88759F;
    }

    .home-brand {
        color: #88759F;
        font-size: 14px;
        font-weight: 600;
        margin: 12px 0 6px;
    }

    .home-hero h1 {
        font-size: 32px;
        line-height: 1.4;
        margin: 0;
        padding: 3px 0;
        word-break: keep-all;
    }

    .home-hero p {
        color: #756C80;
        font-size: 14px;
        line-height: 1.65;
        margin: 10px 0 4px;
        word-break: keep-all;
    }

    .feature-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 14px;
        max-width: 800px;
        margin: 10px auto 0;
    }

    .feature {
        border: 1px solid #E4DDE8;
        border-radius: 17px;
        padding: 16px;
        background: rgba(255, 255, 255, 0.55);
    }

    .feature h3 {
        font-size: 15px;
        margin: 0 0 7px;
        padding: 0;
        line-height: 1.4;
    }

    .feature p {
        color: #7B7283;
        font-size: 12px;
        line-height: 1.6;
        margin: 0;
        word-break: keep-all;
    }

    @media (max-height: 760px) and (min-width: 701px) {
        .block-container {
            padding-top: 3.6rem;
            padding-bottom: 0.5rem;
        }

        .school-logo, .logo-placeholder {
            height: 80px;
        }

        .home-brand {
            margin-top: 8px;
        }

        .home-hero h1 {
            font-size: 28px;
        }

        .home-hero p {
            font-size: 13px;
            margin-top: 8px;
        }

        .feature {
            padding: 12px 14px;
        }
    }

    @media (max-height: 640px) and (min-width: 701px) {
        .school-logo, .logo-placeholder {
            height: 64px;
        }

        .home-hero h1 {
            font-size: 25px;
        }

        .feature-grid {
            margin-top: 0;
        }
    }

    @media (max-width: 700px) {
        .home-hero h1 {
            font-size: 26px;
        }

        .feature-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <style>
    .school-logo {
        height: 140px;
        max-width: 260px;
    }

    .logo-placeholder {
        height: 140px;
    }

    .home-brand {
        font-size: 16px;
    }

    .home-hero h1 {
        font-size: 34px;
    }

    .home-hero p {
        font-size: 15px;
    }

    .feature h3 {
        font-size: 16px;
    }

    .feature p {
        font-size: 13px;
    }

    @media (max-height: 760px) and (min-width: 701px) {
        .school-logo, .logo-placeholder {
            height: 120px;
        }

        .home-brand {
            font-size: 15px;
        }

        .home-hero h1 {
            font-size: 30px;
        }

        .home-hero p {
            font-size: 14px;
        }
    }

    @media (max-height: 640px) and (min-width: 701px) {
        .school-logo, .logo-placeholder {
            height: 100px;
        }

        .home-hero h1 {
            font-size: 28px;
        }
    }

    @media (max-width: 700px) {
        .school-logo, .logo-placeholder {
            height: 120px;
        }

        .home-hero h1 {
            font-size: 28px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 두 페이지에서 사용하는 페이지 이동 버튼
def page_button():
    with st.popover(
        "페이지 이동",
        icon=":material/swap_horiz:",
    ):
        st.page_link(
            home,
            label="1페이지 · 서비스 소개",
            icon=":material/home:",
        )
        st.page_link(
            analysis,
            label="2페이지 · 데이터 입력 및 분석",
            icon=":material/analytics:",
        )


# 페이지 1: 랜딩 페이지
def landing_page():
    page_button()

    logo_html = (
        '<div class="logo-placeholder">'
        '가천대 로고 파일을 확인해 주세요'
        '</div>'
    )

    if LOGO_PATH.exists():
        encoded = base64.b64encode(
            LOGO_PATH.read_bytes()
        ).decode("ascii")

        logo_html = (
            f'<img class="school-logo" '
            f'src="data:image/png;base64,{encoded}" '
            'alt="가천대학교 로고">'
        )

    with st.container(key="landing"):
        st.markdown(
            f"""
            <section class="home-hero">
                {logo_html}
                <div class="home-brand">
                    모아 · 학원 평가 도우미
                </div>
                <h1>성적을 모아, 가능성을 발견하다.</h1>
                <p>
                    채점에 쓰던 시간은 줄이고,
                    학생을 알아가는 시간은 늘려요.<br>
                    자료 업로드부터 성적 분석과 연습 문제까지,
                    모아와 함께.
                </p>
            </section>
            """,
            unsafe_allow_html=True,
        )

        _, center, _ = st.columns([2, 1.5, 2])

        with center:
            if st.button(
                "우리 반 분석 시작하기 →",
                type="primary",
                width="stretch",
            ):
                st.switch_page(analysis)

        st.markdown(
            """
            <div class="feature-grid">
                <div class="feature">
                    <h3>📄 정확하게 채점해요</h3>
                    <p>
                        문제지·OMR·정답지를 모아<br>
                        정답과 배점에 맞게 채점해요.
                    </p>
                </div>
                <div class="feature">
                    <h3>📊 한눈에 살펴봐요</h3>
                    <p>
                        성적과 오답 속 힌트를 찾고<br>
                        엑셀 리포트로 정리해요.
                    </p>
                </div>
                <div class="feature">
                    <h3>💬 편하게 물어봐요</h3>
                    <p>
                        궁금한 성적을 물어보고<br>
                        비슷한 연습 문제를 만들어요.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# 페이지 2: 데이터 입력 및 분석
def analysis_page():
    with st.sidebar:
        # 왼쪽 사이드바 맨 위의 페이지 버튼
        page_button()

        st.subheader("📂 시험 자료 모으기")
        st.caption("같은 시험의 자료 세 가지를 올려주세요.")

        question_file = st.file_uploader(
            "① 문제지 PDF",
            type=["pdf"],
            key="question_pdf",
        )
        omr_file = st.file_uploader(
            "② OMR 인식 결과",
            type=["xlsx"],
            key="omr_excel",
        )
        answer_file = st.file_uploader(
            "③ 정답·배점 PDF",
            type=["pdf"],
            key="answer_pdf",
        )

        files = [question_file, omr_file, answer_file]
        uploaded = sum(
            file is not None for file in files
        )

        st.progress(uploaded / 3)
        st.caption(f"자료 준비 {uploaded} / 3")

        fingerprint = tuple(
            hashlib.sha256(file.getvalue()).hexdigest()
            if file is not None else None
            for file in files
        )

        previous = st.session_state.get(
            "upload_fingerprint"
        )

        if any(fingerprint) and fingerprint != previous:
            st.session_state.pop("report", None)
            st.session_state.pop("excel_bytes", None)
            st.session_state["messages"] = []

        st.session_state["upload_fingerprint"] = fingerprint

        if st.button(
            "✨ 분석 시작하기",
            type="primary",
            disabled=uploaded != 3,
            width="stretch",
        ):
            st.session_state.pop("report", None)
            st.session_state.pop("excel_bytes", None)
            st.session_state["messages"] = []

            try:
                with st.spinner(
                    "PDF를 읽고 학생 응답을 채점하고 있어요…"
                ):
                    report = analyze_exam(
                        question_pdf=question_file.getvalue(),
                        answer_pdf=answer_file.getvalue(),
                        omr_excel=omr_file.getvalue(),
                    )

                    report["exam_name"] = Path(
                        question_file.name
                    ).stem

                    excel_bytes = report_to_excel(report)

                    st.session_state["report"] = report
                    st.session_state["excel_bytes"] = (
                        excel_bytes
                    )

                st.success("채점과 엑셀 준비를 완료했어요!")

            except Exception as error:
                st.error(
                    f"분석을 완료하지 못했어요: {error}"
                )

        excel_bytes = st.session_state.get(
            "excel_bytes"
        )

        st.download_button(
            "📥 엑셀 추출하기",
            data=excel_bytes or b"",
            file_name="모아_성적분석.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument"
                ".spreadsheetml.sheet"
            ),
            disabled=excel_bytes is None,
            width="stretch",
        )

        st.caption(
            "정답 PDF에서 추출한 정답·배점으로 채점해요."
        )

    st.title("우리 반을 알아가는 시간 🌿")
    st.caption(
        "자료를 모으고, 성적 속 작은 힌트를 발견해 보세요."
    )

    report = st.session_state.get("report")
    summary = (
        report["summary"]
        if report is not None
        else None
    )

    for column, label, field in zip(
        st.columns(3),
        ["평균", "중앙값", "표준편차"],
        ["mean", "median", "std"],
    ):
        with column:
            value = (
                f"{summary[field]:.2f}점"
                if summary else "—"
            )
            st.metric(label, value)

    if report is not None:
        st.caption(
            f"{report['exam_name']} · "
            f"응시 {summary['students']}명 · "
            f"{summary['questions']}문항 · "
            f"{summary['total_points']:g}점 만점"
        )

        top_questions = ", ".join(
            f"{n}번" for n in summary["top_wrong"]
        )
        st.info(f"오답 상위 3문항: {top_questions}")

        if summary["blank_responses"]:
            st.warning(
                f"미응답 {summary['blank_responses']}건을 "
                "오답으로 처리했어요."
            )

        with st.expander(
            "📊 학생별 결과와 문항별 분석 보기"
        ):
            students_tab, questions_tab, answers_tab = (
                st.tabs([
                    "학생별 성적",
                    "문항별 분석",
                    "문항별 정답 여부",
                ])
            )

            with students_tab:
                st.dataframe(
                    report["scores"],
                    hide_index=True,
                    width="stretch",
                )

            with questions_tab:
                st.dataframe(
                    report["questions"].sort_values(
                        ["오답수", "문항번호"],
                        ascending=[False, True],
                    ),
                    hide_index=True,
                    width="stretch",
                )

            with answers_tab:
                ox = report["correctness"].replace({
                    True: "O",
                    False: "X",
                })
                st.dataframe(
                    ox,
                    width="stretch",
                )

        st.caption(
            "표준편차는 전체 응시자 기준이며, "
            "오답 수 동률이면 문항 번호순으로 표시해요."
        )

    # 채팅 연결: analysis_page() 안의 마지막 부분
    render_chat(report)


# 페이지 등록 및 실행
home = st.Page(
    landing_page,
    title="서비스 소개",
    default=True,
)

analysis = st.Page(
    analysis_page,
    title="데이터 입력 및 분석",
    url_path="analysis",
)

navigation = st.navigation(
    [home, analysis],
    position="hidden",
)

navigation.run()