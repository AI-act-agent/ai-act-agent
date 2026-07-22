"""법에서 정한 고영향 AI 활용 영역인지 확인하는 기능"""
from backend.app.assessment.schemas import AssessmentInput


HIGH_IMPACT_DOMAIN_KEYWORDS = {
    "에너지 공급": (
        "에너지 공급",
        "전력 공급",
        "가스 공급",
    ),
    "먹는물 생산": (
        "먹는물",
        "상수도",
        "정수",
    ),
    "의료기기": (
        "의료기기",
        "디지털의료기기",
    ),
    "보건의료": (
        "보건의료",
        "진료",
        "진단",
        "치료",
    ),
    "원자력 안전": (
        "원자력",
        "핵물질",
        "방사능",
    ),
    "범죄 수사·체포": (
        "범죄 수사",
        "범죄수사",
        "체포",
    ),
    "채용·대출 심사": (
        "채용",
        "서류전형",
        "입사지원",
        "대출 심사",
        "대출심사",
        "신용 심사",
        "신용심사",
    ),
    "교통수단·시설·체계": (
        "교통수단",
        "교통시설",
        "교통체계",
    ),
    "공공서비스 의사결정": (
        "공공서비스",
        "자격 확인",
        "자격 결정",
        "비용 징수",
        "비용징수",
    ),
    "학생 평가": (
        "학생 평가",
        "학생평가",
        "성적 평가",
        "성적평가",
    ),
}


def find_high_impact_domains(
    usage_domain: str | None,
) -> list[str]:
    """입력된 활용 분야와 일치하는 법정 영역을 찾는다."""

    if usage_domain is None:
        return []

    normalized_domain = usage_domain.strip()

    if not normalized_domain:
        return []

    matched_domains = []

    for domain_name, keywords in (
        HIGH_IMPACT_DOMAIN_KEYWORDS.items()
    ):
        if any(
            keyword in normalized_domain
            for keyword in keywords
        ):
            matched_domains.append(domain_name)

    return matched_domains


def assess_domain_match(
    usage_domain: str | None,
) -> bool | None:
    """법정 활용 영역 해당 여부를 예비 확인한다."""

    if usage_domain is None:
        return None

    if not usage_domain.strip():
        return None

    matched_domains = find_high_impact_domains(
        usage_domain
    )

    return bool(matched_domains)


"""AI의 결정 관여 정도와 사람의 실질적 검토 여부"""
def assess_decision_involvement(
    assessment_input: AssessmentInput,
) -> str | None:
    """AI 결과가 최종 의사결정에 관여하는 정도를 확인한다."""

    if assessment_input.automatic_decision is True:
        return "직접 결정"

    if assessment_input.output_used_in_score is True:
        return "평가 반영"

    if (
        assessment_input.automatic_decision is False
        and assessment_input.output_used_in_score is False
    ):
        return "보조 자료"

    return None


def assess_human_review(
    assessment_input: AssessmentInput,
) -> str | None:
    """사람이 AI 결과를 실질적으로 검토하는지 확인한다."""

    review_process = (
        assessment_input.human_review_process
    )

    if review_process is None:
        return None

    if not review_process.strip():
        return None

    if (
        assessment_input.human_final_decision is None
        or assessment_input.human_can_override is None
    ):
        return None

    if (
        assessment_input.human_final_decision is True
        and assessment_input.human_can_override is True
    ):
        return "실질적 검토"

    return "제한적 또는 형식적 검토"