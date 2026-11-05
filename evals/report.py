import json
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from pydantic import TypeAdapter

from evals.questions import Question
from evals.runner import Mode, Outcome, Result

RESULTS = TypeAdapter(list[Result])


def save_results(results: Sequence[Result], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(RESULTS.dump_python(list(results), mode="json"), indent=2) + "\n")


def load_results(directory: Path) -> list[Result]:
    return [
        result
        for path in sorted(directory.glob("*.json"))
        for result in RESULTS.validate_json(path.read_text(encoding="utf-8"))
    ]


def summary_table(results: Sequence[Result], questions: Sequence[Question]) -> str:
    """One row per model: correct answers, wrong answers and no answer, without and with tools."""
    topics = {q.id: q.topic for q in questions}
    models = sorted({result.model for result in results})
    lines = [
        "| Model | Mode | Correct | Wrong | No answer | Failed |",
        "|---|---|---|---|---|---|",
    ]
    for model in models:
        for mode in Mode:
            rows = [r for r in results if r.model == model and r.mode is mode]
            if rows:
                lines.append(_row(model, mode, Counter(r.outcome for r in rows), len(rows)))
    lines += ["", _topic_table(results, topics)]
    return "\n".join(lines)


def _row(model: str, mode: Mode, counts: Counter[Outcome], total: int) -> str:
    failed = counts[Outcome.WRONG] + counts[Outcome.NO_ANSWER]
    return (
        f"| {model} | {mode.value} | {counts[Outcome.CORRECT]}/{total} | "
        f"{counts[Outcome.WRONG]} | {counts[Outcome.NO_ANSWER]} | {failed / total:.0%} |"
    )


def _topic_table(results: Sequence[Result], topics: dict[str, str]) -> str:
    """Correct answers per topic for every model and mode that was run."""
    columns = sorted({(r.model, r.mode) for r in results}, key=lambda c: (c[0], c[1].value))
    lines = [
        "| Topic | " + " | ".join(f"{model} {mode.value}" for model, mode in columns) + " |",
        "|---|" + "---|" * len(columns),
    ]
    for topic in sorted(set(topics.values())):
        cells = []
        for model, mode in columns:
            rows = [
                r
                for r in results
                if (r.model, r.mode) == (model, mode) and topics.get(r.question_id) == topic
            ]
            right = sum(1 for r in rows if r.outcome is Outcome.CORRECT)
            cells.append(f"{right}/{len(rows)}" if rows else "-")
        lines.append(f"| {topic} | " + " | ".join(cells) + " |")
    return "\n".join(lines)
