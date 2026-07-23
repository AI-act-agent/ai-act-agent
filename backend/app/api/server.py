"""
조문조문 API 서버 (FastAPI)

프론트엔드(frontend/ask.html)의 POST /api/ask 요청을 받아
에이전트(run_agent)를 실행하고 결과를 JSON으로 돌려줍니다.

실행:
    pip install fastapi uvicorn
    # 프로젝트 루트에서
    uvicorn backend.app.api.server:app --reload --port 8000

주의:
    run_agent() 내부의 create_plan()이 Gemini API를 호출하므로
    환경변수 GEMINI_API_KEY 가 필요합니다(planner). 검색(retriever)은
    아직 mock 이라, 실제 RAG 연결 전까지는 데모 수준 응답이 나옵니다.
"""
from dataclasses import asdict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.app.agent.workflow import run_agent

app = FastAPI(title="조문조문 API", version="0.1.0")

# 로컬 개발 중 프론트엔드(file:// 또는 다른 포트)에서의 호출 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str


@app.post("/api/ask")
def ask(req: AskRequest):
    try:
        result = run_agent(req.question)
        return asdict(result)  # verdict, answer, confidence, citations, steps, retry_count
    except Exception as e:  # 키 미설정 등 실패 시 프론트가 데모로 폴백함
        return {
            "verdict": "🔎 서버 처리 실패",
            "answer": f"에이전트 실행 중 오류가 발생했습니다: {e}",
            "confidence": "근거 부족",
            "citations": [],
            "steps": [],
            "retry_count": 0,
        }


@app.get("/health")
def health():
    return {"status": "ok"}


# 정적 프론트엔드 서빙 (http://localhost:8000/ 에서 랜딩페이지 표시)
# frontend/ 를 같은 서버로 서빙하면 /api/ask 가 같은 출처가 되어 CORS 불필요
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
