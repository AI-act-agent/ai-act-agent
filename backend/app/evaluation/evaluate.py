import json
import time
import csv

from statistics import median

from backend.app.agent.grounding import NLI_MODEL_NAME
from backend.app.agent.llm_client import (
    MODEL_NAME as GENERATION_MODEL_NAME,
)
from backend.app.rag.pipeline import (
    LOCAL_EMBEDDING_MODEL,
)

from backend.app.agent.retriever import retrieve_evidence
from pathlib import Path

from backend.app.agent.versions.v3_planning_agent import run_v3
from backend.app.agent.versions.v4_grounded_agent import run_v4

AGENT_RUNNERS = {
    "V3": run_v3,
    "V4": run_v4,
}

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_TEST_CASES_PATH = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "test_cases.json"
)

DEFAULT_RESULTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "results"
    / "agent_results.jsonl"
)

DEFAULT_SUMMARY_PATH = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "results"
    / "agent_summary.csv"
)


def load_test_cases(
    path=DEFAULT_TEST_CASES_PATH,
) -> list[dict]:
    """평가용 정답 테스트셋을 불러온다."""

    test_path = Path(path)

    if not test_path.exists():
        raise FileNotFoundError(
            f"테스트셋 파일이 없습니다: {test_path}"
        )

    with test_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        test_cases = json.load(file)

    if not isinstance(test_cases, list):
        raise ValueError(
            "테스트셋의 최상위 구조는 배열이어야 합니다."
        )

    return test_cases

def evaluate_retrieval_case(
    test_case: dict,
    top_k: int = 5,
    expand_reference: bool = True,
) -> dict:
    """테스트 질문 하나의 검색 성능을 평가한다."""

    evidence = retrieve_evidence(
        question=test_case["question"],
        top_k=top_k,
        expand_reference=expand_reference,
    )

    retrieved_ids = [
        item.article_id
        for item in evidence
    ]

    gold_ids = set(
        test_case["gold_article_ids"]
    )

    matched_ids = gold_ids.intersection(
        retrieved_ids
    )

    hit_at_k = bool(matched_ids)

    recall_at_k = (
        len(matched_ids) / len(gold_ids)
        if gold_ids
        else None
    )

    reciprocal_rank = 0.0

    for rank, article_id in enumerate(
        retrieved_ids,
        start=1,
    ):
        if article_id in gold_ids:
            reciprocal_rank = 1 / rank
            break

    return {
        "id": test_case["id"],
        "question": test_case["question"],
        "top_k": top_k,
        "expand_reference": expand_reference,
        "retrieved_count": len(retrieved_ids),
        "gold_article_ids": sorted(gold_ids),
        "retrieved_article_ids": retrieved_ids,
        "hit_at_k": hit_at_k,
        "recall_at_k": recall_at_k,
        "reciprocal_rank": reciprocal_rank,
    }

def evaluate_retrieval(
    test_cases: list[dict],
    top_k: int = 5,
    expand_reference: bool = True,
) -> dict:
    """전체 테스트셋의 검색 성능을 평가한다."""

    results = [
        evaluate_retrieval_case(
            test_case=test_case,
            top_k=top_k,
            expand_reference=expand_reference,
        )
        for test_case in test_cases
    ]

    measurable_results = [
        result
        for result in results
        if result["recall_at_k"] is not None
    ]

    case_count = len(measurable_results)

    if case_count == 0:
        hit_rate = 0.0
        mean_recall = 0.0
        mean_reciprocal_rank = 0.0

    else:
        hit_rate = sum(
            result["hit_at_k"]
            for result in measurable_results
        ) / case_count

        mean_recall = sum(
            result["recall_at_k"]
            for result in measurable_results
        ) / case_count

        mean_reciprocal_rank = sum(
            result["reciprocal_rank"]
            for result in measurable_results
        ) / case_count

    return {
        "summary": {
            "evaluated_cases": case_count,
            "base_top_k": top_k,
            "expand_reference": expand_reference,
            "max_retrieved_count": max(
                (
                    result["retrieved_count"]
                    for result in results
                ),
                default=0,
            ),
            "hit_rate": hit_rate,
            "mean_recall": mean_recall,
            "mrr": mean_reciprocal_rank,
        },
        "results": results,
    }
"""정답 조문이 없는 판단 보류 질문은 검색 평균 계산에서 자동 제외"""

def evaluate_agent_case(
    test_case: dict,
    version: str,
) -> dict:
    """에이전트 버전 하나를 질문 하나로 평가한다."""

    if version not in AGENT_RUNNERS:
        raise ValueError(
            f"지원하지 않는 버전입니다: {version}"
        )

    runner = AGENT_RUNNERS[version]

    start_time = time.perf_counter()

    result = runner(
        test_case["question"]
    )

    latency_ms = round(
        (
            time.perf_counter()
            - start_time
        )
        * 1000,
        2,
    )

    evidence_ids = [
        item.article_id
        for item in result.citations
    ]

    gold_ids = set(
        test_case["gold_article_ids"]
    )

    matched_ids = gold_ids.intersection(
        evidence_ids
    )

    evidence_recall = (
        len(matched_ids) / len(gold_ids)
        if gold_ids
        else None
    )

    verdict_correct = (
        result.verdict
        == test_case["expected_verdict"]
    )

    hallucination = (
        not test_case["answerable"]
        and result.verdict == "답변 확정"
    )

    false_abstention = (
        test_case["answerable"]
        and result.verdict == "판단 보류"
    )

    return {
        "version": version,
        "generation_model": GENERATION_MODEL_NAME,
        "embedding_model": LOCAL_EMBEDDING_MODEL,
        "nli_model": (
            NLI_MODEL_NAME
            if version == "V4"
            else None
        ),
        "id": test_case["id"],
        "type": test_case["type"],
        "question": test_case["question"],
        "answerable": test_case["answerable"],
        "expected_verdict": test_case[
            "expected_verdict"
        ],
        "actual_verdict": result.verdict,
        "verdict_correct": verdict_correct,
        "hallucination": hallucination,
        "false_abstention": false_abstention,
        "evidence_recall": evidence_recall,
        "evidence_ids": evidence_ids,
        "retry_count": result.retry_count,
        "estimated_api_calls": (
            2 + result.retry_count
        ),
        "latency_ms": latency_ms,
        "answer": result.answer,
        "steps": result.steps,
    }

def save_agent_result(
    result: dict,
    path=DEFAULT_RESULTS_PATH,
) -> None:
    """에이전트 평가 결과를 JSONL 파일에 누적 저장한다."""

    result_path = Path(path)

    result_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with result_path.open(
        "a",
        encoding="utf-8",
    ) as file:
        json.dump(
            result,
            file,
            ensure_ascii=False,
        )
        file.write("\n")

def load_agent_results(
    path=DEFAULT_RESULTS_PATH,
) -> list[dict]:
    """저장된 JSONL 평가 결과를 불러온다."""

    result_path = Path(path)

    if not result_path.exists():
        return []

    results = []

    with result_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            cleaned_line = line.strip()

            if not cleaned_line:
                continue

            results.append(
                json.loads(cleaned_line)
            )

    return results

def summarize_agent_results(
    results: list[dict],
) -> list[dict]:
    """저장된 평가 결과를 버전별로 요약한다."""

    summaries = []

    versions = sorted({
        result["version"]
        for result in results
    })

    for version in versions:
        version_results = [
            result
            for result in results
            if result["version"] == version
        ]

        total_count = len(version_results)

        true_positive = sum(
            result["answerable"]
            and result["actual_verdict"]
            == "답변 확정"
            for result in version_results
        )

        false_positive = sum(
            not result["answerable"]
            and result["actual_verdict"]
            == "답변 확정"
            for result in version_results
        )

        false_negative = sum(
            result["answerable"]
            and result["actual_verdict"]
            == "판단 보류"
            for result in version_results
        )

        answerable_count = sum(
            result["answerable"]
            for result in version_results
        )

        unanswerable_count = (
            total_count - answerable_count
        )

        precision = (
            true_positive
            / (true_positive + false_positive)
            if true_positive + false_positive
            else 0.0
        )

        recall = (
            true_positive
            / (true_positive + false_negative)
            if true_positive + false_negative
            else 0.0
        )

        f1_score = (
            2 * precision * recall
            / (precision + recall)
            if precision + recall
            else 0.0
        )

        evidence_scores = [
            result["evidence_recall"]
            for result in version_results
            if result["evidence_recall"]
            is not None
        ]

        latencies = [
            result["latency_ms"]
            for result in version_results
        ]

        summaries.append({
            "version": version,
            "case_count": total_count,
            "verdict_accuracy": sum(
                result["verdict_correct"]
                for result in version_results
            ) / total_count,
            "answerability_precision": precision,
            "answerability_recall": recall,
            "answerability_f1": f1_score,
            "hallucination_rate": (
                false_positive
                / unanswerable_count
                if unanswerable_count
                else None
            ),
            "false_abstention_rate": (
                false_negative
                / answerable_count
                if answerable_count
                else None
            ),
            "mean_evidence_recall": (
                sum(evidence_scores)
                / len(evidence_scores)
                if evidence_scores
                else None
            ),
            "average_latency_ms": (
                sum(latencies)
                / len(latencies)
            ),
            "median_latency_ms": median(
                latencies
            ),
            "average_api_calls": sum(
                result["estimated_api_calls"]
                for result in version_results
            ) / total_count,
        })

    return summaries

def save_agent_summary(
    summaries: list[dict],
    path=DEFAULT_SUMMARY_PATH,
) -> None:
    """버전별 평가 요약을 CSV 파일로 저장한다."""

    if not summaries:
        raise ValueError(
            "저장할 평가 요약이 없습니다."
        )

    summary_path = Path(path)

    summary_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = list(
        summaries[0].keys()
    )

    with summary_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(summaries)