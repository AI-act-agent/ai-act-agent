import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from backend.app.assessment.assessor import (
    run_preliminary_assessment,
)
from backend.app.assessment.cli import run_cli
from backend.app.assessment.schemas import (
    AssessmentInput,
    AssessmentWorkflowResult,
)


def _build_complete_workflow_result():
    assessment_input = AssessmentInput(
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
        assessment_input
    )

    return AssessmentWorkflowResult(
        assessment_input=assessment_input,
        assessment_result=assessment_result,
    )


class AssessmentCliTests(unittest.TestCase):

    @patch(
        "backend.app.assessment.cli.start_assessment"
    )
    @patch(
        "builtins.input",
        side_effect=[
            "채용 보조 AI",
            "자기소개서 요약 서비스",
            "",
        ],
    )
    def test_cli_prints_completed_report(
        self,
        mock_input,
        mock_start,
    ):
        mock_start.return_value = (
            _build_complete_workflow_result()
        )

        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = run_cli()

        self.assertEqual(exit_code, 0)
        self.assertIn(
            "해당 가능성 낮음",
            output.getvalue(),
        )
        self.assertIn(
            "# 고영향 AI 사전 검토 보고서",
            output.getvalue(),
        )
        mock_start.assert_called_once()

    @patch(
        "backend.app.assessment.cli.start_assessment"
    )
    @patch(
        "builtins.input",
        side_effect=[
            "채용 AI",
            "채용 업무에 사용합니다.",
        ],
    )
    def test_cli_handles_extractor_error(
        self,
        mock_input,
        mock_start,
    ):
        mock_start.side_effect = RuntimeError(
            "테스트 API 오류"
        )

        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = run_cli()

        self.assertEqual(exit_code, 1)
        self.assertIn(
            "입력 정보를 구조화하지 못했습니다",
            output.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()