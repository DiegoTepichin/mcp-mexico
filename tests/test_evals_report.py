from pathlib import Path

import pytest

from evals.questions import load_questions
from evals.report import load_results, save_results, summary_table
from evals.runner import Mode, Outcome, Result

QUESTIONS = load_questions()


def result(question_id: str, model: str, mode: Mode, outcome: Outcome) -> Result:
    return Result(
        question_id=question_id,
        model=model,
        mode=mode,
        reply="RESPUESTA: 1",
        parsed=None if outcome is Outcome.NO_ANSWER else 1.0,
        outcome=outcome,
        tool_calls=0,
        messages=[{"role": "user", "content": "hola"}],
    )


@pytest.fixture
def results() -> list[Result]:
    return [
        result("uma-2025-daily", "small", Mode.PLAIN, Outcome.WRONG),
        result("fix-2025-03-14", "small", Mode.PLAIN, Outcome.NO_ANSWER),
        result("uma-2024-monthly", "small", Mode.PLAIN, Outcome.CORRECT),
        result("uma-2025-daily", "small", Mode.TOOLS, Outcome.CORRECT),
        result("fix-2025-03-14", "small", Mode.TOOLS, Outcome.CORRECT),
        result("uma-2024-monthly", "small", Mode.TOOLS, Outcome.WRONG),
    ]


def test_results_survive_a_round_trip(tmp_path: Path, results: list[Result]) -> None:
    save_results(results, tmp_path / "nested" / "small.json")

    assert load_results(tmp_path / "nested") == results


def test_summary_counts_failures_without_and_with_tools(results: list[Result]) -> None:
    table = summary_table(results, QUESTIONS)

    assert "| small | plain | 1/3 | 1 | 1 | 67% |" in table
    assert "| small | tools | 2/3 | 1 | 0 | 33% |" in table


def test_summary_breaks_down_correct_answers_by_topic(results: list[Result]) -> None:
    table = summary_table(results, QUESTIONS)

    assert "| fix | 0/1 | 1/1 |" in table
    assert "| uma | 1/2 | 1/2 |" in table
    assert "| isr | - | - |" in table


def test_summary_lists_each_model_once_per_mode(results: list[Result]) -> None:
    other = [r.model_copy(update={"model": "big"}) for r in results if r.mode is Mode.PLAIN]

    table = summary_table([*results, *other], QUESTIONS)

    assert table.count("| big |") == 1
    assert table.count("| small |") == 2
