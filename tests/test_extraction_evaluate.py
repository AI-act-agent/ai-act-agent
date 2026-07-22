import unittest
from unittest.mock import patch

from backend.app.assessment.schemas import AssessmentInput
from backend.app.evaluation.extraction_evaluate import (
    evaluate_extraction,
    evaluate_extraction_case,
    load_extraction_cases,
)


class ExtractionEvaluationTests(unittest.TestCase):

    @patch(
        "backend.app.evaluation.extraction_evaluate."
        "extract_assessment_input"
    )
    def test_correct_extraction_scores_one(
        self,
        mock_extract,
    ):
        case = load_extraction_cases()[0]

        mock_extract.return_value = AssessmentInput(
            system_name="자동 채용 AI",
            system_description=case["description"],
            usage_domain="채용 서류전형",
            ai_role="지원자 점수 산정 및 자동 탈락",
            decision_consequence="70점 미만 지원자 탈락",
            output_used_in_score=True,
            automatic_decision=True,
            human_review_process="사람의 검토 없음",
            human_final_decision=False,
            human_can_override=False,
            provided_to_third_party=False,
        )

        result = evaluate_extraction_case(case)

        self.assertTrue(result["case_correct"])
        self.assertEqual(
            result["correct_checks"],
            result["total_checks"],
        )
        self.assertIsNone(result["error"])

    @patch(
        "backend.app.evaluation.extraction_evaluate."
        "extract_assessment_input"
    )
    def test_api_error_is_recorded(
        self,
        mock_extract,
    ):
        case = load_extraction_cases()[0]

        mock_extract.side_effect = RuntimeError(
            "테스트 API 오류"
        )

        report = evaluate_extraction([case])

        self.assertEqual(
            report["summary"]["error_count"],
            1,
        )
        self.assertEqual(
            report["summary"]["field_accuracy"],
            0.0,
        )
        self.assertIn(
            "RuntimeError",
            report["results"][0]["error"],
        )


if __name__ == "__main__":
    unittest.main()