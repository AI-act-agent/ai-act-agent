import { useState } from "react";
import { Link } from "react-router-dom";

import AnswerCard from "../components/AnswerCard.jsx";
import {
  continueAssessment,
  finalizeAssessment,
  startAssessment,
} from "../lib/assessment.js";


const BOOLEAN_FIELDS = new Set([
  "output_used_in_score",
  "automatic_decision",
  "human_final_decision",
  "human_can_override",
  "provided_to_third_party",
]);

const controlStyle = {
  width: "100%",
  padding: "14px 16px",
  border: "1px solid #d0d5dd",
  borderRadius: 10,
  font: "inherit",
  boxSizing: "border-box",
};

const labelStyle = {
  display: "block",
  marginBottom: 8,
  fontWeight: 700,
};


function inferLevel(verdict = "") {
  if (verdict.includes("높음")) {
    return "high";
  }

  if (verdict.includes("낮음")) {
    return "low";
  }

  return "hold";
}


function buildAnswerCardResult(workflow) {
  const result = workflow.assessment_result;

  return {
    verdict: result.verdict,
    level: inferLevel(result.verdict),
    answer: result.summary,
    confidence:
      workflow.status === "completed"
        ? "법령·가이드라인 근거 연결 완료"
        : "사전 판정",
    citations: result.citations || [],
  };
}


export default function Assessment() {
  const [systemName, setSystemName] = useState("");
  const [systemDescription, setSystemDescription] =
    useState("");
  const [workflow, setWorkflow] = useState(null);
  const [answer, setAnswer] = useState("");
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");


  const handleStart = async (event) => {
    event.preventDefault();

    if (
      !systemName.trim()
      || !systemDescription.trim()
    ) {
      setError(
        "AI 시스템 이름과 설명을 입력해 주세요."
      );
      return;
    }

    setLoading(true);
    setError("");

    try {
      const result = await startAssessment(
        systemName,
        systemDescription,
      );

      setWorkflow(result);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };


  const handleContinue = async (event) => {
    event.preventDefault();

    if (!answer.trim()) {
      setError("추가 질문에 답변해 주세요.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const currentQuestion =
        workflow.next_question;

      const result = await continueAssessment(
        workflow.session_id,
        answer,
      );

      setHistory((previous) => [
        ...previous,
        {
          question: currentQuestion,
          answer,
        },
      ]);
      setAnswer("");
      setWorkflow(result);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };


  const handleFinalize = async () => {
    setLoading(true);
    setError("");

    try {
      const result = await finalizeAssessment(
        workflow.session_id
      );

      setWorkflow(result);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };


  const handleDownload = () => {
    const report = workflow.report || "";
    const blob = new Blob(
      [report],
      {
        type: "text/markdown;charset=utf-8",
      },
    );
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const safeName = (
      workflow.assessment_input.system_name
      || "ai_system"
    ).replace(/[^\w가-힣-]+/g, "_");

    link.href = url;
    link.download = (
      `${safeName}_고영향_AI_사전검토.md`
    );
    link.click();
    URL.revokeObjectURL(url);
  };


  const handleReset = () => {
    setSystemName("");
    setSystemDescription("");
    setWorkflow(null);
    setAnswer("");
    setHistory([]);
    setError("");
  };


  return (
    <div className="ask-page">
      <header className="ask-header">
        <div className="wrap nav-inner">
          <Link className="brand" to="/">
            조문조문<span className="dot" />
          </Link>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 16,
            }}
          >
            <Link
              className="btn btn-ghost btn-sm"
              to="/ask"
            >
              법령 Q&amp;A
            </Link>

            <Link
              className="btn btn-ghost btn-sm"
              to="/"
            >
              ← 홈으로
            </Link>
          </div>
        </div>
      </header>

      <main
        style={{
          width: "min(880px, calc(100% - 32px))",
          margin: "0 auto",
          padding: "48px 0 80px",
        }}
      >
        <h1>고영향 AI 사전 검토</h1>

        <p
          style={{
            color: "#667085",
            lineHeight: 1.7,
            marginBottom: 28,
          }}
        >
          AI 시스템의 활용 방식과 의사결정 구조를
          입력하면 추가 질문을 거쳐 법령·가이드라인
          근거가 포함된 사전 검토 보고서를 생성합니다.
        </p>

        {error && (
          <div
            className="answer-card"
            style={{
              borderColor: "#f04438",
              color: "#b42318",
              marginBottom: 20,
            }}
          >
            {error}
          </div>
        )}

        {!workflow && (
          <form
            className="answer-card"
            onSubmit={handleStart}
          >
            <div style={{ marginBottom: 20 }}>
              <label
                htmlFor="system-name"
                style={labelStyle}
              >
                AI 시스템 이름
              </label>

              <input
                id="system-name"
                value={systemName}
                onChange={(event) =>
                  setSystemName(event.target.value)
                }
                placeholder="예: 자동 채용 AI"
                style={controlStyle}
              />
            </div>

            <div style={{ marginBottom: 24 }}>
              <label
                htmlFor="system-description"
                style={labelStyle}
              >
                AI 시스템 설명
              </label>

              <textarea
                id="system-description"
                value={systemDescription}
                onChange={(event) =>
                  setSystemDescription(
                    event.target.value
                  )
                }
                placeholder={
                  "AI의 역할, 점수 반영 여부, "
                  + "자동 결정 여부, 사람의 검토 절차, "
                  + "외부 제공 여부를 작성해 주세요."
                }
                rows={8}
                style={{
                  ...controlStyle,
                  resize: "vertical",
                  lineHeight: 1.6,
                }}
              />
            </div>

            <button
              className="btn btn-primary"
              type="submit"
              disabled={loading}
            >
              {loading
                ? "입력 내용을 분석하고 있습니다..."
                : "사전 검토 시작"}
            </button>
          </form>
        )}

        {workflow && history.length > 0 && (
          <div
            className="answer-card"
            style={{ marginBottom: 20 }}
          >
            <h3>추가 확인 내용</h3>

            {history.map((item, index) => (
              <div
                key={`${item.question}-${index}`}
                style={{
                  padding: "12px 0",
                  borderBottom:
                    "1px solid #eaecf0",
                }}
              >
                <strong>Q. {item.question}</strong>
                <div style={{ marginTop: 6 }}>
                  A. {item.answer}
                </div>
              </div>
            ))}
          </div>
        )}

        {workflow?.status === "needs_input" && (
          <form
            className="answer-card"
            onSubmit={handleContinue}
          >
            <div
              style={{
                color: "#667085",
                marginBottom: 10,
              }}
            >
              추가 정보 확인
            </div>

            <h3>{workflow.next_question}</h3>

            {BOOLEAN_FIELDS.has(
              workflow.next_field
            ) ? (
              <div
                style={{
                  display: "flex",
                  gap: 24,
                  margin: "24px 0",
                }}
              >
                {["예", "아니오"].map((value) => (
                  <label key={value}>
                    <input
                      type="radio"
                      name="followup-answer"
                      value={value}
                      checked={answer === value}
                      onChange={(event) =>
                        setAnswer(event.target.value)
                      }
                    />{" "}
                    {value}
                  </label>
                ))}
              </div>
            ) : (
              <textarea
                value={answer}
                onChange={(event) =>
                  setAnswer(event.target.value)
                }
                rows={5}
                style={{
                  ...controlStyle,
                  resize: "vertical",
                  margin: "16px 0 24px",
                }}
              />
            )}

            <button
              className="btn btn-primary"
              type="submit"
              disabled={loading}
            >
              {loading ? "처리 중..." : "다음"}
            </button>
          </form>
        )}

        {workflow?.status
          === "ready_to_finalize" && (
          <>
            <AnswerCard
              result={buildAnswerCardResult(workflow)}
            />

            <div style={{ marginTop: 20 }}>
              <button
                className="btn btn-primary"
                type="button"
                disabled={loading}
                onClick={handleFinalize}
              >
                {loading
                  ? "법령 근거를 검색하고 있습니다..."
                  : "근거 연결 및 보고서 생성"}
              </button>
            </div>
          </>
        )}

        {workflow?.status === "completed" && (
          <>
            <AnswerCard
              result={buildAnswerCardResult(workflow)}
            />

            <div
              className="answer-card"
              style={{ marginTop: 20 }}
            >
              <details>
                <summary
                  style={{
                    cursor: "pointer",
                    fontWeight: 700,
                  }}
                >
                  전체 보고서 보기
                </summary>

                <pre
                  style={{
                    marginTop: 20,
                    whiteSpace: "pre-wrap",
                    wordBreak: "keep-all",
                    lineHeight: 1.7,
                    fontFamily: "inherit",
                  }}
                >
                  {workflow.report}
                </pre>
              </details>
            </div>

            <div
              style={{
                display: "flex",
                gap: 12,
                marginTop: 20,
                flexWrap: "wrap",
              }}
            >
              <button
                className="btn btn-primary"
                type="button"
                onClick={handleDownload}
              >
                Markdown 보고서 다운로드
              </button>

              <button
                className="btn btn-ghost"
                type="button"
                onClick={handleReset}
              >
                새로운 시스템 검토
              </button>
            </div>
          </>
        )}

        {workflow
          && workflow.status !== "completed" && (
          <div style={{ marginTop: 20 }}>
            <button
              className="btn btn-ghost"
              type="button"
              onClick={handleReset}
            >
              처음부터 다시 입력
            </button>
          </div>
        )}

        <p
          className="disclaimer"
          style={{ marginTop: 30 }}
        >
          본 결과는 사전 검토 자료이며 정부의 공식
          확인이나 법률 자문을 대신하지 않습니다.
        </p>
      </main>
    </div>
  );
}