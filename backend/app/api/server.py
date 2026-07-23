"""
조문조문 API 서버 (FastAPI)

프론트엔드의 POST /api/ask 요청을 받아 에이전트(run_agent)를 실행하고
결과를 JSON으로 돌려준다. 정적 프론트엔드도 함께 서빙한다.

- web/dist(React 빌드)가 있으면 그것을, 없으면 frontend/(정적 HTML)를 서빙
- React는 클라이언트 라우팅(/ask)이므로 알 수 없는 경로는 index.html로 폴백(SPA)

실행:
    pip install -r requirements-api.txt
    # React를 쓰려면 먼저: cd web && npm install && npm run build
    uvicorn backend.app.api.server:app --reload --port 8000

주의:
    답변 생성(generate_answer)과 조사계획(create_plan)은 Gemini를 사용하므로
    .env 의 GEMINI_API_KEY 가 있으면 LLM 답변, 없으면 검색 근거 기반 답변이 나온다.
"""
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.app.agent.workflow import run_agent

PROJECT_ROOT = Path(__file__).resolve().parents[3]
WEB_DIST = PROJECT_ROOT / "web" / "dist"
FRONTEND_DIR = WEB_DIST if WEB_DIST.is_dir() else PROJECT_ROOT / "frontend"

app = FastAPI(title="조문조문 API", version="0.2.0")

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
    except Exception as e:  # 실패 시 프론트가 데모로 폴백함
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


# 정적 에셋 (Vite: web/dist/assets, 정적 HTML: frontend/assets)
_assets = FRONTEND_DIR / "assets"
if _assets.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_assets)), name="assets")


@app.get("/{full_path:path}")
def spa(full_path: str):
    """정적 파일이 있으면 그대로, 없으면 index.html(SPA 라우팅 폴백)."""
    candidate = FRONTEND_DIR / full_path
    if full_path and candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(FRONTEND_DIR / "index.html")
