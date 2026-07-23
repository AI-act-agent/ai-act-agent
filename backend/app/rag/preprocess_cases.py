"""사례집 전처리 (복구판).

기존 노트북 추출은 목차(<사례 N> + 페이지번호)를 긁어 Q/A 본문이 비어 있었다.
이 스크립트는 상세 본문 형식('사례 NN 제목 / Q ... / A ... / 핵심 포인트 ...')을
정확히 추출해 data/processed/사례집_chunks.jsonl 을 재생성한다.

실행:
    python -m backend.app.rag.preprocess_cases
"""
import json
import re
from pathlib import Path

import pdfplumber

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PDF_CANDIDATES = [
    PROJECT_ROOT / "data" / "processed" / "인공지능기본법_지원데스크_사례집.pdf",
    PROJECT_ROOT / ".venv" / "인공지능기본법_지원데스크_사례집.pdf",
]
OUTPUT = PROJECT_ROOT / "data" / "processed" / "사례집_chunks.jsonl"
SOURCE_NAME = "인공지능기본법 지원데스크 사례집"


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_cases(full: str) -> list[dict]:
    """'사례 NN' 헤더로 블록을 나눠 Q/A/핵심포인트를 추출한다."""
    heads = list(re.finditer(r"사례\s*0?(\d{1,2})(?=[\s가-힣])", full))
    seen: set[int] = set()
    cases: list[dict] = []

    for i, head in enumerate(heads):
        num = int(head.group(1))
        start = head.end()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(full)
        block = full[start:end]

        q_marker = re.search(r"\bQ\s", block)
        a_marker = re.search(r"\bA\s", block)
        # 상세 본문만: Q 다음에 A 가 있어야 함(목차 블록은 걸러짐)
        if not q_marker or not a_marker or a_marker.start() <= q_marker.start():
            continue
        if num in seen:
            continue

        title = re.sub(r"\([^)]*\)\s*$", "", _clean(block[: q_marker.start()])).strip()
        question = _clean(block[q_marker.end() : a_marker.start()])
        rest = block[a_marker.end() :]
        kp_marker = re.search(r"핵심\s*포인트", rest)
        answer = _clean(rest[: kp_marker.start()] if kp_marker else rest)
        key_point = _clean(rest[kp_marker.end() :]) if kp_marker else ""

        if len(answer) < 20:
            continue

        seen.add(num)
        content = f"[사례 {num}] {title}\nQ: {question}\nA: {answer}"
        if key_point:
            content += f"\n핵심 포인트: {key_point}"

        cases.append(
            {
                "chunk_id": f"사례집_{num:03d}",
                "사례번호": str(num),
                "제목": title,
                "질문": question,
                "답변": answer,
                "핵심포인트": key_point,
                "content": content,
                "출처": SOURCE_NAME,
                "청크유형": "QA사례",
            }
        )

    cases.sort(key=lambda c: int(c["사례번호"]))
    return cases


def main() -> None:
    pdf_path = next((p for p in PDF_CANDIDATES if p.exists()), None)
    if pdf_path is None:
        raise FileNotFoundError(
            "사례집 PDF를 찾을 수 없습니다: " + " / ".join(map(str, PDF_CANDIDATES))
        )

    with pdfplumber.open(pdf_path) as pdf:
        full = "\n".join(page.extract_text() or "" for page in pdf.pages)

    cases = extract_cases(full)

    with OUTPUT.open("w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")

    print(f"사례 {len(cases)}개 추출 → {OUTPUT}")
    print("번호:", [c["사례번호"] for c in cases])


if __name__ == "__main__":
    main()
