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

GUIDELINE_SOURCES = [
    {
        "path": PROJECT_ROOT / "ai_enforcement.txt",
        "document_name": (
            "2026 인공지능 영향평가 가이드라인"
        ),
        "chunk_prefix": "AI_IMPACT_GUIDE",
        "start_marker": (
            "제1장\n인공지능 영향평가 개요"
        ),
    },
    {
        "path": PROJECT_ROOT / "msit_guideline.txt",
        "document_name": (
            "인공지능 투명성 확보 가이드라인"
        ),
        "chunk_prefix": "AI_TRANSPARENCY_GUIDE",
        "start_marker": (
            "투명성 확보 의무의 취지"
        ),
    },
]

GUIDELINE_CHUNK_SIZE = 900
GUIDELINE_OVERLAP_LINES = 2

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

def clean_guideline_lines(
    raw_text: str,
    document_name: str,
) -> list[str]:
    cleaned_lines = []

    for raw_line in raw_text.splitlines():
        line = re.sub(
            r"\s+",
            " ",
            raw_line,
        ).strip()

        if not line:
            continue

        if line == document_name:
            continue

        if line in {
            "CONTENTS",
            "목차",
        }:
            continue

        if re.fullmatch(r"\d+", line):
            continue

        if re.search(r"·{3,}\d+$", line):
            continue

        cleaned_lines.append(line)

    return cleaned_lines

def is_guideline_heading(line: str) -> bool:
    if len(line) > 80:
        return False

    return bool(
        re.match(
            r"^(제\d+[장절]|"
            r"\d+\)\s|"
            r"부록)",
            line,
        )
    )


def extract_law_references(
    text: str,
) -> list[str]:
    references = set()

    pattern = re.compile(
        r"(?:인공지능\s*기본법|인공지능기본법|법)"
        r"\s*제\s*(\d+)\s*조"
        r"(?:의\s*(\d+))?"
    )

    for match in pattern.finditer(text):
        number = int(match.group(1))
        sub_number = int(match.group(2) or 0)

        if sub_number:
            chunk_id = (
                f"AI_BASIC_ACT_{number}_{sub_number}"
            )
        else:
            chunk_id = f"AI_BASIC_ACT_{number}"

        references.add(chunk_id)

    return sorted(references)

def parse_guideline(
    raw_text: str,
    document_name: str,
    chunk_prefix: str,
    source_name: str,
) -> list[dict]:
    lines = clean_guideline_lines(
        raw_text=raw_text,
        document_name=document_name,
    )

    chunks = []
    current_lines = []
    current_title = document_name

    def append_chunk(
        chunk_lines: list[str],
        chunk_title: str,
    ) -> None:
        article_text = " ".join(
            chunk_lines
        ).strip()

        if len(article_text) < 30:
            return

        chunk_number = len(chunks) + 1

        chunks.append({
            "chunk_id": (
                f"{chunk_prefix}_{chunk_number}"
            ),
            "document_name": document_name,
            "article_number": (
                f"문단 {chunk_number}"
            ),
            "article_title": chunk_title,
            "article_text": article_text,
            "source_url": source_name,
            "references": extract_law_references(
                article_text
            ),
        })

    for line in lines:
        if is_guideline_heading(line):
            current_length = len(
                " ".join(current_lines)
            )

            if current_length >= 250:
                append_chunk(
                    current_lines,
                    current_title,
                )
                current_lines = []

            current_title = line

        candidate_lines = [
            *current_lines,
            line,
        ]

        candidate_length = len(
            " ".join(candidate_lines)
        )

        if (
            current_lines
            and candidate_length
            > GUIDELINE_CHUNK_SIZE
        ):
            append_chunk(
                current_lines,
                current_title,
            )

            current_lines = current_lines[
                -GUIDELINE_OVERLAP_LINES:
            ]

        current_lines.append(line)

    if current_lines:
        append_chunk(
            current_lines,
            current_title,
        )

    return chunks

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

    print(
        f"{DOCUMENT_NAME}: "
        f"{len(chunks)}개 조문"
    )

    for source in GUIDELINE_SOURCES:
        source_path = source["path"]

        if not source_path.exists():
            raise FileNotFoundError(
                f"가이드라인 파일이 없습니다: "
                f"{source_path}"
            )

        guideline_text = source_path.read_text(
            encoding="utf-8"
        )

        start_marker = source["start_marker"]
        start_index = guideline_text.find(
            start_marker
        )

        if start_index == -1:
            raise RuntimeError(
                f"본문 시작 위치를 찾지 못했습니다: "
                f"{source_path.name}"
            )

        guideline_text = guideline_text[
            start_index:
        ]

        guideline_chunks = parse_guideline(
            raw_text=guideline_text,
            document_name=source[
                "document_name"
            ],
            chunk_prefix=source[
                "chunk_prefix"
            ],
            source_name=source_path.name,
        )

        print(
            f"{source['document_name']}: "
            f"{len(guideline_chunks)}개 청크"
        )

        chunks.extend(guideline_chunks)

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

    print(f"전처리 완료: {len(chunks)}개 청크")
    print(f"저장 위치: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()