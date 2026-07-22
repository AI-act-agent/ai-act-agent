"""부족한 입력을 찾는 기능"""

from backend.app.assessment.schemas import AssessmentInput


FOLLOWUP_QUESTIONS = {
    "system_description": (
        "AI 시스템이 어떤 방식으로 작동하는지 설명해 주세요."
    ),
    "usage_domain": (
        "이 AI 시스템은 어떤 분야에서 사용되나요? "
        "예: 채용, 의료, 대출, 교육, 공공서비스"
    ),
    "ai_role": (
        "AI가 수행하는 구체적인 역할은 무엇인가요?"
    ),
    "decision_consequence": (
        "AI의 결과가 사람에게 어떤 영향을 주나요?"
    ),
    "output_used_in_score": (
        "AI 결과가 점수, 등급 또는 평가에 반영되나요?"
    ),
    "automatic_decision": (
        "AI가 합격, 탈락, 승인 또는 거절을 "
        "자동으로 결정하나요?"
    ),
    "human_review_process": (
        "AI 결과를 사람이 어떤 절차로 검토하고 "
        "최종 결정하나요?"
    ),
        "human_final_decision": (
        "최종 합격, 탈락, 승인 또는 거절은 "
        "사람이 독립적으로 결정하나요?"
    ),
    "human_can_override": (
        "검토자는 AI의 결과를 변경하거나 "
        "거부할 수 있나요?"
    ),
    "provided_to_third_party": (
        "이 AI 시스템을 외부 기관이나 고객에게 제공하나요?"
    ),
}


def find_missing_fields(
    assessment_input: AssessmentInput,
) -> list[str]:
    """사전 검토에 필요한 정보 중 비어 있는 항목을 찾는다."""

    missing_fields = []

    for field_name in FOLLOWUP_QUESTIONS:
        value = getattr(
            assessment_input,
            field_name,
        )

        if value is None:
            missing_fields.append(field_name)
            continue

        if isinstance(value, str) and not value.strip():
            missing_fields.append(field_name)

    return missing_fields


def build_followup_questions(
    assessment_input: AssessmentInput,
) -> list[str]:
    """비어 있는 입력 항목에 맞는 추가 질문을 반환한다."""

    missing_fields = find_missing_fields(
        assessment_input
    )

    return [
        FOLLOWUP_QUESTIONS[field_name]
        for field_name in missing_fields
    ]