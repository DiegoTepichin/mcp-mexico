import pytest
from mcp import Client

from evals.questions import Question, load_questions
from mcp_mexico.fiscal.isr import isr_table
from mcp_mexico.fiscal.uma import uma_for_year
from mcp_mexico.models import IsrPeriod
from mcp_mexico.server import build_server

QUESTIONS = load_questions()
BY_ID = {question.id: question for question in QUESTIONS}


def test_ids_are_unique() -> None:
    assert len(BY_ID) == len(QUESTIONS)


def test_every_topic_is_covered() -> None:
    assert {q.topic for q in QUESTIONS} == {"fix", "rates", "inflation", "uma", "isr"}


@pytest.mark.anyio
async def test_every_question_names_a_real_tool() -> None:
    async with Client(build_server()) as client:
        names = {tool.name for tool in (await client.list_tools()).tools}

    assert {q.tool for q in QUESTIONS} <= names


@pytest.mark.parametrize("question", QUESTIONS, ids=lambda q: q.id)
def test_every_question_has_a_source_and_a_date(question: Question) -> None:
    assert question.source.url.startswith("https://")
    assert question.tolerance > 0


@pytest.mark.parametrize(
    ("question_id", "year", "field"),
    [
        ("uma-2025-daily", 2025, "daily"),
        ("uma-2024-monthly", 2024, "monthly"),
        ("uma-2026-annual", 2026, "annual"),
        ("uma-2023-daily", 2023, "daily"),
    ],
)
def test_uma_answers_match_the_packaged_tables(question_id: str, year: int, field: str) -> None:
    assert BY_ID[question_id].answer == getattr(uma_for_year(year), field)


def _bracket(year: int, period: IsrPeriod, income: float) -> dict[str, float]:
    table = isr_table(year, period)
    (bracket,) = [
        b
        for b in table.brackets
        if b.lower_limit <= income and (b.upper_limit is None or income <= b.upper_limit)
    ]
    return {"fee": bracket.fixed_fee, "rate": bracket.rate_percent}


def test_isr_answers_match_the_packaged_tables() -> None:
    assert BY_ID["isr-2025-monthly-fee"].answer == _bracket(2025, "monthly", 20_000)["fee"]
    assert BY_ID["isr-2025-monthly-rate"].answer == _bracket(2025, "monthly", 60_000)["rate"]
    assert BY_ID["isr-2026-annual-fee"].answer == _bracket(2026, "annual", 500_000)["fee"]
    (bracket,) = [b for b in isr_table(2024, "monthly").brackets if b.rate_percent == 23.52]
    assert BY_ID["isr-2024-monthly-lower"].answer == bracket.lower_limit


def test_tolerance_decides_what_is_right() -> None:
    fix = BY_ID["fix-2025-03-14"]

    assert fix.accepts(19.87)
    assert not fix.accepts(20.5)
