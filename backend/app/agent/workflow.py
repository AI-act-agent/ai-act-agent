from backend.app.agent.grounding import grounding_check
from backend.app.agent.mocks import mock_retrieve
from backend.app.agent.planner import create_plan
from backend.app.agent.schemas import AgentResult


MAX_RETRIES = 2


def run_agent(question: str) -> AgentResult:

    if not question.strip():
        raise ValueError("질문을 입력해야 합니다.")

    plan = create_plan(question)
    search_query = plan.search_queries[0]

    steps = [
        "질문 입력",
        "조사 계획 생성",
    ]

    last_evidence = []

    for attempt in range(MAX_RETRIES + 1):
        evidence = mock_retrieve(search_query)
        last_evidence = evidence

        steps.append(f"조문 검색 {attempt + 1}회")

        if evidence:
            draft_answer = "검색된 조문을 바탕으로 답변 초안을 생성했습니다."
        else:
            draft_answer = ""

        grounding_result = grounding_check(
            answer=draft_answer,
            evidence=evidence,
        )

        steps.append(f"근거 검증: {grounding_result}")

        if grounding_result == "entailment":
            steps.append("답변 확정")

            return AgentResult(
                verdict="답변 확정",
                answer=draft_answer,
                confidence="근거 충분",
                citations=evidence,
                steps=steps,
                retry_count=attempt,
            )

        if attempt < MAX_RETRIES:
            steps.append("근거 부족: 재검색")

    steps.append("판단 보류")

    return AgentResult(
        verdict="판단 보류",
        answer="검색된 법령 근거만으로는 판단하기 어렵습니다.",
        confidence="근거 부족",
        citations=last_evidence,
        steps=steps,
        retry_count=MAX_RETRIES,
    )