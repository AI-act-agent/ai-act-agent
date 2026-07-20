import json

from backend.app.agent.llm_client import call_gemini
from backend.app.agent.prompts import (
    ANSWER_SYSTEM_PROMPT,
    build_answer_prompt,
)
from backend.app.agent.schemas import Evidence


def format_evidence(evidence: list[Evidence]) -> str:

    formatted_items = []

    for index, item in enumerate(evidence, start=1):
        formatted_items.append(
            f"[근거 {index}]\n"
            f"조문: {item.article}\n"
            f"원문: {item.text}\n"
            f"출처: {item.source_url}"
        )

    return "\n\n".join(formatted_items)


def generate_answer(
    question: str,
    evidence: list[Evidence],
) -> dict[str, str]:
    """질문과 법령 근거를 사용해 Gemini 답변을 생성한다."""

    if not evidence:
        return {
            "verdict": "판단 보류",
            "answer": "검색된 법령 근거가 없어 판단하기 어렵습니다.",
            "confidence": "근거 부족",
        }

    evidence_text = format_evidence(evidence)

    response = call_gemini(
        system_prompt=ANSWER_SYSTEM_PROMPT,
        user_prompt=build_answer_prompt(
            question=question,
            evidence_text=evidence_text,
        ),
    )

    try:
        answer_data = json.loads(response)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Gemini 답변을 JSON으로 변환할 수 없습니다: {response}"
        ) from error

    required_fields = {
        "verdict",
        "answer",
        "confidence",
    }

    if not required_fields.issubset(answer_data):
        raise RuntimeError("Gemini 답변에 필수 항목이 없습니다.")

    return answer_data