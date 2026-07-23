// 답변 카드 (히어로 미리보기 + 질문화면 공용)
const badgeClass = (level) =>
  level === "high" ? "judge-high" : level === "low" ? "judge-low" : "judge-hold";

// 백엔드 citations의 source_url은 URL이 아니라 원문 파일명인 경우가 있다.
const SOURCE_LABELS = {
  "ai_basic_law.txt": "AI기본법",
  "ai_enforcement.txt": "시행령",
  "msit_guideline.txt": "과기정통부 가이드라인",
};

function citeLabel(c) {
  if (c.label) return c.label;
  const source = SOURCE_LABELS[c.source_url] || (c.source_url || "").replace(/\.txt$/, "");
  const article = c.article || "";
  if (source && !/^https?:\/\//.test(source)) {
    return article ? `${source} ${article}` : source;
  }
  return article || "근거";
}

function Chip({ c }) {
  const label = citeLabel(c);
  const tip = (c.text || "").slice(0, 200);
  const isUrl = /^https?:\/\//.test(c.source_url || "");
  return isUrl ? (
    <a className="chip" href={c.source_url} target="_blank" rel="noopener noreferrer" title={tip}>
      {label}
    </a>
  ) : (
    <span className="chip" title={tip}>
      {label}
    </span>
  );
}

export default function AnswerCard({ result, showName = false }) {
  const cites = result.citations || [];
  const steps = result.steps || [];
  return (
    <div className="answer-card">
      {result.verdict && (
        <span className={`judge-badge ${badgeClass(result.level)}`}>{result.verdict}</span>
      )}
      <div className="answer-text">{result.answer}</div>
      {cites.length > 0 && (
        <>
          <div className="answer-divider" />
          <div className="cite-row">
            <span className="cite-label">근거</span>
            {cites.map((c, i) => (
              <Chip key={i} c={c} />
            ))}
          </div>
        </>
      )}
      {result.confidence && (
        <div className="confidence">
          신뢰도: <b>{result.confidence}</b>
        </div>
      )}
      {steps.length > 0 && (
        <details className="steps">
          <summary>에이전트 진행 단계 ({steps.length})</summary>
          <ol>
            {steps.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ol>
        </details>
      )}
    </div>
  );
}
