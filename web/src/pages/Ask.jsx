import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import AnswerCard from "../components/AnswerCard.jsx";
import { askQuestion } from "../lib/ask.js";

const SAMPLES = [
  "우리 서비스가 고영향 AI에 해당하나요? (의료 예약 시스템, B2C)",
  "고영향 AI 사업자의 책무는 무엇인가요?",
  "이용자 보호 방안은 어떻게 수립해야 하나요?",
  "채용에 쓰는 AI도 고영향 AI인가요?",
];

export default function Ask() {
  const [params] = useSearchParams();
  const [messages, setMessages] = useState([]); // {role:'user'|'bot', text?, result?}
  const [typing, setTyping] = useState(false);
  const [input, setInput] = useState("");
  const [started, setStarted] = useState(false);
  const endRef = useRef(null);
  const inputRef = useRef(null);
  const askedInitial = useRef(false);

  const scrollToEnd = () =>
    requestAnimationFrame(() =>
      endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" })
    );

  const ask = async (question) => {
    if (!question.trim()) return;
    setStarted(true);
    setInput("");
    setMessages((m) => [...m, { role: "user", text: question }]);
    setTyping(true);
    scrollToEnd();

    const result = await askQuestion(question);
    setTyping(false);
    setMessages((m) => [...m, { role: "bot", result }]);
    scrollToEnd();
    inputRef.current?.focus();
  };

  // 랜딩에서 넘어온 ?q= 자동 실행 (한 번만)
  useEffect(() => {
    const q = (params.get("q") || "").trim();
    if (q && !askedInitial.current) {
      askedInitial.current = true;
      ask(q);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    scrollToEnd();
  }, [messages, typing]);

  return (
    <div className="ask-page">
      <header className="ask-header">
        <div className="wrap nav-inner">
          <Link className="brand" to="/">
            조문조문<span className="dot" />
          </Link>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <span className="bot-name" style={{ margin: 0 }}>
              조문조문 AI <span className="live-dot" />
            </span>
            <Link className="btn btn-ghost btn-sm" to="/">
              ← 홈으로
            </Link>
          </div>
        </div>
      </header>

      <main className="ask-main">
        {!started && (
          <div className="ask-intro">
            <h1>무엇이든 물어보세요</h1>
            <p>AI기본법 조항과 가이드라인을 근거로 답변해 드립니다.</p>
            <div className="samples">
              {SAMPLES.map((s) => (
                <button key={s} className="sample-chip" onClick={() => ask(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="thread">
          {messages.map((m, i) =>
            m.role === "user" ? (
              <div key={i} className="msg user">
                <div className="bubble">{m.text}</div>
              </div>
            ) : (
              <div key={i} className="msg bot">
                <div className="bubble">
                  <div className="bot-name">
                    조문조문 AI <span className="live-dot" />
                  </div>
                  <AnswerCard result={m.result} />
                </div>
              </div>
            )
          )}
          {typing && (
            <div className="msg bot">
              <div className="bubble">
                <div className="typing">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        <div className="composer">
          <form
            className="chat-input"
            onSubmit={(e) => {
              e.preventDefault();
              ask(input);
            }}
          >
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              type="text"
              placeholder="AI기본법에 대해 무엇이든 물어보세요..."
              aria-label="질문 입력"
            />
            <button className="send" type="submit" disabled={typing} aria-label="전송">
              ↑
            </button>
          </form>
          <p className="disclaimer">
            답변은 참고용이며 법적 효력이 없습니다. 정확한 판단은 전문가와 상담하세요.
          </p>
        </div>
      </main>
    </div>
  );
}
