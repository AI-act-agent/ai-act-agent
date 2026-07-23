# 조문조문 Frontend

AI기본법 전문 QA 에이전트의 사용자 UI. 정적 HTML/CSS/JS (빌드 불필요).

## 화면
- `index.html` — 랜딩 페이지
- `ask.html` — 서비스(질문) 화면

## 바로 보기 (백엔드 없이)
`index.html` 을 브라우저로 더블클릭해서 열면 됩니다.
질문 화면은 백엔드 연결 실패 시 **내장 데모 응답**으로 동작합니다.

## 실제 백엔드에 연결 (실제 RAG 답변)
1. 의존성 설치:
   ```bash
   pip install -r requirements.txt          # 임베딩(sentence-transformers 등)
   pip install -r requirements-api.txt      # fastapi, uvicorn
   ```
2. **벡터스토어 구축** (최초 1회, `data/processed/law_chunks.json` → 임베딩):
   ```bash
   python -c "from backend.app.rag.pipeline import build_vector_store; build_vector_store()"
   # → data/vector_store/law_embeddings.json 생성 (임베딩은 로컬, 키 불필요)
   ```
3. 프로젝트 루트에서 서버 실행:
   ```bash
   uvicorn backend.app.api.server:app --reload --port 8000
   ```
4. 브라우저에서 http://localhost:8000 접속
   - 같은 서버가 프론트엔드와 `/api/ask` 를 함께 서빙하므로 CORS 설정 불필요
   - `ask.html` 의 질문이 실제 `run_agent()` → RAG 검색으로 전달됩니다

### 동작 수준
- **키 없이**: 로컬 임베딩 검색 + 검색 근거 인용 답변(오프라인). 바로 동작합니다.
- **`GEMINI_API_KEY` 설정 시**: LLM 조사계획 + LLM 답변 생성 + 로컬 NLI 근거검증까지 전체 파이프라인 동작.
  ```bash
  export GEMINI_API_KEY=발급받은키
  ```

> 다른 포트/호스트에서 프론트를 열 경우 `assets/app.js` 상단의 `API_BASE` 를 서버 주소로 바꾸세요.
