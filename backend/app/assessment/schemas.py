"""사용자 입력 구조 만들기"""
"""판정 결과 구조 만들기"""

from dataclasses import dataclass, field
from backend.app.agent.schemas import Evidence


@dataclass
class AssessmentInput:

    system_name: str
    system_description: str

    usage_domain: str | None = None
    ai_role: str | None = None
    decision_consequence: str | None = None

    output_used_in_score: bool | None = None
    automatic_decision: bool | None = None
    human_review_process: str | None = None
    human_final_decision: bool | None = None
    human_can_override: bool | None = None
    provided_to_third_party: bool | None = None


@dataclass
class AssessmentResult:
    """고영향 AI 사전 검토 결과."""

    verdict: str
    summary: str

    domain_match: bool | None = None
    significant_impact: bool | None = None
    operator_status: str | None = None

    matched_criteria: list[str] = field(
        default_factory=list
    )
    missing_fields: list[str] = field(
        default_factory=list
    )
    citations: list[Evidence] = field(
        default_factory=list
    )
    recommendations: list[str] = field(
        default_factory=list
    )

@dataclass
class AssessmentWorkflowResult:
    """사전 검토 워크플로의 한 번의 실행 결과."""

    assessment_input: AssessmentInput
    assessment_result: AssessmentResult
    next_field: str | None = None
    next_question: str | None = None