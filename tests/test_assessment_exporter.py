import tempfile
import unittest
from pathlib import Path

from backend.app.assessment.assessor import (
    run_preliminary_assessment,
)
from backend.app.assessment.exporter import (
    save_assessment_report,
)
from backend.app.assessment.schemas import (
    AssessmentInput,
    AssessmentWorkflowResult,
)


class AssessmentExporterTests(unittest.TestCase):

    def setUp(self):
        self.data = AssessmentInput(
            system_name="채용 보조 AI",
            system_description=(
                "AI가 자기소개서를 요약하고 사람이 평가합니다."
            ),
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

        assessment_result = run_preliminary_assessment(
            self.data
        )

        self.workflow_result = AssessmentWorkflowResult(
            assessment_input=self.data,
            assessment_result=assessment_result,
        )

    def test_save_markdown_report(self):
        with tempfile.TemporaryDirectory() as directory:
            output_path = (
                Path(directory)
                / "assessment_report.md"
            )

            saved_path = save_assessment_report(
                self.workflow_result,
                output_path,
            )

            self.assertTrue(saved_path.exists())

            report_text = saved_path.read_text(
                encoding="utf-8"
            )

            self.assertIn(
                "# 고영향 AI 사전 검토 보고서",
                report_text,
            )
            self.assertIn(
                "해당 가능성 낮음",
                report_text,
            )

    def test_existing_report_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output_path = (
                Path(directory)
                / "assessment_report.md"
            )

            save_assessment_report(
                self.workflow_result,
                output_path,
            )

            with self.assertRaises(FileExistsError):
                save_assessment_report(
                    self.workflow_result,
                    output_path,
                )


if __name__ == "__main__":
    unittest.main()