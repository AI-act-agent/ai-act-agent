import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors


load_dotenv()

MODEL_NAME = os.getenv(
    "GEMINI_GENERATION_MODEL",
    "gemini-3.1-flash-lite",
)

MAX_RETRIES = 3

RETRYABLE_CODES = {
    429,
    500,
    502,
    503,
    504,
}


def call_gemini(
    system_prompt: str,
    user_prompt: str,
) -> str:
    """Gemini를 호출하고 일시적 오류 발생 시 재시도한다."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY가 설정되지 않았습니다."
        )

    client = genai.Client(api_key=api_key)

    prompt = (
        f"{system_prompt}\n\n"
        f"{user_prompt}"
    )

    try:
        for retry_count in range(MAX_RETRIES + 1):
            try:
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=prompt,
                )

                if not response.text:
                    raise RuntimeError(
                        "Gemini가 응답을 반환하지 않았습니다."
                    )

                return response.text.strip()

            except errors.APIError as error:
                is_last_attempt = (
                    retry_count >= MAX_RETRIES
                )

                if (
                    error.code not in RETRYABLE_CODES
                    or is_last_attempt
                ):
                    raise

                if error.code == 429:
                    wait_seconds = 60
                else:
                    wait_seconds = 2 ** retry_count

                print(
                    f"Gemini 일시 오류({error.code}): "
                    f"{wait_seconds}초 후 재시도합니다."
                )

                time.sleep(wait_seconds)

    finally:
        client.close()