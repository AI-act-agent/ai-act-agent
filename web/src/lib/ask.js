// 질문 → 답변 로직. 백엔드(/api/ask)의 실제 에이전트 답변만 사용한다.
// (데모 답변 폴백 없음 — 실패는 실패로 표시해야 진짜 답변과 구분된다.)

// 에이전트는 계획→검색→생성→검증을 거치므로 40초 이상 걸리는 경우가 있다.
const TIMEOUT_MS = 180_000;

export function inferLevel(verdict = "") {
  if (/높음|해당|고영향/.test(verdict) && !/안 함|아님|낮음/.test(verdict)) return "high";
  if (/낮음|해당 안|아님|보류/.test(verdict)) return "low";
  return "hold";
}

export async function askQuestion(question) {
  try {
    return await callApi(question);
  } catch (e) {
    return errorAnswer(e);
  }
}

async function callApi(question) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  let res;
  try {
    res = await fetch("/api/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // ngrok 무료 터널이 끼워 넣는 경고 페이지(HTML) 우회 — 로컬에서는 무시된다
        "ngrok-skip-browser-warning": "true",
      },
      body: JSON.stringify({ question }),
      signal: controller.signal,
    });
  } catch (e) {
    if (e.name === "AbortError") throw new Error("답변 생성이 너무 오래 걸려 중단했습니다.");
    throw new Error("서버에 연결하지 못했습니다. API 서버가 실행 중인지 확인해 주세요.");
  } finally {
    clearTimeout(timer);
  }

  if (!res.ok) {
    const detail = await res
      .json()
      .then((d) => d.detail)
      .catch(() => null);
    throw new Error(detail || `서버 오류 (HTTP ${res.status})`);
  }

  const data = await res.json();
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

function errorAnswer(e) {
  return {
    verdict: "⚠ 답변을 가져오지 못했습니다",
    level: "low",
    answer:
      `${e.message}\n\n` +
      "서버 실행:\n" +
      "  pip install -r requirements-api.txt\n" +
      "  uvicorn backend.app.api.server:app --reload --port 8000",
    confidence: "",
    citations: [],
    steps: [],
    isError: true,
  };
}
