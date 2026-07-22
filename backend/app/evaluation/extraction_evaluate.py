import json
import time
from dataclasses import asdict
from pathlib import Path
from statistics import mean

from backend.app.assessment.extractor import (
    extract_assessment_input,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_CASES_PATH = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "assessment_extraction_cases.json"
)

DEFAULT_RESULT_PATH = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "results"
    / "assessment_extraction_results.json"
)


def load_extraction_cases(
    path: str | Path = DEFAULT_CASES_PATH,
) -> list[dict]:
    with Path(path).open(
        "r",
        encoding="utf-8",
    ) as file:
        cases = json.load(file)

    if not isinstance(cases, list):
        raise ValueError(
            "Extractor 평가 데이터는 배열이어야 합니다."
        )

    return cases


def _build_check_counts(
    case: dict,
) -> dict:
    return {
        "boolean": len(
            case["expected_boolean_fields"]
        ),
        "text_keywords": len(
            case["expected_text_keywords"]
        ),
        "null": len(
            case["expected_null_fields"]
        ),
    }


def _evaluate_fields(
    case: dict,
    extracted_data,
) -> list[dict]:
    results = []

    for field_name, expected in (
        case["expected_boolean_fields"].items()
    ):
        actual = getattr(
            extracted_data,
            field_name,
        )

        results.append({
            "field": field_name,
            "check_type": "boolean",
            "expected": expected,
            "actual": actual,
            "correct": actual == expected,
        })

    for field_name, keywords in (
        case["expected_text_keywords"].items()
    ):
        actual = getattr(
            extracted_data,
            field_name,
        )

        normalized_actual = (
            actual.casefold()
            if isinstance(actual, str)
            else ""
        )

        correct = all(
            keyword.casefold() in normalized_actual
            for keyword in keywords
        )

        results.append({
            "field": field_name,
            "check_type": "text_keywords",
            "expected": keywords,
            "actual": actual,
            "correct": correct,
        })

    for field_name in case["expected_null_fields"]:
        actual = getattr(
            extracted_data,
            field_name,
        )

        results.append({
            "field": field_name,
            "check_type": "null",
            "expected": None,
            "actual": actual,
            "correct": actual is None,
        })

    return results


def evaluate_extraction_case(
    case: dict,
) -> dict:
    check_counts = _build_check_counts(case)
    total_checks = sum(check_counts.values())

    start_time = time.perf_counter()

    try:
        extracted_data = extract_assessment_input(
            system_name=case["system_name"],
            system_description=case["description"],
        )

        field_results = _evaluate_fields(
            case,
            extracted_data,
        )

        correct_counts = {
            check_type: sum(
                result["correct"]
                for result in field_results
                if result["check_type"] == check_type
            )
            for check_type in check_counts
        }

        correct_checks = sum(
            correct_counts.values()
        )

        error = None
        extracted_output = asdict(extracted_data)

    except Exception as exception:
        field_results = []
        correct_counts = {
            check_type: 0
            for check_type in check_counts
        }
        correct_checks = 0
        error = (
            f"{type(exception).__name__}: "
            f"{exception}"
        )
        extracted_output = None

    latency_ms = round(
        (time.perf_counter() - start_time) * 1000,
        2,
    )

    return {
        "id": case["id"],
        "total_checks": total_checks,
        "correct_checks": correct_checks,
        "case_correct": (
            correct_checks == total_checks
        ),
        "check_counts": check_counts,
        "correct_counts": correct_counts,
        "field_results": field_results,
        "extracted_output": extracted_output,
        "latency_ms": latency_ms,
        "estimated_api_calls": 1,
        "error": error,
    }


def _safe_accuracy(
    correct: int,
    total: int,
) -> float | None:
    if total == 0:
        return None

    return correct / total


def evaluate_extraction(
    cases: list[dict],
) -> dict:
    results = [
        evaluate_extraction_case(case)
        for case in cases
    ]

    total_checks = sum(
        result["total_checks"]
        for result in results
    )

    correct_checks = sum(
        result["correct_checks"]
        for result in results
    )

    type_totals = {
        check_type: sum(
            result["check_counts"][check_type]
            for result in results
        )
        for check_type in (
            "boolean",
            "text_keywords",
            "null",
        )
    }

    type_correct = {
        check_type: sum(
            result["correct_counts"][check_type]
            for result in results
        )
        for check_type in type_totals
    }

    return {
        "summary": {
            "case_count": len(results),
            "complete_case_accuracy": (
                sum(
                    result["case_correct"]
                    for result in results
                )
                / len(results)
            ),
            "field_accuracy": _safe_accuracy(
                correct_checks,
                total_checks,
            ),
            "boolean_accuracy": _safe_accuracy(
                type_correct["boolean"],
                type_totals["boolean"],
            ),
            "text_keyword_accuracy": _safe_accuracy(
                type_correct["text_keywords"],
                type_totals["text_keywords"],
            ),
            "null_accuracy": _safe_accuracy(
                type_correct["null"],
                type_totals["null"],
            ),
            "error_count": sum(
                result["error"] is not None
                for result in results
            ),
            "average_latency_ms": mean(
                result["latency_ms"]
                for result in results
            ),
            "estimated_api_calls": len(results),
        },
        "results": results,
    }


def save_extraction_evaluation(
    report: dict,
    output_path: str | Path = DEFAULT_RESULT_PATH,
) -> Path:
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