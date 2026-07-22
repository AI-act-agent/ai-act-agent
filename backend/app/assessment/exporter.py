from pathlib import Path

from backend.app.assessment.report import (
    build_assessment_report,
)
from backend.app.assessment.schemas import (
    AssessmentWorkflowResult,
)


def save_assessment_report(
    workflow_result: AssessmentWorkflowResult,
    output_path: str | Path,
    overwrite: bool = False,
) -> Path:
    """사전 검토 보고서를 Markdown 파일로 저장한다."""

    path = Path(output_path)

    if path.suffix.lower() != ".md":
        raise ValueError(
            "보고서 파일의 확장자는 .md여야 합니다."
        )

    if path.exists() and not overwrite:
        raise FileExistsError(
            f"이미 보고서 파일이 존재합니다: {path}"
        )

    report_text = build_assessment_report(
        workflow_result
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        report_text,
        encoding="utf-8",
    )

    return path.resolve()