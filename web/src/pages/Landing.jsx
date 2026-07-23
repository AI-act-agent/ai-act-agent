import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AnswerCard from "../components/AnswerCard.jsx";

const PREVIEW_RESULT = {
  verdict: "⚠ 고영향 AI — 해당 가능성 높음",
  level: "high",
  answer:
    "의료 예약 시스템은 AI기본법 제2조 제4호에 따른 '의료 서비스 영역' 고영향 AI에 해당합니다.\n\n판단 근거 조항: 제2조 제4호 가목, 시행령 제24조 제1항 제1호",
  citations: [
    { article: "제2조 제4호" },
    { article: "시행령 제24조" },
    { article: "판단가이드라인 1.2.1" },
  ],
};

export default function Landing() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");

  const submit = (e) => {
    e.preventDefault();
    const question = q.trim();
    if (question) navigate(`/ask?q=${encodeURIComponent(question)}`);
  };

  return (
    <>
      {/* Navbar */}
      <header className="nav">
        <div className="wrap nav-inner">
          <Link className="brand" to="/">
            조문조문<span className="dot" />
          </Link>
          <nav className="nav-links">
            <a href="#how">서비스 소개</a>
            <a href="#features">주요 기능</a>
            <a href="#how">활용 사례</a>
            <a href="#footer">문의</a>
          </nav>
          <Link className="btn btn-primary btn-sm" to="/ask">
            무료로 시작하기
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="hero">
        <div className="blob blob-1" />
        <div className="wrap hero-grid">
          <div className="hero-copy">
            <span className="badge">AI기본법 시행 · 2026.1.22</span>
            <h1>
              AI기본법,
              <br />
              직접 물어보세요
            </h1>
            <p className="lead">
              단순히 체크리스트가 아닙니다.
              <br />
              법 조항과 가이드라인을 근거로 정확한 답변을 드립니다.
            </p>
            <div className="hero-actions">
              <Link className="btn btn-primary" to="/ask">
                지금 질문하기
              </Link>
              <a className="btn btn-ghost" href="#features">
                기능 살펴보기 →
              </a>
            </div>
          </div>

          {/* Chat preview */}
          <div className="chat-card">
            <div className="chat-card-head">
              조문조문 AI <span className="live-dot" />
            </div>
            <div className="chat-card-body">
              <div className="bubble-user">
                우리 서비스가 고영향 AI에 해당하나요? (의료 예약 시스템, B2C)
              </div>
              <AnswerCard result={PREVIEW_RESULT} />
              <form className="chat-input" onSubmit={submit}>
                <input
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  type="text"
                  placeholder="AI기본법에 대해 무엇이든 물어보세요..."
                  aria-label="질문 입력"
                />
                <button className="send" type="submit" aria-label="전송">
                  ↑
                </button>
              </form>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="band">
        <div className="wrap stats">
          <div className="stat">
            <div className="num">6종</div>
            <div className="cap">반영 법·가이드라인 문서</div>
          </div>
          <div className="stat">
            <div className="num">2단계</div>
            <div className="cap">고영향 AI 판별 프로세스</div>
          </div>
          <div className="stat">
            <div className="num">실시간</div>
            <div className="cap">조항 기반 근거 답변</div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="sec-pad">
        <div className="wrap">
          <p className="eyebrow">HOW IT WORKS</p>
          <h2 className="sec-title">3단계로 끝나는 AI기본법 검토</h2>
          <div className="steps">
            <div className="step">
              <div className="idx">01</div>
              <h3>질문 입력</h3>
              <p>서비스나 AI 시스템에 대해 자유롭게 물어보세요.</p>
            </div>
            <div className="step">
              <div className="idx">02</div>
              <h3>자동 판별 · 분석</h3>
              <p>2단계 필터링으로 고영향 AI 해당 여부를 즉시 판단하고 관련 법 조항을 탐색합니다.</p>
            </div>
            <div className="step">
              <div className="idx">03</div>
              <h3>근거 기반 답변</h3>
              <p>법 조항·가이드라인을 직접 인용한 정확한 답변과 사업자 조치사항을 한 번에 확인하세요.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="band sec-pad">
        <div className="wrap">
          <p className="eyebrow">FEATURES</p>
          <h2 className="sec-title">조문조문이 다른 이유</h2>
          <div className="feats">
            <div className="feat">
              <div className="icon">⚖️</div>
              <span className="tag tag-blue">핵심 기능</span>
              <h3>고영향 AI 판별</h3>
              <p>
                AI기본법 시행령 제24조 기반 2단계 필터링으로 정확하게 판별. 도메인·기본권·영향·비가역성을
                자동으로 체크합니다.
              </p>
            </div>
            <div className="feat">
              <div className="icon">📋</div>
              <span className="tag tag-green">투명성</span>
              <h3>조항 근거 제시</h3>
              <p>
                답변마다 해당 법 조항·가이드라인을 직접 인용. 근거 없는 말이 아닌 정확한 법률 출처와 함께
                판단 결과를 확인하세요.
              </p>
            </div>
            <div className="feat">
              <div className="icon">📌</div>
              <span className="tag tag-amber">실무 적용</span>
              <h3>사업자 책무 안내</h3>
              <p>고영향 AI로 판단 시 위험관리·설명·이용자보호 등 5개 책무 조치사항을 즉시 안내합니다.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cta">
        <div className="blob blob-2" />
        <div className="wrap">
          <h2>지금 바로 물어보세요</h2>
          <p>로그인 없이 즉시 사용 가능 · AI기본법 전문 QA 에이전트</p>
          <Link className="btn btn-primary" to="/ask">
            무료로 시작하기 →
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer id="footer" className="footer">
        <div className="wrap footer-inner">
          <div>
            <div className="fbrand">조문조문</div>
            <div className="fdesc">
              AI기본법 전문 QA 에이전트
              <br />
              홍익대학교 산업·데이터공학과 졸업 프로젝트
            </div>
          </div>
          <nav className="footer-links">
            <a href="#">이용약관</a>
            <a href="#">개인정보처리방침</a>
            <a href="https://github.com/AI-act-agent" target="_blank" rel="noopener noreferrer">
              GitHub
            </a>
          </nav>
        </div>
        <div className="wrap copy">© 2026 조문조문. Built on AI기본법 가이드라인 7종.</div>
      </footer>
    </>
  );
}
