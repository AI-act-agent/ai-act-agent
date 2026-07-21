from functools import lru_cache

import re

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

from backend.app.agent.schemas import Evidence


NLI_MODEL_NAME = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"


@lru_cache(maxsize=1)
def _load_nli_model():
    tokenizer = AutoTokenizer.from_pretrained(NLI_MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        NLI_MODEL_NAME,
        use_safetensors=True,
    )
    model.eval()

    return tokenizer, model

ENTAILMENT_THRESHOLD = 0.5
CONTRADICTION_THRESHOLD = 0.7
MIN_CLAIM_COVERAGE = 0.7


def split_answer_claims(
    answer: str,
) -> list[str]:
    claims = []

    for block in re.split(
        r"\n+",
        answer,
    ):
        cleaned_block = block.strip()

        if not cleaned_block:
            continue

        cleaned_block = re.sub(
            r"^\d+\.\s*[^:]{1,40}:\s*",
            "",
            cleaned_block,
        )

        sentences = re.split(
            r"(?<=[.!?])\s+",
            cleaned_block,
        )

        for sentence in sentences:
            cleaned_sentence = re.sub(
                r"\((?:법|시행령|근거)[^)]*\)",
                "",
                sentence,
            ).strip()

            if len(cleaned_sentence) < 10:
                continue

            if cleaned_sentence.endswith(
                "다음과 같습니다."
            ):
                continue

            claims.append(cleaned_sentence)

    if not claims and answer.strip():
        claims.append(answer.strip())

    return claims

def get_label_id(
    model,
    target_label: str,
) -> int:
    """NLI 모델에서 원하는 판정 라벨의 번호를 찾는다."""

    for label_id, label_name in model.config.id2label.items():
        if label_name.lower() == target_label.lower():
            return int(label_id)

    raise RuntimeError(
        f"NLI 모델에서 {target_label} 라벨을 찾지 못했습니다."
    )

def score_claim_against_evidence(
    claim: str,
    evidence: list[Evidence],
) -> tuple[float, float]:
    """주장 하나의 지지 및 모순 점수를 계산한다."""

    if not evidence:
        return 0.0, 0.0

    tokenizer, model = _load_nli_model()

    premises = [
        f"{item.article}: {item.text}"
        for item in evidence
    ]
    hypotheses = [
        claim
        for _ in premises
    ]

    model_inputs = tokenizer(
        premises,
        hypotheses,
        padding=True,
        truncation="only_first",
        max_length=512,
        return_tensors="pt",
    )

    with torch.inference_mode():
        logits = model(**model_inputs).logits

    probabilities = torch.softmax(
        logits,
        dim=-1,
    )

    entailment_id = get_label_id(
        model,
        "entailment",
    )
    contradiction_id = get_label_id(
        model,
        "contradiction",
    )

    entailment_score = probabilities[
        :,
        entailment_id,
    ].max().item()

    contradiction_score = probabilities[
        :,
        contradiction_id,
    ].max().item()

    return entailment_score, contradiction_score

def evaluate_claim(
    claim: str,
    evidence: list[Evidence],
) -> dict:
    """주장 하나를 entailment, contradiction, neutral로 판정한다."""

    entailment_score, contradiction_score = (
        score_claim_against_evidence(
            claim=claim,
            evidence=evidence,
        )
    )

    if (
        entailment_score >= ENTAILMENT_THRESHOLD
        and entailment_score >= contradiction_score
    ):
        label = "entailment"

    elif (
        contradiction_score
        >= CONTRADICTION_THRESHOLD
    ):
        label = "contradiction"

    else:
        label = "neutral"

    return {
        "claim": claim,
        "label": label,
        "entailment_score": entailment_score,
        "contradiction_score": contradiction_score,
    }

def grounding_details(
    answer: str,
    evidence: list[Evidence],
) -> dict:
    """답변을 주장 단위로 검사하고 상세 결과를 반환한다."""

    if not answer.strip() or not evidence:
        return {
            "label": "neutral",
            "coverage": 0.0,
            "claims": [],
        }

    claims = split_answer_claims(answer)

    claim_results = [
        evaluate_claim(
            claim=claim,
            evidence=evidence,
        )
        for claim in claims
    ]

    entailed_count = sum(
        result["label"] == "entailment"
        for result in claim_results
    )

    has_contradiction = any(
        result["label"] == "contradiction"
        for result in claim_results
    )

    coverage = (
        entailed_count / len(claim_results)
        if claim_results
        else 0.0
    )

    if has_contradiction:
        label = "contradiction"

    elif coverage >= MIN_CLAIM_COVERAGE:
        label = "entailment"

    else:
        label = "neutral"

    return {
        "label": label,
        "coverage": coverage,
        "claims": claim_results,
    }

def grounding_check(
    answer: str,
    evidence: list[Evidence],
) -> str:
    """답변의 최종 Grounding 판정만 반환한다."""

    result = grounding_details(
        answer=answer,
        evidence=evidence,
    )

    return result["label"]