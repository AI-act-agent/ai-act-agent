// 답변 카드 (히어로 미리보기 + 질문화면 공용)
const badgeClass = (level) =>
  level === "high" ? "judge-high" : level === "low" ? "judge-low" : "judge-hold";

function Chip({ c }) {
  const label = c.article || c.label || "근거";
  const isUrl = /^https?:\/\//.test(c.source_url || "");
  return isUrl ? (
    <a className="chip" href={c.source_url} target="_blank" rel="noopener noreferrer">
      {label}
    </a>
  ) : (
    <span className="chip">{label}</span>
  );
}

export default function AnswerCard({ result, showName = false }) {
  const cites = result.citations || [];
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
    </div>
  );
}
