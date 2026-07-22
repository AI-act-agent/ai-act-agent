"""대화 실행 기능"""

from backend.app.assessment.exporter import (
    save_assessment_report,
)
from backend.app.assessment.report import (
    build_assessment_report,
)
from backend.app.assessment.workflow import (
    continue_assessment,
    start_assessment,
)


def _read_required(prompt: str) -> str:
    while True:
        value = input(prompt).strip()

        if value:
            return value

        print("값을 입력해 주세요.")


def run_cli() -> int:
    print("고영향 AI 사전 검토")
    print("=" * 40)
    print(
        "현재는 규칙 기반 판정과 보고서 형식을 "
        "확인하는 미리보기입니다."
    )
    print(
        "법령·가이드라인 RAG 근거는 벡터 저장소 "
        "갱신 후 연결됩니다."
    )
    print()

    system_name = _read_required(
        "AI 시스템 이름: "
    )
    system_description = _read_required(
        "AI 시스템 설명: "
    )

    try:
        workflow_result = start_assessment(
            system_name=system_name,
            system_description=system_description,
        )
    except Exception as error:
        print(
            "입력 정보를 구조화하지 못했습니다: "
            f"{error}"
        )
        return 1

    while workflow_result.next_question:
        print()
        print(
            f"추가 질문: {workflow_result.next_question}"
        )

        answer = input("답변: ").strip()

        try:
            workflow_result = continue_assessment(
                previous_result=workflow_result,
                answer=answer,
            )
        except ValueError as error:
            print(error)

    print()
    print("사전 검토가 완료되었습니다.")
    print(
        "검토 결과: "
        f"{workflow_result.assessment_result.verdict}"
    )
    print(
        "검토 요약: "
        f"{workflow_result.assessment_result.summary}"
    )
    print()

    report_text = build_assessment_report(
        workflow_result
    )

    print(report_text)

    print()
    output_path = input(
        "Markdown 보고서를 저장할 경로"
        "(.md, 저장하지 않으려면 Enter): "
    ).strip()

    if not output_path:
        return 0

    try:
        saved_path = save_assessment_report(
            workflow_result=workflow_result,
            output_path=output_path,
        )
    except (ValueError, FileExistsError) as error:
        print(f"보고서를 저장하지 못했습니다: {error}")
        return 1

    print(f"보고서 저장 완료: {saved_path}")

    return 0


def main() -> None:
    run_cli()


if __name__ == "__main__":
    main()