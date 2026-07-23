# 조문조문 Frontend

AI기본법 전문 QA 에이전트의 사용자 UI. 정적 HTML/CSS/JS (빌드 불필요).

## 화면
- `index.html` — 랜딩 페이지
- `ask.html` — 서비스(질문) 화면

## 바로 보기 (백엔드 없이)
`index.html` 을 브라우저로 더블클릭해서 열면 됩니다.
질문 화면은 백엔드 연결 실패 시 **내장 데모 응답**으로 동작합니다.

## 실제 백엔드에 연결
1. 의존성 설치: `pip install fastapi uvicorn`
2. (에이전트용) 환경변수 `GEMINI_API_KEY` 설정
3. 프로젝트 루트에서 서버 실행:
   ```bash
   uvicorn backend.app.api.server:app --reload --port 8000
   ```
4. 브라우저에서 http://localhost:8000 접속
   - 같은 서버가 프론트엔드와 `/api/ask` 를 함께 서빙하므로 CORS 설정 불필요
   - `ask.html` 의 질문이 실제 `run_agent()` 로 전달됩니다

> 다른 포트/호스트에서 프론트를 열 경우 `assets/app.js` 상단의 `API_BASE` 를 서버 주소로 바꾸세요.
