import tempfile
import unittest
from pathlib import Path

from backend.app.evaluation.assessment_evaluate import (
    evaluate_assessment,
    load_assessment_cases,
    save_assessment_evaluation,
)


class AssessmentEvaluationTests(unittest.TestCase):

    def test_load_and_evaluate_cases(self):
        cases = load_assessment_cases()
        report = evaluate_assessment(cases)

        self.assertEqual(len(cases), 6)
        self.assertEqual(
            report["summary"]["case_count"],
            6,
        )
        self.assertEqual(
            report["summary"]["verdict_accuracy"],
            1.0,
        )
        self.assertEqual(
            report["summary"]["macro_f1"],
            1.0,
        )

    def test_save_evaluation_result(self):
        cases = load_assessment_cases()
        report = evaluate_assessment(cases)

        with tempfile.TemporaryDirectory() as directory:
            output_path = (
                Path(directory)
                / "assessment_result.json"
            )

            saved_path = save_assessment_evaluation(
                report,
                output_path,
            )

            self.assertTrue(saved_path.exists())
            self.assertGreater(
                saved_path.stat().st_size,
                0,
            )


if __name__ == "__main__":
    unittest.main()