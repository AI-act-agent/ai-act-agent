from backend.app.agent.answer_generator import generate_answer
from backend.app.agent.grounding import grounding_check
from backend.app.agent.retriever import retrieve_evidence
from backend.app.agent.planner import create_plan
from backend.app.agent.schemas import AgentResult


MAX_RETRIES = 2
GROUNDING_PASS_LABEL = "entailment"

def run_v4(question: str) -> AgentResult:
    """계획, 재검색, Grounding 검사를 적용한 V4 에이전트를 실행한다."""

    if not question.strip():
        raise ValueError("질문을 입력해야 합니다.")

    plan = create_plan(question)
    search_queries = plan.search_queries or [question]

    steps = [
        "질문 입력",
        "조사 계획 생성",
    ]

    last_evidence = []
    last_answer = None

    for attempt in range(MAX_RETRIES + 1):
        query_index = min(
            attempt,
            len(search_queries) - 1,
        )
        search_query = search_queries[query_index]

        evidence = retrieve_evidence(search_query)
        last_evidence = evidence

        steps.append(
            f"조문 검색 {attempt + 1}회: {search_query}"
        )

        generated_answer = generate_answer(
            question=question,
            evidence=evidence,
        )
        last_answer = generated_answer

        steps.append(
            f"답변 생성: {generated_answer['verdict']}"
        )
        """최대 3회 검색하고, 검색할 때마다 Gemini 답변을 새로 생성"""

        if generated_answer["verdict"] != "답변 확정":
            if attempt < MAX_RETRIES:
                steps.append("근거 부족: 재검색")
            continue

        grounding_result = grounding_check(
            answer=generated_answer["answer"],
            evidence=evidence,
        )

        steps.append(
            f"Grounding 검사: {grounding_result}"
        )

        if grounding_result == GROUNDING_PASS_LABEL:
            steps.append("Grounding 통과: 답변 확정")

            return AgentResult(
                verdict="답변 확정",
                answer=generated_answer["answer"],
                confidence=generated_answer["confidence"],
                citations=evidence,
                steps=steps,
                retry_count=attempt,
            )

        if attempt < MAX_RETRIES:
            steps.append("Grounding 실패: 재검색")

    steps.append("최종 판단 보류")

    if (
        last_answer is not None
        and last_answer["verdict"] == "판단 보류"
    ):
        final_answer = last_answer["answer"]
    else:
        final_answer = (
            "생성된 답변이 법령 근거와 일치하는지 확인하지 못해 "
            "판단을 보류합니다."
        )

    return AgentResult(
        verdict="판단 보류",
        answer=final_answer,
        confidence="근거 부족",
        citations=last_evidence,
        steps=steps,
        retry_count=MAX_RETRIES,
    )