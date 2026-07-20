from backend.app.agent.answer_generator import generate_answer
from backend.app.agent.retriever import retrieve_evidence
from backend.app.agent.planner import create_plan
from backend.app.agent.schemas import AgentResult


MAX_RETRIES = 2


def run_v3(question: str) -> AgentResult:
    """계획 생성과 재검색을 적용한 V3 에이전트를 실행한다."""

    if not question.strip():
        raise ValueError("질문을 입력해야 합니다.")

    plan = create_plan(question)

    steps = [
        "질문 입력",
        "조사 계획 생성",
    ]

    last_evidence = []
    last_answer = None

    for attempt in range(MAX_RETRIES + 1):
        query_index = min(
            attempt,
            len(plan.search_queries) - 1,
        )
        search_query = plan.search_queries[query_index]

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

        if generated_answer["verdict"] == "답변 확정":
            steps.append("답변 확정")

            return AgentResult(
                verdict="답변 확정",
                answer=generated_answer["answer"],
                confidence=generated_answer["confidence"],
                citations=evidence,
                steps=steps,
                retry_count=attempt,
            )

        if attempt < MAX_RETRIES:
            steps.append("근거 부족: 재검색")

    steps.append("판단 보류")

    return AgentResult(
        verdict="판단 보류",
        answer=last_answer["answer"],
        confidence="근거 부족",
        citations=last_evidence,
        steps=steps,
        retry_count=MAX_RETRIES,
    )