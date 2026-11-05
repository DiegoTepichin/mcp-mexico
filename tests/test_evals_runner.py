import json
from pathlib import Path
from typing import Any

import anyio.to_thread
import httpx
import pytest
from mcp import Client

from evals.__main__ import main
from evals.questions import Question, load_questions
from evals.runner import (
    MAX_TURNS,
    ChatClient,
    Mode,
    Outcome,
    ask,
    judge,
    openai_tools,
    parse_number,
    run,
)
from mcp_mexico.server import build_server

pytestmark = pytest.mark.anyio

QUESTIONS = {q.id: q for q in load_questions()}
UMA = QUESTIONS["uma-2025-daily"]
BASE_URL = "http://models.test/v1/"


class ScriptedModel:
    """An OpenAI-compatible endpoint that plays back messages and records every request."""

    def __init__(self, *messages: dict[str, Any]) -> None:
        self.messages = list(messages)
        self.requests: list[httpx.Request] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        message = self.messages.pop(0) if len(self.messages) > 1 else self.messages[0]
        return httpx.Response(200, json={"choices": [{"message": message}]})

    def chat(self, api_key: str | None = None) -> ChatClient:
        http = httpx.AsyncClient(transport=httpx.MockTransport(self.handle))
        return ChatClient(BASE_URL, api_key, http)

    def body(self, index: int) -> dict[str, Any]:
        body: dict[str, Any] = json.loads(self.requests[index].content)
        return body


def say(text: str) -> dict[str, Any]:
    return {"role": "assistant", "content": text}


def call(name: str, arguments: str, call_id: str = "call-1") -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {"id": call_id, "type": "function", "function": {"name": name, "arguments": arguments}}
        ],
    }


@pytest.mark.parametrize(
    ("reply", "expected"),
    [
        ("RESPUESTA: 113.14", 113.14),
        ("El valor es alto.\nRESPUESTA: 1,640.18", 1640.18),
        ("respuesta : 7.75 % anual", 7.75),
        ("Creo que fue 19.87 pesos.", 19.87),
        ("El 14 de marzo de 2025 fue 19.87", 19.87),
        ("RESPUESTA: 5\nRESPUESTA: 6", 6.0),
        ("No tengo ese dato.", None),
        ("", None),
    ],
)
def test_parse_number(reply: str, expected: float | None) -> None:
    question = "¿Cuál fue el FIX el 14 de marzo de 2025?"

    assert parse_number(reply, question) == expected


def test_numbers_already_in_the_question_are_not_an_answer() -> None:
    assert parse_number("Para $20,000.00 en 2025 no sé.", "ingreso de $20,000.00 en 2025") is None


def test_judge_separates_wrong_from_no_answer() -> None:
    assert judge(UMA, 113.14) is Outcome.CORRECT
    assert judge(UMA, 113.15) is Outcome.WRONG
    assert judge(UMA, None) is Outcome.NO_ANSWER


async def test_openai_tools_describe_every_mcp_tool() -> None:
    async with Client(build_server()) as client:
        tools = openai_tools((await client.list_tools()).tools)

    by_name = {tool["function"]["name"]: tool for tool in tools}
    assert "get_uma" in by_name
    assert by_name["get_uma"]["type"] == "function"
    assert by_name["get_uma"]["function"]["parameters"]["type"] == "object"
    assert by_name["get_uma"]["function"]["description"]


async def test_plain_mode_sends_no_tools() -> None:
    model = ScriptedModel(say("Creo que es 113.14\nRESPUESTA: 113.14"))

    result = await ask(model.chat(), "m", UMA, Mode.PLAIN)

    assert result.outcome is Outcome.CORRECT
    assert result.tool_calls == 0
    assert "tools" not in model.body(0)
    assert model.body(0)["temperature"] == 0
    assert model.body(0)["messages"][1]["content"] == UMA.question


async def test_a_wrong_answer_is_wrong() -> None:
    model = ScriptedModel(say("RESPUESTA: 99.5"))

    result = await ask(model.chat(), "m", UMA, Mode.PLAIN)

    assert (result.outcome, result.parsed) == (Outcome.WRONG, 99.5)


async def test_tools_mode_lets_the_model_call_the_server() -> None:
    model = ScriptedModel(call("get_uma", '{"year": 2025}'), say("RESPUESTA: 113.14"))

    async with Client(build_server()) as mcp:
        result = await ask(model.chat(), "m", UMA, Mode.TOOLS, mcp)

    assert result.outcome is Outcome.CORRECT
    assert result.tool_calls == 1
    assert [t["function"]["name"] for t in model.body(0)["tools"]].count("get_uma") == 1
    returned = model.body(1)["messages"][-1]
    assert returned["role"] == "tool"
    assert returned["tool_call_id"] == "call-1"
    assert json.loads(returned["content"])["daily"] == 113.14


async def test_a_failed_tool_call_is_fed_back_to_the_model() -> None:
    model = ScriptedModel(call("get_uma", '{"year": 1999}'), say("RESPUESTA: 113.14"))

    async with Client(build_server()) as mcp:
        result = await ask(model.chat(), "m", UMA, Mode.TOOLS, mcp)

    assert "Available years" in model.body(1)["messages"][-1]["content"]
    assert result.outcome is Outcome.CORRECT


@pytest.mark.parametrize("arguments", ["{not json", '{"year": "last"}', '{"nope": 1}'])
async def test_malformed_arguments_do_not_crash_the_run(arguments: str) -> None:
    model = ScriptedModel(call("get_uma", arguments), say("No pude obtenerlo."))

    async with Client(build_server()) as mcp:
        result = await ask(model.chat(), "m", UMA, Mode.TOOLS, mcp)

    assert result.outcome is Outcome.NO_ANSWER
    assert model.body(1)["messages"][-1]["content"]


async def test_an_unknown_tool_is_reported_to_the_model() -> None:
    model = ScriptedModel(call("get_weather", "{}"), say("RESPUESTA: 1"))

    async with Client(build_server()) as mcp:
        await ask(model.chat(), "m", UMA, Mode.TOOLS, mcp)

    assert "Unknown tool: get_weather" in model.body(1)["messages"][-1]["content"]


async def test_a_model_that_never_stops_calling_tools_gets_no_answer() -> None:
    model = ScriptedModel(call("get_uma", '{"year": 2025}'))

    async with Client(build_server()) as mcp:
        result = await ask(model.chat(), "m", UMA, Mode.TOOLS, mcp)

    assert result.outcome is Outcome.NO_ANSWER
    assert result.tool_calls == MAX_TURNS
    assert len(model.requests) == MAX_TURNS


async def test_run_asks_every_question_in_every_mode() -> None:
    model = ScriptedModel(say("RESPUESTA: 1"))
    questions: list[Question] = [UMA, QUESTIONS["uma-2024-monthly"]]

    async with Client(build_server()) as mcp:
        results = await run(model.chat(), "m", questions, [Mode.PLAIN, Mode.TOOLS], mcp)

    assert [(r.mode, r.question_id) for r in results] == [
        (Mode.PLAIN, "uma-2025-daily"),
        (Mode.PLAIN, "uma-2024-monthly"),
        (Mode.TOOLS, "uma-2025-daily"),
        (Mode.TOOLS, "uma-2024-monthly"),
    ]


async def test_the_chat_client_sends_the_api_key_and_uses_the_chat_path() -> None:
    model = ScriptedModel(say("hola"))

    await model.chat(api_key="secret").complete("m", [{"role": "user", "content": "hi"}])

    request = model.requests[0]
    assert request.headers["authorization"] == "Bearer secret"
    assert str(request.url) == "http://models.test/v1/chat/completions"


async def test_the_chat_client_omits_the_header_without_a_key() -> None:
    model = ScriptedModel(say("hola"))

    await model.chat().complete("m", [{"role": "user", "content": "hi"}])

    assert "authorization" not in model.requests[0].headers


async def test_http_errors_are_raised() -> None:
    http = httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(500)))
    chat = ChatClient(BASE_URL, None, http)

    with pytest.raises(httpx.HTTPStatusError):
        await chat.complete("m", [{"role": "user", "content": "hi"}])


async def test_the_command_line_runs_and_reports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    model = ScriptedModel(say("RESPUESTA: 1"))
    monkeypatch.setattr("evals.__main__.ChatClient", lambda base_url, api_key: model.chat(api_key))
    results = tmp_path / "results"

    code = await anyio.to_thread.run_sync(
        main, ["run", "--model", "tiny/model:1b", "--mode", "plain", "--results", str(results)]
    )

    assert code == 0
    assert "0/18 correct" in capsys.readouterr().out
    assert (results / "tiny_model_1b.json").exists()
    assert main(["report", "--results", str(results)]) == 0
    assert "| tiny/model:1b | plain | 0/18 |" in capsys.readouterr().out


async def test_a_request_that_times_out_counts_as_no_answer() -> None:
    def time_out(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("too slow", request=request)

    chat = ChatClient(BASE_URL, None, httpx.AsyncClient(transport=httpx.MockTransport(time_out)))

    result = await ask(chat, "m", UMA, Mode.PLAIN)

    assert result.outcome is Outcome.NO_ANSWER
    assert result.reply == "[request failed: ReadTimeout]"


async def test_both_modes_ask_for_unrounded_figures() -> None:
    model = ScriptedModel(say("RESPUESTA: 1"))

    async with Client(build_server()) as mcp:
        await ask(model.chat(), "m", UMA, Mode.PLAIN)
        await ask(model.chat(), "m", UMA, Mode.TOOLS, mcp)

    for index in (0, 1):
        assert "redonde" in model.body(index)["messages"][0]["content"]
