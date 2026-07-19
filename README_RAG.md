# AI 기본법 RAG 파이프라인

AI 기본법 관련 사용자 질문을 임베딩하고, 의미적으로 가까운 법령 조문을 검색하는 V1~V2 RAG 파이프라인입니다.

## 1. 담당 범위

- Gemini Embedding API 연동
- 법령 청크 임베딩 생성
- 임베딩 결과 로컬 저장
- 코사인 유사도 기반 Top-K 검색
- V1 단발성 Dense Retrieval
- V2 참조 조항 확장
- 에이전트에서 호출할 수 있는 `retrieve()` 함수 제공

답변 생성, 조사 계획 생성, 재검색 판단 및 Grounding Check는 에이전트 영역에서 담당합니다.

## 2. 프로젝트 구조

```text
AI-LAW-AGENT/
├── backend/
│   └── app/
│       └── rag/
│           ├── __init__.py
│           └── pipeline.py
├── data/
│   ├── processed/
│   │   └── sample_law_chunks.json
│   └── vector_store/
│       └── law_embeddings.json
├── .env
├── .gitignore
└── README_RAG.md
```

## 3. 환경변수

프로젝트 최상위의 `.env` 파일에 다음 값을 설정합니다.

```env
GEMINI_API_KEY=본인의_Gemini_API_키
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
```

`.env`에는 API 키가 포함되므로 GitHub에 업로드하지 않습니다.

## 4. 필요한 패키지

```bash
python -m pip install google-genai python-dotenv numpy
```

## 5. 임베딩 생성

법령 청크를 임베딩하고 다음 파일에 저장합니다.

```text
data/vector_store/law_embeddings.json
```

실행 명령:

```bash
python -m backend.app.rag.pipeline --build
```

## 6. V1 실행

V1은 질문과 의미적으로 가까운 법령 조문을 Top-K만큼 검색합니다.

```bash
python -m backend.app.rag.pipeline --version V1 --top-k 5 --question "생성형 AI 결과물에 표시해야 하나요?"
```

## 7. V2 실행

V2는 V1 검색 결과에 포함된 `references`를 확인하고 관련 조항을 추가합니다.

```bash
python -m backend.app.rag.pipeline --version V2 --top-k 1 --question "생성형 AI 결과물에 표시해야 하나요?"
```

검색으로 찾은 조항은 다음 값으로 표시됩니다.

```json
"retrieval_type": "dense"
```

참조 관계를 따라 추가한 조항은 다음 값으로 표시됩니다.

```json
"retrieval_type": "reference"
```

참조 조항의 `score`는 `null`일 수 있습니다.

## 8. 에이전트 연결 방법

에이전트에서는 다음과 같이 검색 함수를 불러옵니다.

```python
from backend.app.rag import retrieve

evidence = retrieve(
    question="생성형 AI 결과물에 표시해야 하나요?",
    top_k=3,
    expand_reference=True
)
```

### 주요 매개변수

- `question`: 사용자 질문
- `top_k`: Dense Retrieval로 가져올 조항 수
- `expand_reference`: 참조 조항 확장 여부
- `max_total`: 참조 조항을 포함한 최대 결과 수
- `records`: 미리 불러온 벡터 데이터이며, 생략하면 자동으로 불러옴

## 9. 법령 청크 입력 형식

```json
{
  "chunk_id": "ACT_31",
  "document_name": "인공지능기본법",
  "document_type": "법률",
  "article_number": "제31조",
  "article_title": "인공지능 투명성 확보 의무",
  "article_text": "조문 원문",
  "effective_date": "2026-07-21",
  "source_url": "국가법령정보센터 URL",
  "references": ["DECREE_23"]
}
```

## 10. 검색 결과 형식

```json
{
  "chunk_id": "ACT_31",
  "document_name": "인공지능기본법",
  "document_type": "법률",
  "article_number": "제31조",
  "article_title": "인공지능 투명성 확보 의무",
  "article_text": "조문 원문",
  "effective_date": "2026-07-21",
  "source_url": "국가법령정보센터 URL",
  "references": ["DECREE_23"],
  "score": 0.82,
  "retrieval_type": "dense"
}
```

## 11. 현재 상태와 제한사항

현재는 실제 법령 청크를 전달받기 전이므로 샘플 데이터를 사용합니다.

완료된 기능:

- 임베딩 API 연결
- 벡터 생성 및 저장
- V1 검색
- V2 참조 조항 확장
- 에이전트용 공통 검색 함수

실제 법령 데이터를 받은 후 진행할 작업:

- 실제 `law_chunks.json` 적용
- 임베딩 재생성
- Top-K 튜닝
- Hit@1, Hit@3, Hit@5 평가
- MRR 평가
- V1과 V2 검색 성능 비교

## 12. 주의사항

- `.env`는 GitHub에 업로드하지 않습니다.
- `.venv/`는 GitHub에 업로드하지 않습니다.
- `data/vector_store/`는 실행 시 재생성할 수 있으므로 GitHub에 업로드하지 않습니다.
- 실제 법령 데이터를 적용할 때 샘플 임베딩을 그대로 사용하지 않고 `--build`로 다시 생성해야 합니다.