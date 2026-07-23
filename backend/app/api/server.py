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
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.app.agent.workflow import run_agent
from backend.app.assessment.report import (
    build_assessment_report,
)
from backend.app.assessment.schemas import (
    AssessmentWorkflowResult,
)
from backend.app.assessment.workflow import (
    continue_assessment,
    finalize_assessment,
    start_assessment,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
WEB_DIST = PROJECT_ROOT / "web" / "dist"
FRONTEND_DIR = WEB_DIST if WEB_DIST.is_dir() else PROJECT_ROOT / "frontend"

app = FastAPI(title="조문조문 API", version="0.2.0")


def _index_file() -> Path:
    return FRONTEND_DIR / "index.html"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str

class AssessmentStartRequest(BaseModel):
    system_name: str
    system_description: str


class AssessmentContinueRequest(BaseModel):
    session_id: str
    answer: str


class AssessmentFinalizeRequest(BaseModel):
    session_id: str


assessment_sessions: dict[
    str,
    AssessmentWorkflowResult,
] = {}


def _serialize_assessment(
    session_id: str,
    workflow_result: AssessmentWorkflowResult,
    status: str,
    report: str | None = None,
) -> dict:
    return {
        "session_id": session_id,
        "status": status,
        "assessment_input": asdict(
            workflow_result.assessment_input
        ),
        "assessment_result": asdict(
            workflow_result.assessment_result
        ),
        "next_field": workflow_result.next_field,
        "next_question": workflow_result.next_question,
        "report": report,
    }


def _get_assessment_session(
    session_id: str,
) -> AssessmentWorkflowResult:
    workflow_result = assessment_sessions.get(
        session_id
    )

    if workflow_result is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "사전 검토 세션을 찾을 수 없습니다. "
                "처음부터 다시 시작해 주세요."
            ),
        )

    return workflow_result


@app.post("/api/ask")
def ask(req: AskRequest):
    """질문 → 에이전트 실행 → 답변 JSON.

    run_agent는 동기 함수라 FastAPI가 스레드풀에서 실행한다(이벤트 루프 블로킹 없음).
    LLM + 검색 + 검증을 거치므로 응답까지 수십 초가 걸릴 수 있다.
    실패는 반드시 4xx/5xx로 알려 프론트가 '가짜 답변'을 표시하지 않도록 한다.
    """
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="질문을 입력해 주세요.")

    try:
        result = run_agent(question)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"에이전트 실행 중 오류가 발생했습니다: {e}",
        )

    # verdict, answer, confidence, citations, steps, retry_count
    return asdict(result)

@app.post("/api/assessment/start")
def assessment_start(
    req: AssessmentStartRequest,
):
    system_name = req.system_name.strip()
    system_description = (
        req.system_description.strip()
    )

    if not system_name:
        raise HTTPException(
            status_code=400,
            detail="AI 시스템 이름을 입력해 주세요.",
        )

    if not system_description:
        raise HTTPException(
            status_code=400,
            detail="AI 시스템 설명을 입력해 주세요.",
        )

    try:
        workflow_result = start_assessment(
            system_name=system_name,
            system_description=system_description,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "사전 검토 입력을 처리하지 못했습니다: "
                f"{error}"
            ),
        ) from error

    session_id = str(uuid4())
    assessment_sessions[session_id] = (
        workflow_result
    )

    status = (
        "needs_input"
        if workflow_result.next_question
        else "ready_to_finalize"
    )

    return _serialize_assessment(
        session_id=session_id,
        workflow_result=workflow_result,
        status=status,
    )


@app.post("/api/assessment/continue")
def assessment_continue(
    req: AssessmentContinueRequest,
):
    workflow_result = _get_assessment_session(
        req.session_id
    )

    try:
        updated_result = continue_assessment(
            previous_result=workflow_result,
            answer=req.answer,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    assessment_sessions[req.session_id] = (
        updated_result
    )

    status = (
        "needs_input"
        if updated_result.next_question
        else "ready_to_finalize"
    )

    return _serialize_assessment(
        session_id=req.session_id,
        workflow_result=updated_result,
        status=status,
    )


@app.post("/api/assessment/finalize")
def assessment_finalize(
    req: AssessmentFinalizeRequest,
):
    workflow_result = _get_assessment_session(
        req.session_id
    )

    try:
        finalized_result = finalize_assessment(
            workflow_result
        )
        report = build_assessment_report(
            finalized_result
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "법령 근거를 연결하지 못했습니다: "
                f"{error}"
            ),
        ) from error

    assessment_sessions.pop(
        req.session_id,
        None,
    )

    return _serialize_assessment(
        session_id=req.session_id,
        workflow_result=finalized_result,
        status="completed",
        report=report,
    )


@app.get("/health")
def health():
    return {"status": "ok", "frontend": str(FRONTEND_DIR), "built": _index_file().is_file()}


# 정적 에셋 (Vite: web/dist/assets, 정적 HTML: frontend/assets)
_assets = FRONTEND_DIR / "assets"
if _assets.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_assets)), name="assets")


@app.get("/{full_path:path}")
def spa(full_path: str):
    """정적 파일이 있으면 그대로, 없으면 index.html(SPA 라우팅 폴백)."""
    if full_path.startswith("api/"):  # 없는 API 경로가 HTML로 응답되지 않도록
        raise HTTPException(status_code=404, detail="존재하지 않는 API 경로입니다.")

    candidate = (FRONTEND_DIR / full_path).resolve()
    # ../ 로 프로젝트 바깥 파일을 읽지 못하게 제한
    if full_path and candidate.is_file() and candidate.is_relative_to(FRONTEND_DIR.resolve()):
        return FileResponse(candidate)

    index = _index_file()
    if not index.is_file():
        return JSONResponse(
            status_code=503,
            content={
                "detail": "프론트엔드 빌드가 없습니다. `cd web && npm install && npm run build` 후 다시 열어 주세요."
            },
        )
    return FileResponse(index)
