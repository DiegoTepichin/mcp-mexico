import json
import re
from collections.abc import Sequence
from enum import StrEnum
from typing import Any

import httpx
from mcp import Client
from pydantic import BaseModel

from evals.questions import Question

MAX_TURNS = 6
TIMEOUT_SECONDS = 180
ANSWER_LINE = re.compile(r"RESPUESTA\s*:\s*(.+)", re.IGNORECASE)
NUMBER = re.compile(r"-?\d[\d,]*(?:\.\d+)?")

PLAIN_PROMPT = (
    "Eres un asistente que responde preguntas sobre datos oficiales de México. "
    "Responde con tu mejor cifra, aunque no estés seguro, y sin redondear: da todos los "
    "decimales del dato. Termina con una última línea 'RESPUESTA: <número>' con una sola "
    "cifra, sin unidades."
)
TOOLS_PROMPT = (
    "Eres un asistente que responde preguntas sobre datos oficiales de México. "
    "Usa las herramientas disponibles para obtener el dato oficial; no lo estimes. "
    "No redondees: da todos los decimales del dato. Termina con una última línea "
    "'RESPUESTA: <número>' con una sola cifra, sin unidades."
)

Message = dict[str, Any]


class Mode(StrEnum):
    PLAIN = "plain"
    TOOLS = "tools"


class Outcome(StrEnum):
    CORRECT = "correct"
    WRONG = "wrong"
    NO_ANSWER = "no_answer"


class Result(BaseModel):
    question_id: str
    model: str
    mode: Mode
    reply: str
    parsed: float | None
    outcome: Outcome
    tool_calls: int
    messages: list[Message]


class ChatClient:
    """An OpenAI-compatible `/chat/completions` endpoint: Ollama, OpenRouter, OpenAI."""

    def __init__(
        self, base_url: str, api_key: str | None, http: httpx.AsyncClient | None = None
    ) -> None:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._http = http or httpx.AsyncClient(timeout=TIMEOUT_SECONDS)
        self._url = f"{base_url.rstrip('/')}/chat/completions"
        self._headers = headers

    async def complete(
        self, model: str, messages: Sequence[Message], tools: Sequence[Message] | None = None
    ) -> Message:
        body: dict[str, Any] = {"model": model, "messages": list(messages), "temperature": 0}
        if tools:
            body["tools"] = list(tools)
        response = await self._http.post(self._url, json=body, headers=self._headers)
        response.raise_for_status()
        message: Message = response.json()["choices"][0]["message"]
        return message


def parse_number(reply: str, question: str) -> float | None:
    """The figure the model committed to.

    It is the `RESPUESTA:` line when present. Otherwise the last number in the reply that does
    not appear in the question, so echoing the date or the income does not count as an answer.
    """
    line = ANSWER_LINE.findall(reply)
    candidates = NUMBER.findall(line[-1]) if line else _unasked_numbers(reply, question)
    return _to_float(candidates[-1]) if candidates else None


def _unasked_numbers(reply: str, question: str) -> list[str]:
    asked = {_to_float(n) for n in NUMBER.findall(question)}
    return [n for n in NUMBER.findall(reply) if _to_float(n) not in asked]


def _to_float(text: str) -> float:
    return float(text.replace(",", ""))


def judge(question: Question, parsed: float | None) -> Outcome:
    if parsed is None:
        return Outcome.NO_ANSWER
    return Outcome.CORRECT if question.accepts(parsed) else Outcome.WRONG


def openai_tools(tools: Sequence[Any]) -> list[Message]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema,
            },
        }
        for tool in tools
    ]


async def ask(
    chat: ChatClient,
    model: str,
    question: Question,
    mode: Mode,
    mcp: Client | None = None,
) -> Result:
    """Ask one question; in `tools` mode the model may call the MCP server for up to `MAX_TURNS`.

    A request that times out or fails counts as no answer instead of ending the whole run.
    """
    system = PLAIN_PROMPT if mode is Mode.PLAIN else TOOLS_PROMPT
    messages: list[Message] = [
        {"role": "system", "content": system},
        {"role": "user", "content": question.question},
    ]
    tools = openai_tools((await mcp.list_tools()).tools) if mode is Mode.TOOLS and mcp else None
    calls = 0
    reply: Message = {}
    try:
        for _ in range(MAX_TURNS):
            reply = await chat.complete(model, messages, tools)
            messages.append(reply)
            requested = reply.get("tool_calls") or []
            if not requested or mcp is None:
                break
            calls += len(requested)
            messages.extend([await _run_tool(mcp, call) for call in requested])
    except httpx.HTTPError as error:
        reply = {"role": "assistant", "content": f"[request failed: {type(error).__name__}]"}
        messages.append(reply)
    text = str(reply.get("content") or "")
    parsed = None if reply.get("tool_calls") else parse_number(text, question.question)
    return Result(
        question_id=question.id,
        model=model,
        mode=mode,
        reply=text,
        parsed=parsed,
        outcome=judge(question, parsed),
        tool_calls=calls,
        messages=messages,
    )


async def _run_tool(mcp: Client, call: Message) -> Message:
    function = call["function"]
    try:
        arguments = json.loads(function.get("arguments") or "{}")
        result = await mcp.call_tool(function["name"], arguments)
        content = json.dumps(result.structured_content) if result.structured_content else ""
        content = content or "\n".join(getattr(part, "text", "") for part in result.content)
    except Exception as error:  # a bad call is feedback for the model, not a crash
        content = f"Error: {error}"
    return {"role": "tool", "tool_call_id": call.get("id", ""), "content": content}


async def run(
    chat: ChatClient,
    model: str,
    questions: Sequence[Question],
    modes: Sequence[Mode],
    mcp: Client,
) -> list[Result]:
    return [await ask(chat, model, q, mode, mcp) for mode in modes for q in questions]
