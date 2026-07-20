from backend.app.agent.schemas import Evidence
from backend.app.rag.pipeline import retrieve as rag_retrieve

def _to_evidence(item: dict) -> Evidence:
    score = item.get("score")

    if score is None:
        score = 0.0

    article_text = item["article_text"]
    article_title = item.get(
        "article_title",
        "",
    ).strip()

    if article_title:
        article_text = (
            f"{article_title}\n{article_text}"
        )

    return Evidence(
        article_id=item["chunk_id"],
        article=item["article_number"],
        text=article_text,
        source_url=item["source_url"],
        score=float(score),
    )

def retrieve_evidence(
    question: str,
    top_k: int = 5,
    expand_reference: bool = True,
) -> list[Evidence]:
    rag_results = rag_retrieve(
        question=question,
        top_k=top_k,
        expand_reference=expand_reference,
    )

    return [
        _to_evidence(item)
        for item in rag_results
    ]