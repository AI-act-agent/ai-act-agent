// 질문 → 답변 로직. 실제 백엔드(/api/ask) 우선, 실패 시 내장 데모 응답.

export function inferLevel(verdict = "") {
  if (/높음|해당|고영향/.test(verdict) && !/안 함|아님|낮음/.test(verdict)) return "high";
  if (/낮음|해당 안|아님/.test(verdict)) return "low";
  return "hold";
}


export async function askQuestion(question) {
  try {
    return await callApi(question);
  } catch (error) {
    return {
      verdict: "서버 연결 오류",
      level: "hold",
      answer: (
        "실제 에이전트의 답변을 불러오지 못했습니다. "
        + `FastAPI 서버 상태를 확인해 주세요. (${error.message})`
      ),
      confidence: "응답 실패",
      citations: [],
    };
  }
}

async function callApi(question) {
  const res = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error("API error " + res.status);
  const data = await res.json();
  return {
    verdict: data.verdict,
    answer: data.answer,
    confidence: data.confidence,
    citations: data.citations || [],
    level: inferLevel(data.verdict),
  };
}
