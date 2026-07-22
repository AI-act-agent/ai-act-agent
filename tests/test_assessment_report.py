import unittest

from backend.app.assessment.assessor import run_preliminary_assessment
from backend.app.assessment.evidence import build_assessment_query
from backend.app.assessment.report import build_assessment_report
from backend.app.assessment.schemas import (
    AssessmentInput,
    AssessmentWorkflowResult,
)


class AssessmentReportTests(unittest.TestCase):

    def test_build_assessment_query(self):
        data = AssessmentInput(
            system_name="자동 채용 AI",
            system_description="AI가 지원자를 자동 탈락시킵니다.",
            usage_domain="채용 서류전형",
            ai_role="지원자 점수 산정 및 자동 탈락",
            decision_consequence="채용 절차 종료",
            output_used_in_score=True,
            automatic_decision=True,
            human_final_decision=False,
            human_can_override=False,
            provided_to_third_party=False,
        )

        query = build_assessment_query(data)

        self.assertIn("채용 서류전형", query)
        self.assertIn("AI 자동 결정", query)
        self.assertIn("AI 점수 평가 반영", query)
        self.assertIn("고영향 인공지능 판단 기준", query)

    def test_build_high_likelihood_report(self):
        data = AssessmentInput(
            system_name="자동 채용 AI",
            system_description=(
                "AI 점수가 기준 미만이면 지원자를 자동 탈락시킵니다."
            ),
            usage_domain="채용 서류전형",
            ai_role="지원자 점수 산정 및 자동 탈락",
            decision_consequence="지원자의 채용 절차 종료",
            output_used_in_score=True,
            automatic_decision=True,
            human_review_process="사람의 검토 없음",
            human_final_decision=False,
            human_can_override=False,
            provided_to_third_party=False,
        )

        result = run_preliminary_assessment(data)
        workflow_result = AssessmentWorkflowResult(
            assessment_input=data,
            assessment_result=result,
        )

        report = build_assessment_report(workflow_result)

        self.assertIn("# 고영향 AI 사전 검토 보고서", report)
        self.assertIn("해당 가능성 높음", report)
        self.assertIn("AI의 자동 결정: 예", report)
        self.assertIn("정부의 공식 확인", report)

    def test_report_rejects_incomplete_input(self):
        data = AssessmentInput(
            system_name="채용 AI",
            system_description="채용 업무에 AI를 사용합니다.",
        )

        result = run_preliminary_assessment(data)
        workflow_result = AssessmentWorkflowResult(
            assessment_input=data,
            assessment_result=result,
        )

        with self.assertRaises(ValueError):
            build_assessment_report(workflow_result)


if __name__ == "__main__":
    unittest.main()