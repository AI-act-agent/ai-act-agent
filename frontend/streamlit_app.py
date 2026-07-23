import re
import sys
from pathlib import Path
from dataclasses import asdict

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from backend.app.assessment.report import (
    build_assessment_report,
)
from backend.app.assessment.workflow import (
    BOOLEAN_FOLLOWUP_FIELDS,
    continue_assessment,
    finalize_assessment,
    start_assessment,
)


st.set_page_config(
    page_title="고영향 AI 사전 검토",
    page_icon="⚖️",
    layout="centered",
)

st.markdown(
    """
    <style>
    .block-container {
        max-width: 880px;
        padding-top: 2.5rem;
        padding-bottom: 4rem;
    }

    .main-title {
        font-size: 2.1rem;
        font-weight: 800;
        margin-bottom: 0.4rem;
    }

    .sub-title {
        color: #667085;
        margin-bottom: 2rem;
        line-height: 1.7;
    }

    .notice-box {
        padding: 1rem 1.2rem;
        border-radius: 0.8rem;
        background: #f2f4f7;
        color: #344054;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_boolean(
    value: bool | None,
) -> str:
    if value is True:
        return "예"

    if value is False:
        return "아니오"

    return "확인되지 않음"


def build_download_filename(
    system_name: str,
) -> str:
    safe_name = re.sub(
        r"[^\w가-힣-]+",
        "_",
        system_name,
    ).strip("_")

    if not safe_name:
        safe_name = "ai_system"

    return f"{safe_name}_고영향_AI_사전검토.md"


def reset_assessment() -> None:
    st.session_state.pop(
        "workflow_result",
        None,
    )
    st.session_state.pop(
        "assessment_error",
        None,
    )
    st.session_state.pop(
        "evidence_finalized",
        None,
    )


st.markdown(
    '<div class="main-title">'
    "AI 기본법 고영향 AI 사전 검토"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="sub-title">'
    "AI 시스템의 활용 방식과 의사결정 구조를 입력하면 "
    "고영향 AI 해당 가능성을 사전 검토하고 보고서를 "
    "생성합니다."
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="notice-box">
    현재 결과는 입력 정보에 기반한 사전 검토 자료입니다.
    정부의 공식 확인이나 법률 자문을 대신하지 않습니다.
    검토 결과에는 관련 법령과 가이드라인 검색 근거가
    함께 제공됩니다.
    </div>
    """,
    unsafe_allow_html=True,
)

if "workflow_result" not in st.session_state:
    st.session_state.workflow_result = None

if "assessment_error" not in st.session_state:
    st.session_state.assessment_error = None

if "evidence_finalized" not in st.session_state:
    st.session_state.evidence_finalized = False

workflow_result = st.session_state.workflow_result

if workflow_result is None:
    st.subheader("1. AI 시스템 정보 입력")

    with st.form("start_assessment_form"):
        system_name = st.text_input(
            "AI 시스템 이름",
            placeholder="예: 채용 보조 AI",
        )

        system_description = st.text_area(
            "AI 시스템 설명",
            placeholder=(
                "AI가 수행하는 역할, 점수 반영 여부, "
                "자동 결정 여부, 사람의 검토 절차 등을 "
                "가능한 구체적으로 작성해 주세요."
            ),
            height=180,
        )

        start_button = st.form_submit_button(
            "사전 검토 시작",
            type="primary",
            use_container_width=True,
        )

    if start_button:
        if not system_name.strip():
            st.warning(
                "AI 시스템 이름을 입력해 주세요."
            )
        elif not system_description.strip():
            st.warning(
                "AI 시스템 설명을 입력해 주세요."
            )
        else:
            with st.spinner(
                "입력 내용을 구조화하고 있습니다..."
            ):
                try:
                    st.session_state.workflow_result = (
                        start_assessment(
                            system_name=system_name,
                            system_description=(
                                system_description
                            ),
                        )
                    )
                    st.session_state.assessment_error = None
                    st.rerun()

                except Exception as error:
                    st.session_state.assessment_error = (
                        str(error)
                    )

    if st.session_state.assessment_error:
        st.error(
            "입력 정보를 처리하지 못했습니다: "
            f"{st.session_state.assessment_error}"
        )

else:
    if workflow_result.next_question:
        st.subheader("2. 추가 정보 확인")

        st.info(
            "정확한 사전 검토를 위해 한 가지씩 "
            "추가로 확인합니다."
        )

        with st.expander(
            "현재까지 구조화된 입력 보기"
        ):
            st.json(
                asdict(
                    workflow_result.assessment_input
                )
            )

        field_name = workflow_result.next_field

        with st.form(
            f"followup_form_{field_name}"
        ):
            st.markdown(
                f"**{workflow_result.next_question}**"
            )

            if field_name in BOOLEAN_FOLLOWUP_FIELDS:
                selected_answer = st.radio(
                    "답변 선택",
                    options=[
                        "선택해 주세요",
                        "예",
                        "아니오",
                    ],
                    horizontal=True,
                )

                answer = (
                    ""
                    if selected_answer
                    == "선택해 주세요"
                    else selected_answer
                )

            else:
                answer = st.text_area(
                    "답변",
                    height=120,
                )

            continue_button = (
                st.form_submit_button(
                    "다음",
                    type="primary",
                    use_container_width=True,
                )
            )

        if continue_button:
            try:
                st.session_state.workflow_result = (
                    continue_assessment(
                        previous_result=workflow_result,
                        answer=answer,
                    )
                )
                st.rerun()

            except ValueError as error:
                st.warning(str(error))

        if st.button("처음부터 다시 입력"):
            reset_assessment()
            st.rerun()

    else:
        if not st.session_state.evidence_finalized:
            with st.spinner(
                "법령·가이드라인 근거를 "
                "검색하고 있습니다..."
            ):
                try:
                    workflow_result = (
                        finalize_assessment(
                            workflow_result
                        )
                    )

                    st.session_state.workflow_result = (
                        workflow_result
                    )
                    st.session_state.evidence_finalized = (
                        True
                    )

                except Exception as error:
                    st.error(
                        "법령 근거를 연결하지 못했습니다: "
                        f"{error}"
                    )
                    st.stop()

        assessment_input = (
            workflow_result.assessment_input
        )
        assessment_result = (
            workflow_result.assessment_result
        )

        st.subheader("3. 사전 검토 결과")

        if (
            assessment_result.verdict
            == "해당 가능성 높음"
        ):
            st.error(
                f"검토 결과: "
                f"{assessment_result.verdict}"
            )

        elif (
            assessment_result.verdict
            == "해당 가능성 낮음"
        ):
            st.success(
                f"검토 결과: "
                f"{assessment_result.verdict}"
            )

        else:
            st.warning(
                f"검토 결과: "
                f"{assessment_result.verdict}"
            )

        st.write(assessment_result.summary)

        column1, column2, column3 = st.columns(3)

        column1.metric(
            "법정 영역 해당",
            format_boolean(
                assessment_result.domain_match
            ),
        )

        column2.metric(
            "중대한 영향 가능성",
            format_boolean(
                assessment_result.significant_impact
            ),
        )

        column3.metric(
            "사업자 지위",
            assessment_result.operator_status
            or "추가 검토",
        )

        st.markdown("#### 판단 항목")

        for criterion in (
            assessment_result.matched_criteria
        ):
            st.markdown(f"- {criterion}")

        st.markdown("#### 권고사항")

        for recommendation in (
            assessment_result.recommendations
        ):
            st.markdown(f"- {recommendation}")

        if assessment_result.citations:
            st.markdown("#### 참고 근거")

            for citation in (
                assessment_result.citations
            ):
                with st.expander(
                    f"{citation.article}"
                ):
                    st.write(citation.text)
                    st.caption(
                        f"출처: {citation.source_url}"
                    )
        else:
            st.warning(
                "현재 입력과 직접 관련된 법령·가이드라인 "
                "근거를 찾지 못했습니다."
            )

        report_text = build_assessment_report(
            workflow_result
        )

        with st.expander(
            "전체 보고서 미리보기"
        ):
            st.markdown(report_text)

        st.download_button(
            label="Markdown 보고서 다운로드",
            data=report_text,
            file_name=build_download_filename(
                assessment_input.system_name
            ),
            mime="text/markdown",
            use_container_width=True,
        )

        if st.button(
            "새로운 AI 시스템 검토",
            use_container_width=True,
        ):
            reset_assessment()
            st.rerun()