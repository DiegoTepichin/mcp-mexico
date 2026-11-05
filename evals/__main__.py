import argparse
import asyncio
import logging
import os
import re
from pathlib import Path

from mcp import Client

from evals.questions import load_questions
from evals.report import load_results, save_results, summary_table
from evals.runner import ChatClient, Mode, Outcome, run
from mcp_mexico.server import build_server

RESULTS_DIR = Path(__file__).with_name("results")
DEFAULT_BASE_URL = "http://localhost:11434/v1"


def main(argv: list[str] | None = None) -> int:
    # httpx logs every request URL at INFO, and INEGI requires the token in the URL.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    args = _parser().parse_args(argv)
    if args.command == "report":
        print(summary_table(load_results(args.results), load_questions()))
        return 0
    asyncio.run(_run(args))
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m evals", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run_parser = commands.add_parser("run", help="ask every question and save the answers")
    run_parser.add_argument("--model", action="append", required=True, help="repeat for several")
    run_parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="OpenAI-compatible API")
    run_parser.add_argument("--api-key-env", help="name of the variable holding the API key")
    run_parser.add_argument("--mode", choices=[m.value for m in Mode], action="append")
    run_parser.add_argument("--results", type=Path, default=RESULTS_DIR)
    report_parser = commands.add_parser("report", help="print the results as Markdown tables")
    report_parser.add_argument("--results", type=Path, default=RESULTS_DIR)
    return parser


async def _run(args: argparse.Namespace) -> None:
    api_key = os.environ.get(args.api_key_env) if args.api_key_env else None
    chat = ChatClient(args.base_url, api_key)
    modes = [Mode(m) for m in args.mode] if args.mode else list(Mode)
    questions = load_questions()
    async with Client(build_server()) as mcp:
        for model in args.model:
            results = await run(chat, model, questions, modes, mcp)
            target = args.results / f"{re.sub(r'[^A-Za-z0-9._-]+', '_', model)}.json"
            save_results(results, target)
            right = sum(1 for r in results if r.outcome is Outcome.CORRECT)
            print(f"{model}: {right}/{len(results)} correct, saved {target}")


if __name__ == "__main__":
    raise SystemExit(main())
