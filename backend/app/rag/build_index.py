"""검색 인덱스(벡터스토어) 통합 빌드 스크립트.

법령 조문(law_chunks.json)과 가이드라인 전처리 청크 3종
(사례집·판단가이드라인·책무가이드라인)을 파이프라인 스키마로 통합한 뒤
하나의 벡터스토어로 임베딩한다.

실행(프로젝트 루트에서):
    python -m backend.app.rag.build_index

임베딩은 로컬(sentence-transformers)이라 GEMINI_API_KEY 없이도 동작한다.
"""
import json
from pathlib import Path

from backend.app.rag.pipeline import (
    PROJECT_ROOT,
    VECTOR_STORE_PATH,
    build_vector_store,
)

PROCESSED = PROJECT_ROOT / "data" / "processed"
LAW_CHUNKS = PROCESSED / "law_chunks.json"
MERGED_PATH = PROCESSED / "all_chunks.json"

# 파이프라인이 요구하는 스키마 필드
SCHEMA_FIELDS = (
    "chunk_id",
    "document_name",
    "article_number",
    "article_title",
    "article_text",
    "source_url",
    "references",
)


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _norm(chunk: dict, *, prefix: str, number_key: str, title_key: str) -> dict:
    """가이드라인 청크 하나를 파이프라인 스키마로 변환."""
    source = chunk.get("출처", "")
    return {
        "chunk_id": f"{prefix}_{chunk['chunk_id']}",
        "document_name": source,
        "article_number": str(chunk.get(number_key) or chunk.get("chunk_id", "")),
        "article_title": str(chunk.get(title_key) or chunk.get("질문", "")),
        "article_text": chunk.get("content", "").strip(),
        "source_url": source,  # 가이드라인은 URL이 없어 문서명을 출처로 사용
        "references": [],
    }


def build_all_chunks() -> list[dict]:
    """법령 + 가이드라인 청크를 통합한 리스트를 반환하고 all_chunks.json에 저장."""
    law = json.loads(LAW_CHUNKS.read_text(encoding="utf-8"))

    guideline_specs = [
        ("사례집_chunks.jsonl", "CASE", "사례번호", "제목"),
        ("판단가이드라인_chunks.jsonl", "JUDGE", "section_id", "title"),
        ("책무가이드라인_chunks.jsonl", "OBLIG", "항목번호", "제목"),
    ]

    merged = list(law)
    for filename, prefix, number_key, title_key in guideline_specs:
        items = _read_jsonl(PROCESSED / filename)
        merged.extend(
            _norm(c, prefix=prefix, number_key=number_key, title_key=title_key)
            for c in items
        )
        print(f"  + {filename}: {len(items)}개")

    # 스키마 필드만 유지 + 빈 본문 제거
    cleaned = []
    seen = set()
    for c in merged:
        if not c.get("article_text"):
            continue
        if c["chunk_id"] in seen:
            continue
        seen.add(c["chunk_id"])
        cleaned.append({k: c.get(k, "") for k in SCHEMA_FIELDS})

    MERGED_PATH.write_text(
        json.dumps(cleaned, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"통합 청크 {len(cleaned)}개 → {MERGED_PATH.name} 저장 (법령 {len(law)} + 가이드라인 {len(cleaned) - len(law)})")
    return cleaned


def main():
    print("1) 청크 통합")
    build_all_chunks()
    print("2) 임베딩 및 벡터스토어 구축")
    build_vector_store(chunks_path=MERGED_PATH, output_path=VECTOR_STORE_PATH)
    print(f"완료 → {VECTOR_STORE_PATH}")


if __name__ == "__main__":
    main()
