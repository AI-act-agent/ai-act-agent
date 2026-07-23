/* ============================================================
   조문조문 — 질문 화면 로직
   - 실제 백엔드 API가 있으면 POST {API_BASE}/api/ask 호출
   - 없으면(연결 실패) 내장 데모 응답으로 폴백 → 브라우저에서 바로 동작
   백엔드 AgentResult 구조와 동일한 형태로 답변을 렌더링합니다:
     { verdict, answer, confidence, citations:[{article, source_url}], level }
   ============================================================ */

// 백엔드 API 주소. 로컬 서버를 띄우면 여기에 맞춰 자동 호출됩니다.
// 예: FastAPI를 http://localhost:8000 에 띄운 경우 아래를 그 값으로 바꾸세요.
const API_BASE = ""; // "" 이면 같은 호스트의 /api/ask 로 시도

const thread = document.getElementById("thread");
const form = document.getElementById("form");
const input = document.getElementById("q");
const sendBtn = document.getElementById("send");
const intro = document.getElementById("intro");

const escapeHtml = (s) =>
  s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/* ---------- 렌더링 ---------- */
function addUser(text) {
  const el = document.createElement("div");
  el.className = "msg user";
  el.innerHTML = `<div class="bubble">${escapeHtml(text)}</div>`;
  thread.appendChild(el);
  scroll();
}

function addTyping() {
  const el = document.createElement("div");
  el.className = "msg bot";
  el.id = "typing";
  el.innerHTML = `<div class="bubble"><div class="typing"><span></span><span></span><span></span></div></div>`;
  thread.appendChild(el);
  scroll();
  return el;
}

function badgeClass(level) {
  return level === "high" ? "judge-high" : level === "low" ? "judge-low" : "judge-hold";
}

function addAnswer(result) {
  const typing = document.getElementById("typing");
  if (typing) typing.remove();

  const cites = (result.citations || [])
    .map((c) => {
      const label = escapeHtml(c.article || c.label || "근거");
      // 실제 http(s) 링크일 때만 클릭 가능하게 (파일명·mock 출처는 텍스트로)
      const url = /^https?:\/\//.test(c.source_url || "") ? escapeHtml(c.source_url) : null;
      return url
        ? `<a class="chip" href="${url}" target="_blank" rel="noopener">${label}</a>`
        : `<span class="chip">${label}</span>`;
    })
    .join("");

  const citeBlock = cites
    ? `<div class="answer-divider"></div><div class="cite-row"><span class="cite-label">근거</span>${cites}</div>`
    : "";

  const badge = result.verdict
    ? `<span class="judge-badge ${badgeClass(result.level)}">${escapeHtml(result.verdict)}</span>`
    : "";

  const conf = result.confidence
    ? `<div class="confidence">신뢰도: <b>${escapeHtml(result.confidence)}</b></div>`
    : "";

  const el = document.createElement("div");
  el.className = "msg bot";
  el.innerHTML = `
    <div class="bubble">
      <div class="bot-name">조문조문 AI <span class="live-dot"></span></div>
      <div class="answer-card">
        ${badge}
        <div class="answer-text">${escapeHtml(result.answer || "")}</div>
        ${citeBlock}
        ${conf}
      </div>
    </div>`;
  thread.appendChild(el);
  scroll();
}

function scroll() {
  requestAnimationFrame(() => window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" }));
}

/* ---------- 질문 처리 ---------- */
async function ask(question) {
  if (intro) intro.style.display = "none";
  addUser(question);
  input.value = "";
  sendBtn.disabled = true;
  addTyping();

  let result;
  try {
    result = await callApi(question); // 실제 백엔드
  } catch (e) {
    await wait(700 + Math.random() * 500); // 데모: 생각하는 시간 연출
    result = demoAnswer(question); // 폴백
  }
  addAnswer(result);
  sendBtn.disabled = false;
  input.focus();
}

async function callApi(question) {
  const res = await fetch(`${API_BASE}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error("API error " + res.status);
  const data = await res.json();
  // 백엔드 AgentResult → 화면 형식 매핑
  return {
    verdict: data.verdict,
    answer: data.answer,
    confidence: data.confidence,
    citations: data.citations || [],
    level: inferLevel(data.verdict),
  };
}

function inferLevel(verdict = "") {
  if (/높음|해당|고영향/.test(verdict) && !/안 함|아님|낮음/.test(verdict)) return "high";
  if (/낮음|해당 안|아님/.test(verdict)) return "low";
  return "hold";
}

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

/* ---------- 내장 데모 응답 (백엔드 없이 동작) ---------- */
function demoAnswer(q) {
  const t = q.toLowerCase();

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

  if (/채용|이력서|면접|hr|인사/.test(q) || /채용/.test(t)) {
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

  // 기본: 판단 보류
  return {
    verdict: "🔎 추가 정보 필요",
    level: "hold",
    answer:
      "질문 주신 내용만으로는 정확한 판단이 어렵습니다. 서비스의 사용 도메인(의료·채용·금융 등), 대상(B2C/B2B), 자동화 수준을 알려주시면 고영향 AI 해당 여부를 조항 근거와 함께 판단해 드릴 수 있습니다.",
    confidence: "근거 부족",
    citations: [{ article: "시행령 제24조" }],
  };
}

/* ---------- 이벤트 ---------- */
form.addEventListener("submit", (e) => {
  e.preventDefault();
  const q = input.value.trim();
  if (q) ask(q);
});

document.getElementById("samples")?.addEventListener("click", (e) => {
  const btn = e.target.closest(".sample-chip");
  if (btn) ask(btn.textContent.trim());
});

input.focus();
