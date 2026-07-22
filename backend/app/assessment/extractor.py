import json

from backend.app.agent.llm_client import call_gemini
from backend.app.assessment.schemas import AssessmentInput


EXTRACTION_SYSTEM_PROMPT = """
당신은 AI 시스템의 운영 사실을 구조화하는 정보 추출기입니다.

규칙:
1. 사용자가 명시한 내용만 추출하세요.
2. 입력에 없는 정보는 추측하지 말고 null로 반환하세요.
3. 법적 판단이나 고영향 AI 해당 여부를 답하지 마세요.
4. 사용자가 사람의 검토가 없다고 명시한 경우, human_review_process를 null이 아닌 "검토 없음"으로 반환하세요.
5. boolean 필드는 true, false, null 중 하나만 사용하세요.
6. 반드시 JSON만 반환하고 마크다운 코드 블록을 사용하지 마세요.
7. ai_role에는 분석, 요약, 점수 산정, 추천 등 AI가 직접 수행하는 작업만 작성하세요.
8. decision_consequence에는 AI 결과가 평가 자료로 사용되는지, 점수에 반영되는지, 합격·탈락에 영향을 주는지 등 사람에게 미치는 결과를 작성하세요.
9. AI 결과를 사람이 검토한 뒤 최종 결정에 이용한다고 명시한 경우, 자동 결정이 아니더라도 decision_consequence에 그 사용 결과를 작성하세요.
10. human_review_process에는 사람이 원문이나 AI 결과를 어떻게 검토하는지만 작성하세요. 최종 결정 여부와 결과 변경 가능 여부는 각각의 boolean 필드에 분리하세요.
11. 사용자가 어떤 사실을 명시적으로 부정하면 false로 반환하고, 그 사실을 언급하지 않았다면 null로 반환하세요.

출력 형식:
{
  "usage_domain": "활용 분야 또는 null",
  "ai_role": "AI가 직접 수행하는 작업 또는 null",
  "decision_consequence": "AI 결과의 사용 방식과 사람에게 미치는 결과 또는 null",
  "output_used_in_score": true 또는 false 또는 null,
  "automatic_decision": true 또는 false 또는 null,
  "human_review_process": "사람이 수행하는 검토 절차 또는 null",
  "human_final_decision": true 또는 false 또는 null,
  "human_can_override": true 또는 false 또는 null,
  "provided_to_third_party": true 또는 false 또는 null
}
""".strip()


OUTPUT_FIELDS = {
    "usage_domain",
    "ai_role",
    "decision_consequence",
    "output_used_in_score",
    "automatic_decision",
    "human_review_process",
    "human_final_decision",
    "human_can_override",
    "provided_to_third_party",
}

BOOLEAN_FIELDS = {
    "output_used_in_score",
    "automatic_decision",
    "human_final_decision",
    "human_can_override",
    "provided_to_third_party",
}


def _parse_json_response(
    response: str,
) -> dict:
    start_index = response.find("{")
    end_index = response.rfind("}")

    if start_index == -1 or end_index == -1:
        raise RuntimeError(
            "Gemini 응답에서 JSON 객체를 찾을 수 없습니다."
        )

    json_text = response[
        start_index:end_index + 1
    ]

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "Gemini 응답을 JSON으로 변환할 수 없습니다: "
            f"{response}"
        ) from error

    if not isinstance(data, dict):
        raise RuntimeError(
            "Gemini 응답의 최상위 구조는 객체여야 합니다."
        )

    return data


def _validate_extracted_data(
    data: dict,
) -> None:
    missing_fields = OUTPUT_FIELDS - set(data)

    if missing_fields:
        raise RuntimeError(
            "Gemini 응답에 필수 항목이 없습니다: "
            f"{sorted(missing_fields)}"
        )

    for field_name in BOOLEAN_FIELDS:
        value = data[field_name]

        if value is not None and not isinstance(value, bool):
            raise RuntimeError(
                f"{field_name}은 boolean 또는 null이어야 합니다."
        )


def extract_assessment_input(
    system_name: str,
    system_description: str,
) -> AssessmentInput:
    """자연어 시스템 설명에서 사전 검토 입력값을 추출한다."""

    if not system_name.strip():
        raise ValueError("AI 시스템 이름을 입력해야 합니다.")

    if not system_description.strip():
        raise ValueError("AI 시스템 설명을 입력해야 합니다.")

    response = call_gemini(
        system_prompt=EXTRACTION_SYSTEM_PROMPT,
        user_prompt=(
            "다음 AI 시스템 설명에서 운영 사실을 추출하세요.\n\n"
            f"시스템 이름: {system_name}\n"
            f"시스템 설명: {system_description}"
        ),
    )

    extracted_data = _parse_json_response(
        response
    )
    _validate_extracted_data(
        extracted_data
    )

    human_review_process = extracted_data[
        "human_review_process"
    ]

    if (
        human_review_process is None
        and extracted_data["human_final_decision"] is False
    ):
        human_review_process = (
            "사람의 독립적인 최종 검토 없음"
        )

    return AssessmentInput(
        system_name=system_name.strip(),
        system_description=system_description.strip(),
        usage_domain=extracted_data["usage_domain"],
        ai_role=extracted_data["ai_role"],
        decision_consequence=extracted_data[
            "decision_consequence"
        ],
        output_used_in_score=extracted_data[
            "output_used_in_score"
        ],
        automatic_decision=extracted_data[
            "automatic_decision"
        ],
        human_review_process=human_review_process,
        human_final_decision=extracted_data[
            "human_final_decision"
        ],
        human_can_override=extracted_data[
            "human_can_override"
        ],
        provided_to_third_party=extracted_data[
            "provided_to_third_party"
        ],
    )