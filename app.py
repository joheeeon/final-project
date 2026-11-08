import base64
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="모아 | 영어 학원 평가 도우미",
    page_icon="🌿",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "assets" / "gachon_logo.png"

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1150px;
        padding-top: 2rem;
    }

    h1, h2, h3 {
        color: #51485F;
    }

    .moa-hero {
        min-height: 370px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
    }

    .moa-hero img {
        width: 175px;
        height: auto;
        margin-bottom: 28px;
    }

    .moa-hero h1 {
        font-size: 38px;
        margin: 0;
    }

    .moa-hero p {
        color: #756C80;
        line-height: 1.9;
    }

    .moa-label {
        color: #88759F;
        font-size: 12px;
        letter-spacing: 2px;
    }

    .stButton > button {
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# 페이지 1: 서비스 소개
def landing_page():
    logo_html = ""

    if LOGO_PATH.exists():
        encoded = base64.b64encode(
            LOGO_PATH.read_bytes()
        ).decode("ascii")

        logo_html = (
            f'<img src="data:image/png;base64,{encoded}" '
            'alt="가천대학교 로고">'
        )
    else:
        st.info(
            "assets 폴더에 gachon_logo.png를 넣으면 중앙에 표시돼요."
        )

    st.markdown(
        f"""
        <section class="moa-hero">
            {logo_html}
            <span class="moa-label">
                MOA · FOR YOUR NEXT CLASS
            </span>
            <h1>모아 | 영어 학원 평가 도우미</h1>
            <p>
                성적을 모아, 가능성을 발견하다.<br>
                채점에 쓰던 시간은 줄이고,
                학생을 알아가는 시간은 늘려요.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1, 1, 1])

    with center:
        if st.button(
            "우리 반 분석 시작하기 →",
            type="primary",
            use_container_width=True,
        ):
            st.switch_page(analysis)

    st.divider()

    features = [
        (
            "📄 자동 채점",
            "문제지·정답 PDF와 OMR 결과를 올려 채점해요.",
        ),
        (
            "📊 성적 분석",
            "전체 통계와 문항별 오답을 살펴보고 엑셀로 정리해요.",
        ),
        (
            "💬 분석 챗봇",
            "성적에 대해 질문하고 유사한 연습 문제를 만들어요.",
        ),
    ]

    for column, (title, description) in zip(
        st.columns(3), features
    ):
        with column:
            with st.container(border=True):
                st.subheader(title)
                st.write(description)


# 페이지 2: 데이터 입력 및 분석
def analysis_page():
    with st.sidebar:
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

        uploaded = sum(
            file is not None
            for file in [question_file, omr_file, answer_file]
        )

        st.progress(uploaded / 3)
        st.caption(f"자료 준비 {uploaded} / 3")

        # 자동 채점 연결 전까지 비활성화
        st.button(
            "✨ 분석 시작하기",
            type="primary",
            disabled=True,
            use_container_width=True,
        )

        st.button(
            "📥 엑셀 추출하기",
            disabled=True,
            use_container_width=True,
        )

        st.caption(
            "현재는 화면 구성 단계예요. "
            "다음 단계에서 자동 채점을 연결해요."
        )

    st.title("우리 반을 알아가는 시간 🌿")
    st.caption(
        "자료를 모으고, 성적 속 작은 힌트를 발견해 보세요."
    )

    for column, label in zip(
        st.columns(3), ["평균", "중앙값", "표준편차"]
    ):
        with column:
            st.metric(label, "—")

    with st.container(border=True):
        st.subheader("💬 모아에게 물어보세요")

        with st.container(height=330, border=False):
            with st.chat_message("assistant", avatar="🌿"):
                st.write(
                    "안녕하세요, 선생님! "
                    "우리 반의 이야기를 함께 찾아볼까요?"
                )

                st.write(
                    "채점이 완료되면 이런 질문을 할 수 있어요."
                )

                st.markdown(
                    "- 이번 시험의 평균과 중앙값은 얼마야?\n"
                    "- 가장 많이 틀린 문항은 뭐야?\n"
                    "- 많이 틀린 문항과 비슷한 문제를 만들어 줘."
                )

        st.chat_input(
            "채점을 완료하면 질문할 수 있어요",
            disabled=True,
        )


# 두 페이지 등록
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

# 공통 페이지 이동 버튼
left, right = st.columns([1, 1])

with left:
    st.page_link(
        home,
        label="🌿 모아 · 서비스 소개",
    )

with right:
    st.page_link(
        analysis,
        label="데이터 입력 및 분석 →",
    )

navigation.run()