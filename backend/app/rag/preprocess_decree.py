import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

RAW_DECREE_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "ai_basic_decree.json"
)

LAW_CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "law_chunks.json"
)


def load_json(path):
    with Path(path).open(
        "r",
        encoding="utf-8-sig"
    ) as file:
        return json.load(file)


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with path.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


def to_list(value):
    """객체 하나와 배열을 모두 배열 형태로 통일한다."""
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def collect_contents(value):
    """항·호·목 안에 들어 있는 내용을 순서대로 수집한다."""
    contents = []

    if isinstance(value, list):
        for item in value:
            contents.extend(
                collect_contents(item)
            )

    elif isinstance(value, dict):
        for key, item in value.items():
            if (
                key.endswith("내용")
                and isinstance(item, str)
            ):
                cleaned = " ".join(
                    item.split()
                )

                if cleaned:
                    contents.append(cleaned)

            elif isinstance(item, (dict, list)):
                contents.extend(
                    collect_contents(item)
                )

    return contents


def make_article_identifiers(article):
    number = str(
        article.get("조문번호", "")
    ).strip()

    branch_number = str(
        article.get("조문가지번호", "")
    ).strip()

    if branch_number and branch_number != "0":
        chunk_suffix = (
            f"{number}_{branch_number}"
        )
        article_number = (
            f"제{number}조의{branch_number}"
        )
    else:
        chunk_suffix = number
        article_number = f"제{number}조"

    return chunk_suffix, article_number


def extract_act_references(text):
    """
    '법 제31조', '법 제2조의2' 형태를 찾아
    AI기본법 청크 ID로 변환한다.
    """
    references = []

    pattern = re.compile(
        r"법\s*제(\d+)조(?:의(\d+))?"
    )

    for number, branch in pattern.findall(text):
        if branch:
            reference_id = (
                f"AI_BASIC_ACT_{number}_{branch}"
            )
        else:
            reference_id = (
                f"AI_BASIC_ACT_{number}"
            )

        if reference_id not in references:
            references.append(reference_id)

    return references


def build_decree_chunks(payload):
    law_data = payload.get("법령", {})

    articles = (
        law_data
        .get("조문", {})
        .get("조문단위", [])
    )

    decree_chunks = []

    for article in to_list(articles):
        # '제1장 총칙' 같은 장 제목은 제외
        if article.get("조문여부") != "조문":
            continue

        chunk_suffix, article_number = (
            make_article_identifiers(article)
        )

        if not chunk_suffix:
            continue

        main_text = " ".join(
            str(
                article.get("조문내용", "")
            ).split()
        )

        detail_texts = collect_contents(
            article.get("항")
        )

        text_parts = []

        if main_text:
            text_parts.append(main_text)

        for detail_text in detail_texts:
            if detail_text not in text_parts:
                text_parts.append(detail_text)

        article_text = "\n".join(text_parts)

        if not article_text:
            continue

        effective_date = str(
            article.get(
                "조문시행일자",
                "20260122"
            )
        )

        if len(effective_date) == 8:
            effective_date = (
                f"{effective_date[:4]}-"
                f"{effective_date[4:6]}-"
                f"{effective_date[6:]}"
            )

        decree_chunks.append({
            "chunk_id": (
                f"AI_BASIC_DECREE_{chunk_suffix}"
            ),
            "document_name": (
                "인공지능 발전과 신뢰 기반 "
                "조성 등에 관한 기본법 시행령"
            ),
            "document_type": "대통령령",
            "article_number": article_number,
            "article_title": article.get(
                "조문제목",
                ""
            ),
            "article_text": article_text,
            "effective_date": effective_date,
            "source_url": (
                "https://www.law.go.kr/법령/"
                "인공지능발전과신뢰기반조성등에관한"
                "기본법시행령"
            ),
            "references": extract_act_references(
                article_text
            )
        })

    return decree_chunks


def merge_chunks(
    existing_chunks,
    decree_chunks
):
    """
    기존 법률·가이드라인 청크에 시행령을 추가하고,
    법률 청크에서도 시행령을 역참조하도록 연결한다.
    """

    # 재실행 시 시행령이 중복되지 않게 제거
    merged = [
        chunk
        for chunk in existing_chunks
        if not chunk["chunk_id"].startswith(
            "AI_BASIC_DECREE_"
        )
    ]

    # 기존 시행령 참조를 제거하고 다시 생성
    for chunk in merged:
        references = chunk.get(
            "references",
            []
        )

        chunk["references"] = [
            reference
            for reference in references
            if not reference.startswith(
                "AI_BASIC_DECREE_"
            )
        ]

    chunk_index = {
        chunk["chunk_id"]: chunk
        for chunk in merged
    }

    # 시행령 → 법률 참조를 법률 → 시행령에도 추가
    for decree_chunk in decree_chunks:
        decree_id = decree_chunk["chunk_id"]

        for act_id in decree_chunk["references"]:
            act_chunk = chunk_index.get(act_id)

            if act_chunk is None:
                continue

            references = act_chunk.setdefault(
                "references",
                []
            )

            if decree_id not in references:
                references.append(decree_id)

    merged.extend(decree_chunks)

    return merged


def main():
    if not RAW_DECREE_PATH.exists():
        raise FileNotFoundError(
            f"시행령 원본이 없습니다: "
            f"{RAW_DECREE_PATH}"
        )

    if not LAW_CHUNKS_PATH.exists():
        raise FileNotFoundError(
            f"기존 법령 청크가 없습니다: "
            f"{LAW_CHUNKS_PATH}"
        )

    payload = load_json(
        RAW_DECREE_PATH
    )

    existing_chunks = load_json(
        LAW_CHUNKS_PATH
    )

    decree_chunks = build_decree_chunks(
        payload
    )

    if not decree_chunks:
        raise ValueError(
            "시행령 조문을 찾지 못했습니다."
        )

    merged_chunks = merge_chunks(
        existing_chunks=existing_chunks,
        decree_chunks=decree_chunks
    )

    save_json(
        LAW_CHUNKS_PATH,
        merged_chunks
    )

    print(
        f"시행령 {len(decree_chunks)}개 조문을 "
        f"law_chunks.json에 추가했습니다."
    )
    print(
        f"전체 청크 수: {len(merged_chunks)}"
    )


if __name__ == "__main__":
    main()