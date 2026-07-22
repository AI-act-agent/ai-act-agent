import unittest
from unittest.mock import patch

from backend.app.assessment.assessor import (
    run_preliminary_assessment,
)
from backend.app.assessment.schemas import (
    AssessmentInput,
    AssessmentWorkflowResult,
)
from backend.app.assessment.workflow import (
    finalize_assessment,
)


class AssessmentFinalizeTests(unittest.TestCase):

    @patch(
        "backend.app.assessment.evidence."
        "attach_assessment_evidence"
    )
    def test_complete_assessment_can_be_finalized(
        self,
        mock_attach,
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

        assessment_result = run_preliminary_assessment(data)
        workflow_result = AssessmentWorkflowResult(
            assessment_input=data,
            assessment_result=assessment_result,
        )

        mock_attach.return_value = workflow_result

        finalized_result = finalize_assessment(
            workflow_result,
            top_k=3,
        )

        self.assertIs(
            finalized_result,
            workflow_result,
        )
        mock_attach.assert_called_once_with(
            workflow_result=workflow_result,
            top_k=3,
        )

    def test_incomplete_assessment_cannot_be_finalized(self):
        data = AssessmentInput(
            system_name="채용 AI",
            system_description="채용 업무에 사용합니다.",
        )

        assessment_result = run_preliminary_assessment(data)
        workflow_result = AssessmentWorkflowResult(
            assessment_input=data,
            assessment_result=assessment_result,
            next_field="usage_domain",
            next_question="어떤 분야에서 사용되나요?",
        )

        with self.assertRaises(ValueError):
            finalize_assessment(workflow_result)


if __name__ == "__main__":
    unittest.main()