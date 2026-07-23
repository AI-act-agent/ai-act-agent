"""에이전트 실행 흐름.

실제 RAG 검색(retrieve_evidence)과 답변 생성(generate_answer)에 연결되어 있으며,
Gemini 키가 없거나 호출이 실패해도 검색 근거 기반으로 답변하도록 단계별로 폴백한다.

- 계획(create_plan)      : Gemini 필요 → 실패 시 원 질문을 검색어로 사용
- 검색(retrieve_evidence): 로컬 임베딩(오프라인) → 실패 시 mock_retrieve
- 답변(generate_answer)  : Gemini 필요 → 실패 시 검색 근거로 템플릿 답변
- 검증(grounding_check)  : 로컬 NLI(오프라인) → 실패 시 건너뜀
"""
from backend.app.agent.grounding import grounding_check
from backend.app.agent.mocks import mock_retrieve
from backend.app.agent.planner import create_plan
from backend.app.agent.answer_generator import generate_answer
from backend.app.agent.retriever import retrieve_evidence
from backend.app.agent.schemas import AgentResult



def _plan_query(question: str) -> tuple[str, bool]:
    """검색어 생성. LLM 계획 실패 시 원 질문을 그대로 사용한다."""
    try:
        plan = create_plan(question)
        if plan.search_queries:
            return plan.search_queries[0], True
    except Exception:
        pass
    return question, False


def _retrieve(queries: list[str], top_k: int = 6):
    """여러 검색어로 검색해 병합한다.

    LLM 계획 검색어는 질문을 일반화하며 핵심 키워드(예: '채용')를 잃기도 하므로,
    원 질문과 계획 검색어를 함께 검색해 근거 누락을 줄인다.
    """
    # 검색어별 결과 리스트
    per_query = []
    for query in queries:
        try:
            per_query.append(retrieve_evidence(query, top_k=top_k))
        except Exception:
            per_query.append([])

    # round-robin 병합: 점수는 검색어마다 스케일이 달라(일반화 질의가 고득점) 단순 정렬 시
    # 특정 키워드 질의의 관련 근거가 밀려난다. 각 검색어 상위 결과를 번갈아 넣어 대표성을 보장한다.
    merged: dict[str, object] = {}
    order: list[str] = []
    for rank in range(top_k):
        for results in per_query:
            if rank < len(results):
                e = results[rank]
                if e.article_id not in merged:
                    merged[e.article_id] = e
                    order.append(e.article_id)

    if not merged:
        return mock_retrieve(queries[0] if queries else "")

    return [merged[aid] for aid in order][:top_k]


def _template_answer(evidence) -> dict[str, str]:
    """Gemini 없이 검색 근거만으로 만드는 답변(오프라인 폴백)."""
    top = evidence[0]
    articles = ", ".join(dict.fromkeys(e.article for e in evidence[:3] if e.article))
    body = top.text.strip().replace("\n", " ")
    if len(body) > 320:
        body = body[:320] + "…"
    answer = (
        f"검색된 법령 근거를 종합하면 다음과 같습니다.\n\n"
        f"{top.article}: {body}\n\n"
        f"관련 조항: {articles}"
    )
    return {
        "verdict": "근거 기반 답변",
        "answer": answer,
        "confidence": "근거 충분",
    }


def _make_answer(question: str, evidence) -> tuple[dict[str, str], bool]:
    """답변 생성. LLM 실패 시 템플릿 답변으로 폴백. (결과, LLM사용여부)"""
    try:
        return generate_answer(question, evidence), True
    except Exception:
        return _template_answer(evidence), False


def _safe_grounding(answer: str, evidence) -> str:
    """로컬 NLI 검증. 모델 미설치 등으로 실패하면 검증을 건너뛴다."""
    try:
        return grounding_check(answer=answer, evidence=evidence)
    except Exception:
        return "skipped"


def run_agent(question: str) -> AgentResult:
    if not question.strip():
        raise ValueError(
            "질문을 입력해야 합니다."
        )

    search_query, planned = _plan_query(
        question
    )
    steps = [
        "질문 입력",
        (
            "조사 계획 생성 "
            f"({'LLM 계획' if planned else '원 질문 사용'})"
        ),
    ]

    queries = [question]

    if (
        planned
        and search_query
        and search_query != question
    ):
        queries.append(search_query)

    evidence = _retrieve(
        queries,
        top_k=6,
    )
    steps.append(
        "조문 검색 1회 "
        f"(검색어 {len(queries)}개) "
        f"→ {len(evidence)}건"
    )

    if not evidence:
        steps.append(
            "검색 근거 없음: 판단 보류"
        )

        return AgentResult(
            verdict="판단 보류",
            answer=(
                "검색된 법령·가이드라인 근거가 없어 "
                "답변하기 어렵습니다."
            ),
            confidence="근거 부족",
            citations=[],
            steps=steps,
            retry_count=0,
        )

    answer_data, used_llm = _make_answer(
        question,
        evidence,
    )

    if not used_llm:
        steps.extend([
            "근거 인용 답변 생성",
            "답변 확정",
        ])

        return AgentResult(
            verdict=answer_data["verdict"],
            answer=answer_data["answer"],
            confidence=answer_data["confidence"],
            citations=evidence,
            steps=steps,
            retry_count=0,
        )

    grounding_result = _safe_grounding(
        answer_data["answer"],
        evidence,
    )
    steps.append(
        f"근거 검증: {grounding_result}"
    )

    if grounding_result == "entailment":
        steps.append("답변 확정")

        return AgentResult(
            verdict=answer_data["verdict"],
            answer=answer_data["answer"],
            confidence=answer_data["confidence"],
            citations=evidence,
            steps=steps,
            retry_count=0,
        )

    fallback_answer = _template_answer(
        evidence
    )
    steps.extend([
        "근거 검증 미통과",
        "근거 직접 인용 답변으로 전환",
        "답변 확정",
    ])

    return AgentResult(
        verdict=fallback_answer["verdict"],
        answer=fallback_answer["answer"],
        confidence=fallback_answer["confidence"],
        citations=evidence,
        steps=steps,
        retry_count=0,
    )