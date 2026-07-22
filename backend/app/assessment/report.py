from backend.app.assessment.schemas import (
    AssessmentWorkflowResult,
)


def _format_boolean(
    value: bool | None,
) -> str:
    if value is True:
        return "예"

    if value is False:
        return "아니오"

    return "확인되지 않음"


def build_assessment_report(
    workflow_result: AssessmentWorkflowResult,
) -> str:
    """완료된 사전 검토 결과를 Markdown 보고서로 만든다."""

    assessment_input = workflow_result.assessment_input
    assessment_result = workflow_result.assessment_result

    if assessment_result.missing_fields:
        raise ValueError(
            "입력 정보가 부족하여 보고서를 작성할 수 없습니다."
        )

    lines = [
        "# 고영향 AI 사전 검토 보고서",
        "",
        "## 1. AI 시스템 개요",
        "",
        f"- 시스템명: {assessment_input.system_name}",
        (
            "- 시스템 설명: "
            f"{assessment_input.system_description}"
        ),
        f"- 활용 분야: {assessment_input.usage_domain}",
        f"- AI 역할: {assessment_input.ai_role}",
        (
            "- 의사결정 결과: "
            f"{assessment_input.decision_consequence}"
        ),
        "",
        "## 2. 주요 운영 사실",
        "",
        (
            "- AI 결과의 점수·평가 반영: "
            f"{_format_boolean(assessment_input.output_used_in_score)}"
        ),
        (
            "- AI의 자동 결정: "
            f"{_format_boolean(assessment_input.automatic_decision)}"
        ),
        (
            "- 사람의 최종 결정: "
            f"{_format_boolean(assessment_input.human_final_decision)}"
        ),
        (
            "- AI 결과 변경 가능: "
            f"{_format_boolean(assessment_input.human_can_override)}"
        ),
        (
            "- 외부 기관·고객 제공: "
            f"{_format_boolean(assessment_input.provided_to_third_party)}"
        ),
        (
            "- 사람의 검토 절차: "
            f"{assessment_input.human_review_process}"
        ),
        "",
        "## 3. 사전 검토 결과",
        "",
        f"- 검토 결과: {assessment_result.verdict}",
        f"- 검토 요약: {assessment_result.summary}",
        (
            "- 법정 영역 해당: "
            f"{_format_boolean(assessment_result.domain_match)}"
        ),
        (
            "- 중대한 영향 가능성: "
            f"{_format_boolean(assessment_result.significant_impact)}"
        ),
        (
            "- 사업자 지위 검토: "
            f"{assessment_result.operator_status}"
        ),
        "",
        "## 4. 판단 항목",
        "",
    ]

    if assessment_result.matched_criteria:
        lines.extend(
            f"- {criterion}"
            for criterion in assessment_result.matched_criteria
        )
    else:
        lines.append("- 확인된 판단 항목이 없습니다.")

    lines.extend([
        "",
        "## 5. 참고 근거",
        "",
    ])

    if assessment_result.citations:
        for citation in assessment_result.citations:
            lines.extend([
                f"- {citation.article}",
                f"  - {citation.text}",
                f"  - 출처: {citation.source_url}",
            ])
    else:
        lines.append(
            "- RAG 법령·가이드라인 근거 연결 전입니다."
        )

    lines.extend([
        "",
        "## 6. 권고사항",
        "",
    ])

    if assessment_result.recommendations:
        lines.extend(
            f"- {recommendation}"
            for recommendation
            in assessment_result.recommendations
        )
    else:
        lines.append("- 추가 권고사항이 없습니다.")

    lines.extend([
        "",
        "## 7. 검토 한계",
        "",
        (
            "본 보고서는 입력된 정보와 제공된 법령·가이드라인을 "
            "기반으로 한 사전 검토 자료이며, 정부의 공식 확인이나 "
            "법률 자문을 대신하지 않습니다."
        ),
    ])

    return "\n".join(lines)