import streamlit as st

st.set_page_config(
    page_title="모아 | 영어 학원 평가 도우미",
    page_icon="🌿",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1100px;
        padding-top: 4rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #51485F;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 18px;
    }

    .moa-label {
        color: #88759F;
        font-size: 14px;
        letter-spacing: 2px;
        margin-bottom: 24px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="moa-label">MOA · FOR YOUR NEXT CLASS</div>',
    unsafe_allow_html=True,
)

st.title("🌿 모아")
st.header("성적을 모아, 가능성을 발견하다.")
st.write("채점에 쓰던 시간은 줄이고, 학생을 알아가는 시간은 늘려요.")
st.caption("선생님의 다정한 영어 학원 평가 도우미")

st.divider()

features = [
    ("📄 자동 채점", "문제지·정답 PDF와 OMR 결과를 모아 채점해요."),
    ("📊 성적 분석", "평균과 중앙값, 학생들이 어려워한 문항을 살펴봐요."),
    ("💬 분석 챗봇", "성적을 물어보고, 보충 학습에 필요한 문제를 만들어요."),
]

for column, (title, description) in zip(st.columns(3), features):
    with column:
        with st.container(border=True):
            st.subheader(title)
            st.write(description)

st.info(
    "🌱 첫 화면 준비 완료! 다음 단계에서 자료 업로드와 자동 채점을 연결해요."
)