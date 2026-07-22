import json
import time
from pathlib import Path
from statistics import mean

from backend.app.assessment.assessor import (
    run_preliminary_assessment,
)
from backend.app.assessment.schemas import AssessmentInput


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_CASES_PATH = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "assessment_test_cases.json"
)

VERDICT_LABELS = [
    "해당 가능성 높음",
    "해당 가능성 낮음",
    "판단 보류",
]


def load_assessment_cases(
    path: str | Path = DEFAULT_CASES_PATH,
) -> list[dict]:
    with Path(path).open(
        "r",
        encoding="utf-8",
    ) as file:
        cases = json.load(file)

    if not isinstance(cases, list):
        raise ValueError(
            "사전 판정 평가 데이터는 배열이어야 합니다."
        )

    return cases


def evaluate_assessment_case(
    case: dict,
) -> dict:
    assessment_input = AssessmentInput(
        **case["input"]
    )

    start_time = time.perf_counter()

    assessment_result = run_preliminary_assessment(
        assessment_input
    )

    latency_ms = round(
        (time.perf_counter() - start_time) * 1000,
        3,
    )

    expected_verdict = case["expected_verdict"]
    actual_verdict = assessment_result.verdict

    return {
        "id": case["id"],
        "case_type": case["case_type"],
        "expected_verdict": expected_verdict,
        "actual_verdict": actual_verdict,
        "correct": expected_verdict == actual_verdict,
        "latency_ms": latency_ms,
        "matched_criteria": (
            assessment_result.matched_criteria
        ),
        "missing_fields": (
            assessment_result.missing_fields
        ),
    }


def calculate_label_metrics(
    results: list[dict],
) -> dict:
    metrics = {}

    for label in VERDICT_LABELS:
        true_positive = sum(
            result["expected_verdict"] == label
            and result["actual_verdict"] == label
            for result in results
        )

        false_positive = sum(
            result["expected_verdict"] != label
            and result["actual_verdict"] == label
            for result in results
        )

        false_negative = sum(
            result["expected_verdict"] == label
            and result["actual_verdict"] != label
            for result in results
        )

        support = sum(
            result["expected_verdict"] == label
            for result in results
        )

        precision_denominator = (
            true_positive + false_positive
        )
        recall_denominator = (
            true_positive + false_negative
        )

        precision = (
            true_positive / precision_denominator
            if precision_denominator
            else 0.0
        )

        recall = (
            true_positive / recall_denominator
            if recall_denominator
            else 0.0
        )

        f1_denominator = precision + recall

        f1 = (
            2 * precision * recall / f1_denominator
            if f1_denominator
            else 0.0
        )

        metrics[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }

    return metrics


def build_confusion_matrix(
    results: list[dict],
) -> dict:
    matrix = {
        expected: {
            actual: 0
            for actual in VERDICT_LABELS
        }
        for expected in VERDICT_LABELS
    }

    for result in results:
        expected = result["expected_verdict"]
        actual = result["actual_verdict"]
        matrix[expected][actual] += 1

    return matrix


def evaluate_assessment(
    cases: list[dict],
) -> dict:
    results = [
        evaluate_assessment_case(case)
        for case in cases
    ]

    label_metrics = calculate_label_metrics(
        results
    )

    accuracy = mean(
        result["correct"]
        for result in results
    )

    macro_f1 = mean(
        metric["f1"]
        for metric in label_metrics.values()
    )

    average_latency_ms = mean(
        result["latency_ms"]
        for result in results
    )

    return {
        "summary": {
            "case_count": len(results),
            "verdict_accuracy": accuracy,
            "macro_f1": macro_f1,
            "average_latency_ms": (
                average_latency_ms
            ),
        },
        "label_metrics": label_metrics,
        "confusion_matrix": (
            build_confusion_matrix(results)
        ),
        "results": results,
    }

def save_assessment_evaluation(
    report: dict,
    output_path: str | Path | None = None,
) -> Path:
    """사전 판정 평가 결과를 JSON으로 저장한다."""

    if output_path is None:
        output_path = (
            PROJECT_ROOT
            / "data"
            / "evaluation"
            / "results"
            / "assessment_rule_baseline.json"
        )

    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return path.resolve()