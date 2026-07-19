from dataclasses import dataclass, field


@dataclass
class Evidence:
    article_id: str
    article: str
    text: str
    source_url: str
    score: float


@dataclass
class Plan:
    sub_questions: list[str] = field(default_factory=list)
    search_queries: list[str] = field(default_factory=list)


@dataclass
class AgentResult:
    verdict: str
    answer: str
    confidence: str
    citations: list[Evidence] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    retry_count: int = 0