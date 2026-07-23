// 질문 → 실제 백엔드 에이전트 답변.
// 데모 답변은 사용하지 않으며 실패를 명확하게 표시한다.

const TIMEOUT_MS = 180_000;


export function inferLevel(verdict = "") {
  if (
    /낮음|비해당|해당 안|아님|안 함/.test(
      verdict
    )
  ) {
    return "low";
  }

  if (
    /높음|고영향/.test(verdict)
  ) {
    return "high";
  }

  return "hold";
}


export async function askQuestion(question) {
  try {
    return await callApi(question);
  } catch (error) {
    return errorAnswer(error);
  }
}


async function callApi(question) {
  const controller = new AbortController();
  const timer = setTimeout(
    () => controller.abort(),
    TIMEOUT_MS,
  );

  let response;

  try {
    response = await fetch(
      "/api/ask",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true",
        },
        body: JSON.stringify({
          question,
        }),
        signal: controller.signal,
      },
    );
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error(
        "답변 생성 시간이 초과되었습니다."
      );
    }

    throw new Error(
      "서버에 연결하지 못했습니다. "
      + "FastAPI 서버 상태를 확인해 주세요."
    );
  } finally {
    clearTimeout(timer);
  }

  if (!response.ok) {
    const detail = await response
      .json()
      .then((data) => data.detail)
      .catch(() => null);

    throw new Error(
      detail
      || `서버 오류 (HTTP ${response.status})`
    );
  }

  const data = await response.json();

  return {
    verdict: data.verdict,
    answer: data.answer,
    confidence: data.confidence,
    citations: data.citations || [],
    steps: data.steps || [],
    retryCount: data.retry_count ?? 0,
    level: inferLevel(data.verdict),
  };
}


function errorAnswer(error) {
  return {
    verdict: "답변을 가져오지 못했습니다",
    level: "hold",
    answer: (
      "실제 에이전트 답변을 불러오지 못했습니다. "
      + error.message
    ),
    confidence: "응답 실패",
    citations: [],
    steps: [],
    isError: true,
  };
}