async function postJson(path, payload) {
  let response;

  try {
    response = await fetch(path, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new Error(
      "FastAPI 서버에 연결할 수 없습니다."
    );
  }

  let data = {};

  try {
    data = await response.json();
  } catch {
    throw new Error(
      "서버 응답을 읽을 수 없습니다."
    );
  }

  if (!response.ok) {
    throw new Error(
      data.detail || `API 오류: ${response.status}`
    );
  }

  return data;
}


export function startAssessment(
  systemName,
  systemDescription,
) {
  return postJson(
    "/api/assessment/start",
    {
      system_name: systemName,
      system_description: systemDescription,
    },
  );
}


export function continueAssessment(
  sessionId,
  answer,
) {
  return postJson(
    "/api/assessment/continue",
    {
      session_id: sessionId,
      answer,
    },
  );
}


export function finalizeAssessment(
  sessionId,
) {
  return postJson(
    "/api/assessment/finalize",
    {
      session_id: sessionId,
    },
  );
}