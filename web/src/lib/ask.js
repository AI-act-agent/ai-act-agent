// 질문 → 답변 로직. 실제 백엔드(/api/ask) 우선, 실패 시 내장 데모 응답.

export function inferLevel(verdict = "") {
  if (/높음|해당|고영향/.test(verdict) && !/안 함|아님|낮음/.test(verdict)) return "high";
  if (/낮음|해당 안|아님/.test(verdict)) return "low";
  return "hold";
}

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

export async function askQuestion(question) {
  try {
    return await callApi(question);
  } catch {
    await wait(700 + Math.random() * 500); // 데모: 생각하는 시간 연출
    return demoAnswer(question);
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

function demoAnswer(q) {
  if (/의료|병원|예약/.test(q)) {
    return {
      verdict: "⚠ 고영향 AI — 해당 가능성 높음",
      level: "high",
      answer:
        "의료 예약 시스템은 AI기본법 제2조 제4호에 따른 '보건의료 서비스 영역'의 고영향 AI에 해당할 가능성이 높습니다.\n\n환자의 진료 접근에 직접 영향을 주므로, 시행령 제24조의 고영향 판단 기준(도메인·기본권 영향)을 충족합니다. 해당 시 위험관리·설명·이용자보호 등 사업자 책무를 이행해야 합니다.",
      confidence: "근거 충분",
      citations: [
        { article: "제2조 제4호 가목" },
        { article: "시행령 제24조 제1항" },
        { article: "판단가이드라인 1.2.1" },
      ],
    };
  }
  if (/채용|이력서|면접|hr|인사/.test(q)) {
    return {
      verdict: "⚠ 고영향 AI — 해당 가능성 높음",
      level: "high",
      answer:
        "채용·평가에 사용되는 AI는 AI기본법 시행령 제24조에서 정한 '채용 또는 근로관계' 영역에 해당하여 고영향 AI로 분류될 가능성이 높습니다.\n\n지원자의 권리에 중대한 영향을 미치므로, 판별 시 사람의 관리·감독 및 설명 방안 수립이 요구됩니다.",
      confidence: "근거 충분",
      citations: [{ article: "시행령 제24조 제1항" }, { article: "판단가이드라인 1.3" }],
    };
  }
  if (/책무|의무|조치/.test(q)) {
    return {
      verdict: "📋 사업자 책무 안내",
      level: "hold",
      answer:
        "고영향 AI 사업자는 다음 5개 영역의 책무를 이행해야 합니다.\n\n① 위험관리방안 수립·운영\n② 설명 방안 수립·시행\n③ 이용자 보호방안 수립·운영\n④ 사람의 관리·감독\n⑤ 안전성·신뢰성 확보를 위한 문서의 작성·보관",
      confidence: "근거 충분",
      citations: [{ article: "AI기본법 제34조" }, { article: "책무가이드라인 3장" }],
    };
  }
  if (/이용자\s*보호|보호\s*방안/.test(q)) {
    return {
      verdict: "📋 이용자 보호방안",
      level: "hold",
      answer:
        "이용자 보호방안은 개발 단계와 운영 단계로 나누어 수립합니다.\n\n· 개발: 안전·적법한 데이터 관리, 안전한 설계·개발, 지속적 시험·평가\n· 운영: 모니터링 및 대응, 피드백 수렴·적용, 이용자 권리 보호",
      confidence: "근거 충분",
      citations: [{ article: "책무가이드라인 3-1" }, { article: "책무가이드라인 3-2" }],
    };
  }
  return {
    verdict: "🔎 추가 정보 필요",
    level: "hold",
    answer:
      "질문 주신 내용만으로는 정확한 판단이 어렵습니다. 서비스의 사용 도메인(의료·채용·금융 등), 대상(B2C/B2B), 자동화 수준을 알려주시면 고영향 AI 해당 여부를 조항 근거와 함께 판단해 드릴 수 있습니다.",
    confidence: "근거 부족",
    citations: [{ article: "시행령 제24조" }],
  };
}
