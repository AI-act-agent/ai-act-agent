from backend.app.agent.schemas import Plan


def create_plan(question: str) -> Plan:

    if not question.strip():
        raise ValueError("질문을 입력해야 합니다.")

    return Plan(
        sub_questions=[
            question,
        ],
        search_queries=[
            question,
        ],
    )