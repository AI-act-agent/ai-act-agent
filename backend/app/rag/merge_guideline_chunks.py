import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

PROCESSED_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)

BASE_CHUNKS_PATH = (
    PROCESSED_DIR
    / "law_chunks.json"
)

JUDGMENT_GUIDE_PATH = (
    PROCESSED_DIR
    / "판단가이드라인_chunks.jsonl"
)

DUTY_GUIDE_PATH = (
    PROCESSED_DIR
    / "책무가이드라인_chunks.jsonl"
)

OUTPUT_PATH = (
    PROCESSED_DIR
    / "rag_chunks.json"
)

REQUIRED_FIELDS = {
    "chunk_id",
    "document_name",
    "article_number",
    "article_title",
    "article_text",
    "source_url",
    "references",
}


def _clean(value) -> str:
    if value is None:
        return ""

    return " ".join(
        str(value).split()
    ).strip()


def _load_json(path: Path) -> list[dict]:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def _load_jsonl(path: Path) -> list[dict]:
    rows = []

    for line in path.read_text(
        encoding="utf-8"
    ).splitlines():
        if not line.strip():
            continue

        rows.append(
            json.loads(line)
        )

    return rows


def _convert_judgment_chunk(
    row: dict,
) -> dict:
    chunk_id = _clean(
        row.get("chunk_id")
    )
    section_id = _clean(
        row.get("section_id")
    )
    title = _clean(
        row.get("title")
    )
    content = _clean(
        row.get("content")
    )
    document_name = (
        _clean(row.get("출처"))
        or "고영향 인공지능 판단 가이드라인"
    )

    return {
        "chunk_id": chunk_id,
        "document_name": document_name,
        "article_number": (
            section_id or chunk_id
        ),
        "article_title": (
            title or section_id or chunk_id
        ),
        "article_text": content,
        "source_url": (
            "판단가이드라인_chunks.jsonl"
        ),
        "references": [
            "AI_BASIC_ACT_2",
            "AI_BASIC_ACT_33",
            "AI_BASIC_DECREE_25",
        ],
    }


def _convert_duty_chunk(
    row: dict,
) -> dict:
    chunk_id = _clean(
        row.get("chunk_id")
    )
    item_number = _clean(
        row.get("항목번호")
    )
    title = (
        _clean(row.get("제목"))
        or _clean(row.get("목표"))
        or chunk_id
    )
    content = _clean(
        row.get("content")
    )
    document_name = (
        _clean(row.get("출처"))
        or "고영향 인공지능 사업자 책무 가이드라인"
    )

    return {
        "chunk_id": chunk_id,
        "document_name": document_name,
        "article_number": (
            item_number or chunk_id
        ),
        "article_title": title,
        "article_text": content,
        "source_url": (
            "책무가이드라인_chunks.jsonl"
        ),
        "references": [
            "AI_BASIC_ACT_34",
        ],
    }


def _validate_chunks(
    chunks: list[dict],
) -> None:
    seen_ids = set()

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):
        missing_fields = (
            REQUIRED_FIELDS - set(chunk)
        )

        if missing_fields:
            raise ValueError(
                f"{index}번째 청크 필드 누락: "
                f"{sorted(missing_fields)}"
            )

        chunk_id = _clean(
            chunk["chunk_id"]
        )
        article_text = _clean(
            chunk["article_text"]
        )

        if not chunk_id:
            raise ValueError(
                f"{index}번째 청크 ID가 없습니다."
            )

        if not article_text:
            raise ValueError(
                f"{chunk_id}의 본문이 비어 있습니다."
            )

        if chunk_id in seen_ids:
            raise ValueError(
                f"중복 chunk_id: {chunk_id}"
            )

        seen_ids.add(chunk_id)


def merge_guideline_chunks() -> list[dict]:
    base_chunks = _load_json(
        BASE_CHUNKS_PATH
    )

    for chunk in base_chunks:
        chunk_id = chunk.get("chunk_id")

        if chunk_id == "AI_BASIC_ACT_2":
            chunk["references"] = []

        elif chunk_id == "AI_BASIC_ACT_33":
            chunk["references"] = [
                "AI_BASIC_DECREE_25",
                "AI_BASIC_DECREE_26",
            ]

    judgment_rows = _load_jsonl(
        JUDGMENT_GUIDE_PATH
    )
    judgment_chunks = [
        _convert_judgment_chunk(row)
        for row in judgment_rows
    ]

    duty_rows = _load_jsonl(
        DUTY_GUIDE_PATH
    )
    duty_chunks = [
        _convert_duty_chunk(row)
        for row in duty_rows
        if row.get("청크유형") == "책무항목"
    ]

    merged_chunks = [
        *base_chunks,
        *judgment_chunks,
        *duty_chunks,
    ]

    _validate_chunks(
        merged_chunks
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            merged_chunks,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"기존 법령·가이드라인: "
        f"{len(base_chunks)}개"
    )
    print(
        f"고영향 판단 가이드라인: "
        f"{len(judgment_chunks)}개"
    )
    print(
        f"사업자 책무 항목: "
        f"{len(duty_chunks)}개"
    )
    print(
        f"통합 완료: "
        f"{len(merged_chunks)}개 청크"
    )
    print(
        f"저장 위치: {OUTPUT_PATH}"
    )

    return merged_chunks


if __name__ == "__main__":
    merge_guideline_chunks()