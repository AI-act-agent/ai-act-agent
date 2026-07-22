from backend.app.agent.retriever import retrieve_evidence
from backend.app.agent.schemas import Evidence
from backend.app.assessment.schemas import AssessmentInput


def build_assessment_query(
    assessment_input: AssessmentInput,
) -> str:
    """구조화된 사실관계로 고영향 AI 판단 근거 검색어를 만든다."""

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

    valid_parts.append(
        "고영향 인공지능 판단 기준"
    )

    return " ".join(valid_parts)


def retrieve_assessment_evidence(
    assessment_input: AssessmentInput,
    top_k: int = 5,
) -> list[Evidence]:
    """사전 검토에 필요한 법령과 가이드라인 근거를 검색한다."""

    query = build_assessment_query(
        assessment_input
    )

    return retrieve_evidence(
        question=query,
        top_k=top_k,
        expand_reference=True,
    )