from backend.app.agent.schemas import Evidence


def mock_retrieve(
    question: str,
    top_k: int = 5,
) -> list[Evidence]:
    """RAG 검색 결과를 대신하는 임시 함수"""

    if "근거 없음" in question:
        return []

    mock_evidence = [
        Evidence(
            article_id="mock_article_1",
            article="제00조제1항",
            text=(
                "에이전트 실행 흐름을 확인하기 위한 테스트용 가상 조문입니다. "
                "실제 법령 내용이 아닙니다."
            ),
            source_url="mock://article/1",
            score=0.85,
        )
    ]

    return mock_evidence[:top_k]