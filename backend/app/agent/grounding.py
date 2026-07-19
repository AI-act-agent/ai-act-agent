from backend.app.agent.schemas import Evidence


def grounding_check(
    answer: str,
    evidence: list[Evidence],
) -> str:

    if not answer.strip():
        return "neutral"

    if not evidence:
        return "neutral"

    return "entailment"