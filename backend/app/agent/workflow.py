from backend.app.agent.mocks import mock_retrieve
from backend.app.agent.planner import create_plan
from backend.app.agent.schemas import AgentResult


def run_agent(question: str) -> AgentResult:

    if not question.strip():
        raise ValueError("질문을 입력해야 합니다.")

    plan = create_plan(question)

    search_query = plan.search_queries[0]
    evidence = mock_retrieve(search_query)

    return AgentResult(
        verdict="테스트 완료",
        answer="조사 계획 생성과 가짜 조문 검색을 완료했습니다.",
        confidence="미검증",
        citations=evidence,
        steps=[
            "질문 입력",
            "조사 계획 생성",
            "가짜 조문 검색",
            "테스트 결과 반환",
        ],
        retry_count=0,
    )