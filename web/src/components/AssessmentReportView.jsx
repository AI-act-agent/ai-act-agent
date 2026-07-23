const INPUT_FIELDS = [
  "usage_domain",
  "ai_role",
  "decision_consequence",
  "output_used_in_score",
  "automatic_decision",
  "human_review_process",
  "human_final_decision",
  "human_can_override",
  "provided_to_third_party",
];


function formatBoolean(value) {
  if (value === true) {
    return "예";
  }

  if (value === false) {
    return "아니오";
  }

  return "확인 필요";
}


function verdictTone(verdict = "") {
  if (verdict.includes("높음")) {
    return "danger";
  }

  if (verdict.includes("낮음")) {
    return "safe";
  }

  return "warning";
}


function SourceBox({ citation }) {
  if (!citation) {
    return (
      <div className="report-source">
        연결된 세부 근거가 없습니다.
      </div>
    );
  }

  const label = (
    citation.article
    || citation.article_id
    || "관련 근거"
  );

  return (
    <div className="report-source">
      <strong>근거</strong>
      <div>{label}</div>

      <details>
        <summary>근거 원문 보기</summary>
        <p>{citation.text}</p>
        <small>출처: {citation.source_url}</small>
      </details>
    </div>
  );
}


export default function AssessmentReportView({
  workflow,
  onDownload,
  onReset,
}) {
  const input = workflow.assessment_input;
  const result = workflow.assessment_result;
  const citations = result.citations || [];
  const criteria = result.matched_criteria || [];
  const recommendations = (
    result.recommendations || []
  );

  const completedInputCount = INPUT_FIELDS.filter(
    (fieldName) => (
      input[fieldName] !== null
      && input[fieldName] !== undefined
      && input[fieldName] !== ""
    ),
  ).length;

  const hasStrongHumanReview = (
    input.human_final_decision === true
    && input.human_can_override === true
  );

  const hasWeakHumanReview = (
    input.human_final_decision === false
    || input.human_can_override === false
  );

  const humanReviewStatus = (
    hasStrongHumanReview
      ? "실질적 검토"
      : hasWeakHumanReview
        ? "관리·감독 미흡"
        : "확인 필요"
  );

  const findings = [
    {
      title: "법정 활용 영역",
      status: (
        result.domain_match === true
          ? "해당"
          : result.domain_match === false
            ? "비해당"
            : "확인 필요"
      ),
      tone: (
        result.domain_match === true
          ? "danger"
          : "warning"
      ),
      summary: (
        `${input.usage_domain || "미확인 영역"}에서 `
        + "AI 시스템이 활용됩니다."
      ),
      detail: (
        criteria.find((item) =>
          item.includes("법정 활용 영역")
        )
        || result.summary
      ),
      citation: citations[0],
    },
    {
      title: "AI의 의사결정 관여",
      status: (
        result.significant_impact === true
          ? "중대한 영향 가능"
          : result.significant_impact === false
            ? "영향 가능성 낮음"
            : "확인 필요"
      ),
      tone: (
        result.significant_impact === true
          ? "danger"
          : "warning"
      ),
      summary: (
        `${input.ai_role || "AI 역할 미확인"} / `
        + `${input.decision_consequence
          || "의사결정 결과 미확인"}`
      ),
      detail: (
        `점수·평가 반영: ${
          formatBoolean(input.output_used_in_score)
        }, 자동 결정: ${
          formatBoolean(input.automatic_decision)
        }`
      ),
      citation: citations[1] || citations[0],
    },
    {
      title: "사람의 관리·감독",
      status: humanReviewStatus,
      tone: (
        hasStrongHumanReview
          ? "safe"
          : hasWeakHumanReview
            ? "danger"
            : "warning"
      ),
      summary: (
        input.human_review_process
        || "사람의 검토 절차가 확인되지 않았습니다."
      ),
      detail: (
        `사람의 최종 결정: ${
          formatBoolean(input.human_final_decision)
        }, AI 결과 변경 가능: ${
          formatBoolean(input.human_can_override)
        }`
      ),
      citation: citations[2] || citations[0],
    },
  ];

  return (
    <article className="assessment-report">
      <div className="report-toolbar report-no-print">
        <strong>AI기본법 사전 검토 보고서</strong>

        <div>
          <button
            className="btn btn-ghost btn-sm"
            type="button"
            onClick={() => window.print()}
          >
            PDF 저장
          </button>

          <button
            className="btn btn-primary btn-sm"
            type="button"
            onClick={onDownload}
          >
            보고서 다운로드
          </button>
        </div>
      </div>

      <section className="report-hero">
        <div>
          <h2>
            {input.system_name} — AI기본법 사전 검토
          </h2>

          <div className="report-meta">
            <span>
              검토일{" "}
              {new Intl.DateTimeFormat(
                "ko-KR"
              ).format(new Date())}
            </span>
            <span>
              활용 분야 {input.usage_domain}
            </span>
            <span>
              사업자 지위 {result.operator_status}
            </span>
          </div>
        </div>

        <span
          className={
            `report-verdict ${
              verdictTone(result.verdict)
            }`
          }
        >
          {result.verdict}
        </span>
      </section>

      <section className="report-section">
        <h3>요약</h3>

        <div className="report-metrics">
          <div className="report-metric">
            <span>입력 확인</span>
            <strong>
              {completedInputCount}/{INPUT_FIELDS.length}
            </strong>
          </div>

          <div className="report-metric">
            <span>사전 판정</span>
            <strong>{result.verdict}</strong>
          </div>

          <div className="report-metric">
            <span>판단 항목</span>
            <strong>{criteria.length}개</strong>
          </div>

          <div className="report-metric">
            <span>근거 문서</span>
            <strong>{citations.length}건</strong>
          </div>
        </div>

        <div className="report-summary">
          {result.summary}
        </div>
      </section>

      <section className="report-section">
        <h3>위험·법적 쟁점 및 근거</h3>

        <div className="report-findings">
          {findings.map((finding) => (
            <div
              className={
                `report-finding ${finding.tone}`
              }
              key={finding.title}
            >
              <div className="report-finding-head">
                <h4>{finding.title}</h4>
                <span>{finding.status}</span>
              </div>

              <p>{finding.summary}</p>

              <div className="report-analysis">
                <strong>사전 분석</strong>
                <p>{finding.detail}</p>
              </div>

              <SourceBox
                citation={finding.citation}
              />
            </div>
          ))}
        </div>
      </section>

      <section className="report-section">
        <h3>보완 제안</h3>

        <div className="report-actions">
          {recommendations.length > 0 ? (
            recommendations.map(
              (recommendation, index) => (
                <div
                  className="report-action"
                  key={recommendation}
                >
                  <span className="report-priority">
                    우선 {index + 1}
                  </span>
                  <strong>{recommendation}</strong>
                </div>
              ),
            )
          ) : (
            <div className="report-action">
              추가 권고사항이 없습니다.
            </div>
          )}
        </div>
      </section>

      <section className="report-limit">
        본 보고서는 입력 정보와 제공된 법령·가이드라인을
        기반으로 생성된 사전 검토 자료이며, 정부의 공식
        확인이나 법률 자문을 대신하지 않습니다.
      </section>

      <div className="report-no-print report-bottom-actions">
        <button
          className="btn btn-ghost"
          type="button"
          onClick={onReset}
        >
          새로운 시스템 검토
        </button>
      </div>
    </article>
  );
}