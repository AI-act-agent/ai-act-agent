import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

SOURCE_PATH = PROJECT_ROOT / "ai_basic_law.txt"

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "law_chunks.json"
)

DOCUMENT_NAME = (
    "인공지능 발전과 신뢰 기반 조성 등에 관한 기본법"
)

ARTICLE_PATTERN = re.compile(
    r"(?m)^제(?P<number>\d+)조"
    r"(?:의(?P<sub_number>\d+))?"
    r"\((?P<title>[^)\n]+)\)\s*"
)

def clean_article_text(text: str) -> str:
    cleaned_lines = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if re.fullmatch(
            r"법제처\s+\d+\s+국가법령정보센터",
            line,
        ):
            continue

        if line == DOCUMENT_NAME:
            continue

        if re.match(r"^제\d+장\s+", line):
            continue

        cleaned_lines.append(line)

    cleaned_text = " ".join(cleaned_lines)

    return re.sub(
        r"\s+",
        " ",
        cleaned_text,
    ).strip()

def parse_articles(raw_text: str) -> list[dict]:
    matches = list(ARTICLE_PATTERN.finditer(raw_text))
    chunks_by_order = {}

    for index, match in enumerate(matches):
        body_start = match.end()

        if index + 1 < len(matches):
            body_end = matches[index + 1].start()
        else:
            body_end = len(raw_text)

        article_text = clean_article_text(
            raw_text[body_start:body_end]
        )

        if not article_text:
            continue

        number = int(match.group("number"))
        sub_number_text = match.group("sub_number")
        sub_number = int(sub_number_text or 0)

        article_number = f"제{number}조"

        if sub_number:
            article_number += f"의{sub_number}"

        chunk_suffix = (
            f"{number}_{sub_number}"
            if sub_number
            else str(number)
        )

        chunks_by_order[(number, sub_number)] = {
            "chunk_id": f"AI_BASIC_ACT_{chunk_suffix}",
            "document_name": DOCUMENT_NAME,
            "article_number": article_number,
            "article_title": match.group("title").strip(),
            "article_text": article_text,
            "source_url": SOURCE_PATH.name,
            "references": [],
        }

    return [
        chunks_by_order[key]
        for key in sorted(chunks_by_order)
    ]

def main() -> None:
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(
            f"법률 원문 파일이 없습니다: {SOURCE_PATH}"
        )

    raw_text = SOURCE_PATH.read_text(
        encoding="utf-8"
    )

    chunks = parse_articles(raw_text)

    if not chunks:
        raise RuntimeError(
            "법률 원문에서 조문을 찾지 못했습니다."
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            chunks,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"전처리 완료: {len(chunks)}개 조문")
    print(f"저장 위치: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()