from backend.app.assessment.intake import find_missing_fields
from backend.app.assessment.rules import (
    assess_decision_involvement,
    assess_domain_match,
    assess_human_review,
    find_high_impact_domains,
)
from backend.app.assessment.schemas import (
    AssessmentInput,
    AssessmentResult,
)


RECRUITMENT_KEYWORDS = (
    "채용",
    "서류전형",
    "입사지원",
)


def _is_recruitment_domain(
    usage_domain: str,
) -> bool:
    return any(
        keyword in usage_domain
        for keyword in RECRUITMENT_KEYWORDS
    )


def _assess_operator_status(
    assessment_input: AssessmentInput,
) -> str:
    if assessment_input.provided_to_third_party is False:
        return "내부 이용자 가능성 있음"

    return "외부 제공 사업자 여부 추가 검토 필요"


def run_preliminary_assessment(
    assessment_input: AssessmentInput,
) -> AssessmentResult:
    """입력된 사실관계로 고영향 AI 해당 가능성을 사전 검토한다."""

    missing_fields = find_missing_fields(
        assessment_input
    )

    if missing_fields:
        return AssessmentResult(
            verdict="판단 보류",
            summary=(
                "고영향 AI 해당 가능성을 검토하기 위한 "
                "정보가 부족합니다."
            ),
            missing_fields=missing_fields,
            recommendations=[
                "부족한 정보를 추가로 입력해 주세요."
            ],
        )

    domain_match = assess_domain_match(
        assessment_input.usage_domain
    )

    matched_domains = find_high_impact_domains(
        assessment_input.usage_domain
    )

    operator_status = _assess_operator_status(
        assessment_input
    )

    if domain_match is False:
        return AssessmentResult(
            verdict="해당 가능성 낮음",
            summary=(
                "현재 입력된 활용 분야는 법에서 정한 "
                "고영향 AI 영역과 일치하지 않습니다."
            ),
            domain_match=False,
            operator_status=operator_status,
            recommendations=[
                "실제 활용 분야가 정확히 입력됐는지 확인해 주세요."
            ],
        )

    decision_involvement = assess_decision_involvement(
        assessment_input
    )
    human_review = assess_human_review(
        assessment_input
    )

    matched_criteria = [
        f"법정 활용 영역: {', '.join(matched_domains)}",
        f"AI의 의사결정 관여: {decision_involvement}",
        f"사람의 검토: {human_review}",
    ]

    if not _is_recruitment_domain(
        assessment_input.usage_domain
    ):
        return AssessmentResult(
            verdict="판단 보류",
            summary=(
                "법정 활용 영역에는 해당하지만, "
                "현재는 해당 분야의 세부 판단 규칙이 부족합니다."
            ),
            domain_match=True,
            operator_status=operator_status,
            matched_criteria=matched_criteria,
            recommendations=[
                "관련 판단 가이드라인과 유사 사례를 확인해 주세요."
            ],
        )

    if decision_involvement == "직접 결정":
        return AssessmentResult(
            verdict="해당 가능성 높음",
            summary=(
                "채용 영역에서 AI가 합격 또는 탈락을 "
                "직접 결정하므로 고영향 AI에 해당할 "
                "가능성이 높습니다."
            ),
            domain_match=True,
            significant_impact=True,
            operator_status=operator_status,
            matched_criteria=matched_criteria,
            recommendations=[
                "과학기술정보통신부의 공식 확인 절차를 "
                "검토해 주세요."
            ],
        )

    if (
        decision_involvement == "보조 자료"
        and human_review == "실질적 검토"
    ):
        return AssessmentResult(
            verdict="해당 가능성 낮음",
            summary=(
                "채용 영역에서 사용되지만 AI는 참고자료만 "
                "제공하고 사람이 독립적으로 최종 평가하므로 "
                "고영향 AI에 해당할 가능성이 낮습니다."
            ),
            domain_match=True,
            significant_impact=False,
            operator_status=operator_status,
            matched_criteria=matched_criteria,
            recommendations=[
                "AI 결과가 실제 평가 점수에 반영되지 않는지 "
                "운영 절차를 확인해 주세요."
            ],
        )

    return AssessmentResult(
        verdict="판단 보류",
        summary=(
            "채용 영역에는 해당하지만 AI 결과가 평가에 "
            "미치는 영향을 추가로 검토해야 합니다."
        ),
        domain_match=True,
        operator_status=operator_status,
        matched_criteria=matched_criteria,
        recommendations=[
            "AI 점수의 반영 비율과 사람의 독립적인 "
            "검토 절차를 확인해 주세요."
        ],
    )