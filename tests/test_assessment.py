import unittest

from backend.app.assessment.assessor import (
    run_preliminary_assessment,
)
from backend.app.assessment.schemas import AssessmentInput
from backend.app.assessment.workflow import (
    _build_workflow_result,
    continue_assessment,
)


class AssessmentTest(unittest.TestCase):

    def test_recruitment_support_tool_is_low_likelihood(self):
        data = AssessmentInput(
            system_name="채용 보조 AI",
            system_description="자기소개서를 요약합니다.",
            usage_domain="채용 서류전형",
            ai_role="자기소개서 요약",
            decision_consequence="면접위원 참고자료",
            output_used_in_score=False,
            automatic_decision=False,
            human_review_process=(
                "면접위원이 원문을 확인하고 독립적으로 평가"
            ),
            human_final_decision=True,
            human_can_override=True,
            provided_to_third_party=False,
        )

        result = run_preliminary_assessment(data)

        self.assertEqual(
            result.verdict,
            "해당 가능성 낮음",
        )

    def test_automatic_rejection_is_high_likelihood(self):
        data = AssessmentInput(
            system_name="자동 채용 AI",
            system_description="점수 미달자를 자동 탈락시킵니다.",
            usage_domain="채용 서류전형",
            ai_role="지원자 평가 및 자동 탈락",
            decision_consequence="채용 절차 종료",
            output_used_in_score=True,
            automatic_decision=True,
            human_review_process="검토 없음",
            human_final_decision=False,
            human_can_override=False,
            provided_to_third_party=False,
        )

        result = run_preliminary_assessment(data)

        self.assertEqual(
            result.verdict,
            "해당 가능성 높음",
        )

    def test_missing_information_returns_abstention(self):
        data = AssessmentInput(
            system_name="채용 AI",
            system_description="AI를 채용에 사용합니다.",
        )

        result = run_preliminary_assessment(data)

        self.assertEqual(
            result.verdict,
            "판단 보류",
        )
        self.assertTrue(result.missing_fields)

    def test_followup_answer_updates_input(self):
        data = AssessmentInput(
            system_name="채용 AI",
            system_description="AI를 채용에 사용합니다.",
            usage_domain="채용",
        )

        first_result = _build_workflow_result(data)

        self.assertEqual(
            first_result.next_field,
            "ai_role",
        )

        second_result = continue_assessment(
            first_result,
            "자기소개서를 요약합니다.",
        )

        self.assertEqual(
            second_result.assessment_input.ai_role,
            "자기소개서를 요약합니다.",
        )
        self.assertEqual(
            second_result.next_field,
            "decision_consequence",
        )

    def test_boolean_followup_answer_is_parsed(self):
        data = AssessmentInput(
            system_name="채용 AI",
            system_description="지원자를 평가합니다.",
            usage_domain="채용",
            ai_role="지원자 평가",
            decision_consequence="합격 여부에 영향",
        )

        first_result = _build_workflow_result(data)

        self.assertEqual(
            first_result.next_field,
            "automatic_decision",
        )

        second_result = continue_assessment(
            first_result,
            "예",
        )

        self.assertTrue(
            second_result.assessment_input.automatic_decision
        )


if __name__ == "__main__":
    unittest.main()