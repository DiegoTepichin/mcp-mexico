from datetime import date
from pathlib import Path

from pydantic import BaseModel, TypeAdapter

from mcp_mexico.models import Source

QUESTIONS_FILE = Path(__file__).with_name("questions.json")


class Question(BaseModel, frozen=True):
    id: str
    topic: str
    tool: str
    question: str
    answer: float
    tolerance: float
    unit: str
    source: Source
    verified_on: date

    def accepts(self, value: float) -> bool:
        """An answer is right when it is within `tolerance` of the official figure."""
        return abs(value - self.answer) <= self.tolerance


def load_questions(path: Path = QUESTIONS_FILE) -> list[Question]:
    return TypeAdapter(list[Question]).validate_json(path.read_text(encoding="utf-8"))
