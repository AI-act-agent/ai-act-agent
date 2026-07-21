from functools import lru_cache

from sentence_transformers import SentenceTransformer
import argparse
import json
import os
import time
import re
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from google import genai


load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
LOCAL_EMBEDDING_MODEL = os.getenv(
    "LOCAL_EMBEDDING_MODEL",
    (
        "sentence-transformers/"
        "paraphrase-multilingual-MiniLM-L12-v2"
    ),
)
GENERATION_MODEL = os.getenv("GEMINI_GENERATION_MODEL")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY가 .env 파일에 없습니다."
    )

client = genai.Client(api_key=API_KEY)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "law_chunks.json"
)

VECTOR_STORE_PATH = (
    PROJECT_ROOT
    / "data"
    / "vector_store"
    / "law_embeddings.json"
)


def load_json(path):
    with Path(path).open(
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def save_json(path, data):
    output_path = Path(path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output_path.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


def validate_chunks(chunks):
    required_fields = {
        "chunk_id",
        "document_name",
        "article_number",
        "article_title",
        "article_text",
        "source_url",
        "references"
    }

    if not isinstance(chunks, list):
        raise ValueError(
            "law_chunks JSON의 최상위 구조는 배열이어야 합니다."
        )

    seen_ids = set()

    for index, chunk in enumerate(chunks):
        missing = required_fields - set(chunk.keys())

        if missing:
            raise ValueError(
                f"{index}번 조문에서 필드가 누락됐습니다: "
                f"{sorted(missing)}"
            )

        chunk_id = chunk["chunk_id"]

        if chunk_id in seen_ids:
            raise ValueError(
                f"중복 chunk_id가 있습니다: {chunk_id}"
            )

        if not chunk["article_text"].strip():
            raise ValueError(
                f"조문 본문이 비어 있습니다: {chunk_id}"
            )

        if not isinstance(chunk["references"], list):
            raise ValueError(
                f"references는 배열이어야 합니다: {chunk_id}"
            )

        seen_ids.add(chunk_id)


def build_embedding_text(chunk):
    return (
        f"법령명: {chunk['document_name']}\n"
        f"조문: {chunk['article_number']}\n"
        f"조문 제목: {chunk['article_title']}\n"
        f"조문 원문: {chunk['article_text']}"
    )


@lru_cache(maxsize=1)
def load_embedding_model():
    print(
        "로컬 임베딩 모델을 불러옵니다: "
        f"{LOCAL_EMBEDDING_MODEL}"
    )

    model = SentenceTransformer(
        LOCAL_EMBEDDING_MODEL
    )

    print("로컬 임베딩 모델 로딩 완료")

    return model


def create_embeddings(
    texts,
    batch_size=32,
):
    if not texts:
        raise ValueError(
            "임베딩할 텍스트 목록이 비어 있습니다."
        )

    model = load_embedding_model()

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=len(texts) > 1,
    )

    return embeddings.tolist()


def create_embedding(text):
    if not text or not text.strip():
        raise ValueError(
            "임베딩할 텍스트가 비어 있습니다."
        )

    return create_embeddings(
        [text],
        batch_size=1,
    )[0]


def cosine_similarity(vector_a, vector_b):
    a = np.asarray(vector_a, dtype=float)
    b = np.asarray(vector_b, dtype=float)

    denominator = (
        np.linalg.norm(a)
        * np.linalg.norm(b)
    )

    if denominator == 0:
        return 0.0

    return float(
        np.dot(a, b) / denominator
    )


def build_vector_store(
    chunks_path=DEFAULT_CHUNKS_PATH,
    output_path=VECTOR_STORE_PATH
):
    chunks = load_json(chunks_path)
    validate_chunks(chunks)

    records = []

    print(
        f"총 {len(chunks)}개 조문의 임베딩을 생성합니다."
    )

    embedding_texts = [
        build_embedding_text(chunk)
        for chunk in chunks
    ]

    embeddings = create_embeddings(
        embedding_texts
    )

    for index, (chunk, embedding) in enumerate(
        zip(chunks, embeddings),
        start=1,
    ):
        records.append({
            "chunk": chunk,
            "embedding": embedding,
        })

        print(
            f"[{index}/{len(chunks)}] "
            f"{chunk['chunk_id']} 완료"
        )

    save_json(output_path, records)

    print(f"벡터 저장 완료: {output_path}")

    return records


def load_vector_store(
    vector_store_path=VECTOR_STORE_PATH
):
    path = Path(vector_store_path)

    if not path.exists():
        raise FileNotFoundError(
            "벡터 저장소가 없습니다. "
            "먼저 --build 명령을 실행하세요."
        )

    return load_json(path)


SEARCH_STOPWORDS = {
    "관련",
    "대한",
    "무엇",
    "무엇인가요",
    "어떻게",
    "해야",
    "하나요",
    "인가요",
}


def normalize_search_text(text):
    normalized = text.lower()

    replacements = {
        r"생\s+성형": "생성형",
        r"고\s+영향": "고영향",
        r"인\s+공지능": "인공지능",
        r"저\s+작권": "저작권",
    }

    for pattern, replacement in replacements.items():
        normalized = re.sub(
            pattern,
            replacement,
            normalized,
        )

    return re.sub(
        r"\s+",
        " ",
        normalized,
    ).strip()


def extract_search_terms(text):
    normalized = normalize_search_text(text)

    return {
        term
        for term in re.findall(
            r"[가-힣a-z0-9]+",
            normalized,
        )
        if (
            len(term) >= 2
            and term not in SEARCH_STOPWORDS
        )
    }


def calculate_lexical_score(
    question,
    chunk,
):
    query_terms = extract_search_terms(
        question
    )

    if not query_terms:
        return 0.0

    document_text = " ".join([
        chunk["document_name"],
        chunk["article_number"],
        chunk["article_title"],
        chunk["article_text"],
    ])

    normalized_document = normalize_search_text(
        document_text
    )

    matched_count = sum(
        1
        for term in query_terms
        if term in normalized_document
    )

    return matched_count / len(query_terms)

def calculate_intent_score(
    question,
    chunk,
):
    """질문의 의도와 청크 제목이 일치하는지 계산한다."""

    normalized_question = normalize_search_text(
        question
    )

    normalized_title = normalize_search_text(
        chunk["article_title"]
    )

    definition_query_markers = (
        "이란",
        "정의",
        "뜻",
    )

    definition_title_markers = (
        "정의",
        "개념",
        "용어",
    )

    asks_for_definition = any(
        marker in normalized_question
        for marker in definition_query_markers
    )

    has_definition_title = any(
        marker in normalized_title
        for marker in definition_title_markers
    )

    if (
        asks_for_definition
        and has_definition_title
    ):
        return 1.0

    return 0.0


def retrieve_v1(
    question,
    records,
    top_k=5
):
    if not question.strip():
        raise ValueError(
            "질문이 비어 있습니다."
        )

    normalized_question = normalize_search_text(
        question
    )

    question_embedding = create_embedding(
        normalized_question
    )
    results = []

    for record in records:
        dense_score = cosine_similarity(
            question_embedding,
            record["embedding"],
        )

        lexical_score = calculate_lexical_score(
            question,
            record["chunk"],
        )

        intent_score = calculate_intent_score(
            question,
            record["chunk"],
        )

        combined_score = (
            dense_score * 0.65
            + lexical_score * 0.25
            + intent_score * 0.10
        )

        results.append({
            **record["chunk"],
            "score": combined_score,
            "dense_score": dense_score,
            "lexical_score": lexical_score,
            "intent_score": intent_score,
            "retrieval_type": "hybrid",
        })

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results[:top_k]


def make_chunk_index(records):
    return {
        record["chunk"]["chunk_id"]: record["chunk"]
        for record in records
    }


def expand_references(
    search_results,
    chunk_index,
    max_total=8,
    max_depth=2
):
    expanded = []
    visited = set()

    queue = [
        (result, 0)
        for result in search_results
    ]

    while queue and len(expanded) < max_total:
        current, depth = queue.pop(0)
        current_id = current["chunk_id"]

        if current_id in visited:
            continue

        expanded.append(current)
        visited.add(current_id)

        if depth >= max_depth:
            continue

        for reference_id in current.get(
            "references",
            []
        ):
            if reference_id in visited:
                continue

            referenced_chunk = chunk_index.get(
                reference_id
            )

            if referenced_chunk is None:
                continue

            reference_result = {
                **referenced_chunk,
                "score": None,
                "retrieval_type": "reference"
            }

            queue.append(
                (reference_result, depth + 1)
            )

    return expanded


def format_evidence(evidence):
    blocks = []

    for item in evidence:
        block = (
            f"[{item['chunk_id']}]\n"
            f"{item['document_name']} "
            f"{item['article_number']} "
            f"({item['article_title']})\n"
            f"{item['article_text']}"
        )

        blocks.append(block)

    return "\n\n".join(blocks)


def generate_answer(
    question,
    evidence=None
):
    if not GENERATION_MODEL:
        return (
            "생성 모델이 설정되지 않아 "
            "검색 결과만 반환합니다."
        )

    if evidence:
        evidence_text = format_evidence(evidence)

        prompt = f"""
아래에 제공된 법령 근거만 사용하여 질문에 답하세요.

규칙:
1. 근거에 없는 내용을 단정하지 마세요.
2. 답변에 사용한 조문 번호를 표시하세요.
3. 정보가 부족하면 판단하기 어렵다고 명시하세요.
4. 법률 자문을 대체하지 않는 예비 안내임을 표시하세요.

질문:
{question}

법령 근거:
{evidence_text}
"""
    else:
        prompt = f"""
다음 AI기본법 관련 질문에 답하세요.

질문:
{question}
"""

    response = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=prompt
    )

    return response.text


def run_v0(question):
    start_time = time.perf_counter()

    answer = generate_answer(
        question=question,
        evidence=None
    )

    latency_ms = round(
        (time.perf_counter() - start_time)
        * 1000,
        2
    )

    return {
        "version": "V0",
        "question": question,
        "answer": answer,
        "retrieved_chunk_ids": [],
        "evidence": [],
        "latency_ms": latency_ms
    }


def retrieve(
    question,
    top_k=5,
    expand_reference=False,
    max_total=8,
    records=None
):
    if records is None:
        records = load_vector_store()

    evidence = retrieve_v1(
        question=question,
        records=records,
        top_k=top_k
    )

    if expand_reference:
        chunk_index = make_chunk_index(records)

        evidence = expand_references(
            search_results=evidence,
            chunk_index=chunk_index,
            max_total=max_total
        )

    return evidence


def run_v1(
    question,
    records,
    top_k=5
):
    start_time = time.perf_counter()

    evidence = retrieve_v1(
        question=question,
        records=records,
        top_k=top_k
    )

    answer = generate_answer(
        question=question,
        evidence=evidence
    )

    latency_ms = round(
        (time.perf_counter() - start_time)
        * 1000,
        2
    )

    return {
        "version": "V1",
        "question": question,
        "answer": answer,
        "retrieved_chunk_ids": [
            item["chunk_id"]
            for item in evidence
        ],
        "evidence": evidence,
        "latency_ms": latency_ms
    }


def run_v2(
    question,
    records,
    top_k=5,
    max_total=8
):
    start_time = time.perf_counter()

    initial_results = retrieve_v1(
        question=question,
        records=records,
        top_k=top_k
    )

    chunk_index = make_chunk_index(records)

    evidence = expand_references(
        search_results=initial_results,
        chunk_index=chunk_index,
        max_total=max_total
    )

    answer = generate_answer(
        question=question,
        evidence=evidence
    )

    latency_ms = round(
        (time.perf_counter() - start_time)
        * 1000,
        2
    )

    return {
        "version": "V2",
        "question": question,
        "answer": answer,
        "retrieved_chunk_ids": [
            item["chunk_id"]
            for item in evidence
        ],
        "evidence": evidence,
        "latency_ms": latency_ms
    }


def run_pipeline(
    question,
    version,
    records,
    top_k=5
):
    version = version.upper()

    if version == "V0":
        return run_v0(question)

    if version == "V1":
        return run_v1(
            question=question,
            records=records,
            top_k=top_k
        )

    if version == "V2":
        return run_v2(
            question=question,
            records=records,
            top_k=top_k
        )

    raise ValueError(
        "version은 V0, V1, V2 중 하나여야 합니다."
    )


def main():
    parser = argparse.ArgumentParser(
        description="AI기본법 V0~V2 RAG 파이프라인"
    )

    parser.add_argument(
        "--build",
        action="store_true",
        help="법령 조문의 임베딩을 생성합니다."
    )

    parser.add_argument(
        "--version",
        default="V1",
        choices=["V0", "V1", "V2"],
        help="실행할 파이프라인 버전"
    )

    parser.add_argument(
        "--question",
        help="사용자 질문"
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="검색할 조문 개수"
    )

    args = parser.parse_args()

    if args.build:
        build_vector_store()
        return

    if not args.question:
        raise ValueError(
            "--question을 입력해야 합니다."
        )

    records = load_vector_store()

    result = run_pipeline(
        question=args.question,
        version=args.version,
        records=records,
        top_k=args.top_k
    )

    print(json.dumps(
        result,
        ensure_ascii=False,
        indent=2
    ))


if __name__ == "__main__":
    main()