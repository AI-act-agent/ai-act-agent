from dataclasses import replace

from backend.app.assessment.assessor import (
    run_preliminary_assessment,
)
from backend.app.assessment.extractor import (
    extract_assessment_input,
)
from backend.app.assessment.intake import (
    build_next_followup_question,
    find_next_missing_field,
)
from backend.app.assessment.schemas import (
    AssessmentInput,
    AssessmentWorkflowResult,
)


BOOLEAN_FOLLOWUP_FIELDS = {
    "output_used_in_score",
    "automatic_decision",
    "human_final_decision",
    "human_can_override",
    "provided_to_third_party",
}

TRUE_ANSWERS = {
    "예",
    "네",
    "yes",
    "true",
}

FALSE_ANSWERS = {
    "아니요",
    "아니오",
    "아니",
    "no",
    "false",
}


def _parse_boolean_answer(
    answer: str,
) -> bool:
    normalized_answer = answer.strip().lower()

    if normalized_answer in TRUE_ANSWERS:
        return True

    if normalized_answer in FALSE_ANSWERS:
        return False

    raise ValueError(
        "예 또는 아니오로 답변해 주세요."
    )


def _build_workflow_result(
    assessment_input: AssessmentInput,
) -> AssessmentWorkflowResult:
    assessment_result = run_preliminary_assessment(
        assessment_input
    )

    next_field = None
    next_question = None

    if assessment_result.missing_fields:
        next_field = find_next_missing_field(
            assessment_input
        )
        next_question = build_next_followup_question(
            assessment_input
        )

    return AssessmentWorkflowResult(
        assessment_input=assessment_input,
        assessment_result=assessment_result,
        next_field=next_field,
        next_question=next_question,
    )


def start_assessment(
    system_name: str,
    system_description: str,
) -> AssessmentWorkflowResult:
    """자연어 설명으로 고영향 AI 사전 검토를 시작한다."""

    assessment_input = extract_assessment_input(
        system_name=system_name,
        system_description=system_description,
    )

    return _build_workflow_result(
        assessment_input
    )


def continue_assessment(
    previous_result: AssessmentWorkflowResult,
    answer: str,
) -> AssessmentWorkflowResult:
    """추가 질문의 답변을 저장하고 사전 검토를 계속한다."""

    if previous_result.next_field is None:
        raise ValueError(
            "현재 답변이 필요한 추가 질문이 없습니다."
        )

    if not answer.strip():
        raise ValueError(
            "추가 질문에 대한 답변을 입력해야 합니다."
        )

    field_name = previous_result.next_field

    if field_name in BOOLEAN_FOLLOWUP_FIELDS:
        parsed_answer = _parse_boolean_answer(
            answer
        )
    else:
        parsed_answer = answer.strip()

    updated_input = replace(
        previous_result.assessment_input,
        **{
            field_name: parsed_answer,
        },
    )

    return _build_workflow_result(
        updated_input
    )

def finalize_assessment(
    workflow_result: AssessmentWorkflowResult,
    top_k: int = 3,
) -> AssessmentWorkflowResult:
    """입력이 완료된 사전 검토에 법령 근거를 연결한다."""

    if (
        workflow_result.next_field is not None
        or workflow_result.assessment_result.missing_fields
    ):
        raise ValueError(
            "추가 질문에 모두 답변한 뒤 사전 검토를 "
            "최종 확정해 주세요."
        )

    from backend.app.assessment.evidence import (
        attach_assessment_evidence,
    )

    return attach_assessment_evidence(
        workflow_result=workflow_result,
        top_k=top_k,
    )