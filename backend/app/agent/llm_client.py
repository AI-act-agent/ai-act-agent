import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

MODEL_NAME = "gemini-3.5-flash"


def call_gemini(
    system_prompt: str,
    user_prompt: str,
) -> str:
    """Gemini에 프롬프트를 전달하고 텍스트 응답을 반환한다."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY가 설정되지 않았습니다.")

    client = genai.Client(api_key=api_key)

    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=f"{system_prompt}\n\n{user_prompt}",
    )

    if not interaction.output_text:
        raise RuntimeError("Gemini가 응답을 반환하지 않았습니다.")

    return interaction.output_text.strip()