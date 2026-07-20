from functools import lru_cache

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


def grounding_check(
    answer: str,
    evidence: list[Evidence],
) -> str:

    if not answer.strip():
        return "neutral"

    if not evidence:
        return "neutral"

    premise = "\n".join(
        f"{item.article}: {item.text}"
        for item in evidence
    )

    tokenizer, model = _load_nli_model()

    model_inputs = tokenizer(
        premise,
        answer,
        return_tensors="pt",
        truncation=True,
        max_length=512,
    )

    with torch.inference_mode():
        output = model(**model_inputs)

    prediction_id = output.logits.argmax(
        dim=-1
    ).item()

    label = model.config.id2label[
        prediction_id
    ].lower()

    return label