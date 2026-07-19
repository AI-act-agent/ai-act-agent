from backend.app.agent.grounding import grounding_check
from backend.app.agent.mocks import mock_retrieve
from backend.app.agent.planner import create_plan
from backend.app.agent.schemas import AgentResult


def run_agent(question: str) -> AgentResult:

    if not question.strip():
        raise ValueError("질문을 입력해야 합니다.")

    plan = create_plan(question)

    search_query = plan.search_queries[0]
    evidence = mock_retrieve(search_query)

    draft_answer = "검색된 조문을 바탕으로 답변 초안을 생성했습니다."

    grounding_result = grounding_check(
        answer=draft_answer,
        evidence=evidence,
    )

    if grounding_result == "entailment":
        verdict = "답변 확정"
        confidence = "근거 충분"
        answer = draft_answer
    else:
        verdict = "판단 보류"
        confidence = "근거 부족"
        answer = "검색된 법령 근거만으로는 판단하기 어렵습니다."

    return AgentResult(
        verdict=verdict,
        answer=answer,
        confidence=confidence,
        citations=evidence,
        steps=[
            "질문 입력",
            "조사 계획 생성",
            "가짜 조문 검색",
            f"근거 검증: {grounding_result}",
            verdict,
        ],
        retry_count=0,
    )