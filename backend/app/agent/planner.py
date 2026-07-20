import json

from backend.app.agent.llm_client import call_gemini
from backend.app.agent.prompts import PLAN_SYSTEM_PROMPT, build_plan_prompt
from backend.app.agent.schemas import Plan


def create_plan(question: str) -> Plan:

    if not question.strip():
        raise ValueError("질문을 입력해야 합니다.")

    response = call_gemini(
        system_prompt=PLAN_SYSTEM_PROMPT,
        user_prompt=build_plan_prompt(question),
    )

    try:
        plan_data = json.loads(response)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Gemini 응답을 JSON으로 변환할 수 없습니다: {response}"
        ) from error

    sub_questions = plan_data.get("sub_questions")
    search_queries = plan_data.get("search_queries")

    if not isinstance(sub_questions, list) or not sub_questions:
        raise RuntimeError("하위 질문이 올바르게 생성되지 않았습니다.")

    if not isinstance(search_queries, list) or not search_queries:
        raise RuntimeError("검색어가 올바르게 생성되지 않았습니다.")

    return Plan(
        sub_questions=sub_questions,
        search_queries=search_queries,
    )