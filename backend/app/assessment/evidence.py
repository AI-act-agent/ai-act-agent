from dataclasses import replace

from backend.app.agent.retriever import retrieve_evidence
from backend.app.agent.schemas import Evidence
from backend.app.assessment.schemas import (
    AssessmentInput,
    AssessmentWorkflowResult,
)


def build_assessment_query(
    assessment_input: AssessmentInput,
) -> str:
    query_parts = [
        assessment_input.usage_domain,
        assessment_input.ai_role,
        assessment_input.decision_consequence,
    ]

    if assessment_input.automatic_decision is True:
        query_parts.append("AI 자동 결정")

    if assessment_input.output_used_in_score is True:
        query_parts.append("AI 점수 평가 반영")

    if assessment_input.human_final_decision is True:
        query_parts.append("사람의 최종 결정")

    if assessment_input.human_can_override is True:
        query_parts.append("AI 결과 변경 가능")

    valid_parts = [
        part.strip()
        for part in query_parts
        if isinstance(part, str) and part.strip()
    ]

    if not valid_parts:
        valid_parts.append(
            assessment_input.system_description.strip()
        )

    valid_parts.append("고영향 인공지능 판단 기준")

    return " ".join(valid_parts)


def retrieve_assessment_evidence(
    assessment_input: AssessmentInput,
    top_k: int = 5,
) -> list[Evidence]:
    query = build_assessment_query(assessment_input)

    return retrieve_evidence(
        question=query,
        top_k=top_k,
        expand_reference=True,
    )


def attach_assessment_evidence(
    workflow_result: AssessmentWorkflowResult,
    top_k: int = 5,
) -> AssessmentWorkflowResult:
    """완료된 사전 검토 결과에 검색 근거를 연결한다."""

    assessment_result = workflow_result.assessment_result

    if assessment_result.missing_fields:
        raise ValueError(
            "입력 정보가 부족하여 근거를 검색할 수 없습니다."
        )

    evidence = retrieve_assessment_evidence(
        assessment_input=workflow_result.assessment_input,
        top_k=top_k,
    )

    if not evidence:
        raise RuntimeError(
            "사전 검토에 사용할 근거를 검색하지 못했습니다."
        )

    updated_result = replace(
        assessment_result,
        citations=evidence,
    )

    return replace(
        workflow_result,
        assessment_result=updated_result,
    )