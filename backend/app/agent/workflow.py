from backend.app.agent.mocks import mock_retrieve
from backend.app.agent.schemas import AgentResult


def run_agent(question: str) -> AgentResult:

    if not question.strip():
        raise ValueError("질문을 입력해야 합니다.")

    evidence = mock_retrieve(question)

    return AgentResult(
        verdict="테스트 완료",
        answer="가짜 조문 검색 결과를 정상적으로 불러왔습니다.",
        confidence="미검증",
        citations=evidence,
        steps=[
            "질문 입력",
            "가짜 조문 검색",
            "테스트 결과 반환",
        ],
        retry_count=0,
    )