# Truth gap: official Mexican figures with and without mcp-mexico

How often does a model give the right official figure when it answers from memory, and when it can call this server? This page documents the method, the results of one run and what they do not show.

## Result

Three small local models, 18 questions, one run, temperature 0. A question counts as failed when the answer is wrong or the model gives no number.

| Model | Without tools | With mcp-mexico |
|---|---|---|
| gemma3:1b | 18/18 failed | not run: Ollama does not support tools for this model |
| llama3.2:3b | 18/18 failed (14 wrong, 4 no answer) | 4/18 failed (22%) |
| qwen2.5:1.5b | 18/18 failed (17 wrong, 1 no answer) | 6/18 failed (33%) |

Correct answers by topic (out of 3 FIX, 3 rates, 4 inflation, 4 UMA, 4 ISR questions):

| Topic | llama3.2:3b tools | qwen2.5:1.5b tools |
|---|---|---|
| FIX exchange rate | 3/3 | 3/3 |
| Interest rates | 3/3 | 3/3 |
| Inflation (INPC) | 4/4 | 3/4 |
| UMA | 4/4 | 3/4 |
| ISR tables | 0/4 | 0/4 |

Per-question answers and the full conversations are in [`evals/results/`](../evals/results).

What the run shows:

- **Without tools, none of the three got a single figure right.** Asked for the FIX on 14 March 2025 (19.8693), gemma3:1b answered 13.8, llama3.2:3b answered 198573 and qwen2.5:1.5b answered 19.9555. The "no answer" cases were refusals such as "I have no updated information on the UMA for 2025".
- **With tools, the lookups work.** Both models called the right tool first on all 18 questions. Of the 14 FIX, rate, inflation and UMA questions, llama3.2:3b answered all 14 correctly and qwen2.5:1.5b 12 (it misread the monthly inflation figure as 2.9 instead of 0.29, and gave the daily UMA for a monthly question).
- **The ISR questions failed for both models even with the tool.** The server returns the whole bracket table; the model has to choose the bracket for the income and read its fixed fee or rate. Both models picked the wrong row, and qwen2.5:1.5b also asked for the wrong year. A tool that computes the tax for an income would remove that step; it is not part of this release.

## Method

- **Questions:** [`evals/questions.json`](../evals/questions.json), 18 questions in Spanish across five topics. Each has the official figure, a tolerance, the source and the date it was verified.
- **Answers:** the FIX, rate and inflation figures were read through this server from Banxico SIE and INEGI on 2026-11-05. The UMA and ISR figures come from the packaged tables, verified against the DOF and the SAT annex on 2026-10-03; `tests/test_evals_questions.py` checks them against those tables. Because the tool arm reads the same sources the answers came from, the run measures whether a model gets the figure and reports it faithfully, not whether the sources are right.
- **Tolerance:** an answer is correct within one cent for exchange rates, rates, inflation, the INPC index and UMA/ISR amounts (half a cent for amounts in pesos). A model that rounds 113.14 to 113 fails.
- **Reading the answer:** the model is asked to end with a `RESPUESTA: <number>` line. Without it, the last number in the reply that does not appear in the question is used.
- **Tools arm:** the model gets the server's eight tools in OpenAI function-calling format and may make up to 6 rounds of calls. The server runs in the same process with the real Banxico and INEGI APIs.
- **Prompts:** both arms are told not to round. The first run did not say so and the models rounded figures they had retrieved correctly (for example `113.14` to `113`). I added the instruction to both arms and ran everything again; the first results are kept in [`evals/results/prompt-v1/`](../evals/results/prompt-v1). In that first run llama3.2:3b got 0/18 without tools and 7/18 with them, and qwen2.5:1.5b did not finish because a request timed out.
- **Failures:** a request that fails or times out counts as no answer. It happened once, for qwen2.5:1.5b on the UMA 2025 question without tools.

## Limits

- Three models of 1 to 3 billion parameters, run locally. Larger models would know more figures and use tools better; this run says nothing about them.
- One run, 18 questions. The percentages move by several points with one question, and no confidence intervals are given.
- The questions ask for exact figures, which is where memory is weakest. They say nothing about how a model does on questions that need only approximate figures.
- Questions are written in Spanish; the models were not compared in English.
- The questions are public in this repository, so future models can be trained on them.

## Reproduce

Needs [Ollama](https://ollama.com) with the models, and Banxico and INEGI tokens in `.env` (see the README).

```bash
uv run --env-file .env python -m evals run --model gemma3:1b --mode plain
uv run --env-file .env python -m evals run --model llama3.2:3b --model qwen2.5:1.5b
uv run python -m evals report
```

`--base-url` and `--api-key-env` point the same command at any OpenAI-compatible API, for example OpenRouter.
