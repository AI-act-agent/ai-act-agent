import unittest
from unittest.mock import patch

from backend.app.agent.schemas import Evidence
from backend.app.assessment.assessor import run_preliminary_assessment
from backend.app.assessment.evidence import attach_assessment_evidence
from backend.app.assessment.schemas import (
    AssessmentInput,
    AssessmentWorkflowResult,
)


class AssessmentEvidenceTests(unittest.TestCase):

    @patch(
        "backend.app.assessment.evidence."
        "retrieve_assessment_evidence"
    )
    def test_attach_assessment_evidence(
        self,
        mock_retrieve,
    ):
        data = AssessmentInput(
            system_name="자동 채용 AI",
            system_description="지원자를 자동 탈락시킵니다.",
            usage_domain="채용 서류전형",
            ai_role="지원자 평가 및 자동 탈락",
            decision_consequence="채용 절차 종료",
            output_used_in_score=True,
            automatic_decision=True,
            human_review_process="사람의 검토 없음",
            human_final_decision=False,
            human_can_override=False,
            provided_to_third_party=False,
        )

        mock_retrieve.return_value = [
            Evidence(
                article_id="AI_BASIC_ACT_2",
                article="제2조제4호사목",
                text="채용 심사에 관한 고영향 인공지능 기준",
                source_url="ai_basic_law.txt",
                score=0.9,
            )
        ]

        assessment_result = run_preliminary_assessment(data)
        workflow_result = AssessmentWorkflowResult(
            assessment_input=data,
            assessment_result=assessment_result,
        )

        updated_result = attach_assessment_evidence(
            workflow_result
        )

        self.assertEqual(
            len(updated_result.assessment_result.citations),
            1,
        )
        self.assertEqual(
            updated_result.assessment_result
            .citations[0]
            .article_id,
            "AI_BASIC_ACT_2",
        )
        mock_retrieve.assert_called_once()

    def test_incomplete_input_rejects_evidence_search(self):
        data = AssessmentInput(
            system_name="채용 AI",
            system_description="채용 업무에 사용합니다.",
        )

        assessment_result = run_preliminary_assessment(data)
        workflow_result = AssessmentWorkflowResult(
            assessment_input=data,
            assessment_result=assessment_result,
        )

        with self.assertRaises(ValueError):
            attach_assessment_evidence(workflow_result)


if __name__ == "__main__":
    unittest.main()