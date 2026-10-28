# Project 4 — Troubleshooting

## `ModuleNotFoundError: No module named 'common'`

Run from the **workspace root**, not from inside `common/` or `engine/`:

```bash
cd workspace
python -c "from engine.fraud_engine import run_fraud_detection; print('ok')"
```

## `RuntimeError: No API key found`

`common/patterns.py` calls `llm_client.get_llm_client()`, which needs
`OPENROUTER_API_KEY` (lab default) or `ANTHROPIC_API_KEY`:

```bash
source ~/.bashrc
test -n "$OPENROUTER_API_KEY" && echo "OPENROUTER: set" || echo "OPENROUTER: MISSING"
```

## `messages.create` raises a 404, and the traceback shows HTML / Next.js content

This is not an API error — it's OpenRouter's website "page not found" handler,
which means the request never reached their API at all. Check `base_url` in
`llm_client.py`: it must be `https://openrouter.ai/api` **without** a trailing
`/v1` — the Anthropic SDK appends `/v1/messages` itself, so a base URL that
already ends in `/v1` doubles up to `.../api/v1/v1/messages`, which doesn't
exist. If you see `og:site_name` / `Not Found | OpenRouter` anywhere in the
error output, this is the cause.

## `classify_with_claude` raises a JSON parse error

The model occasionally wraps its JSON in a markdown code fence (```` ```json ````).
Strip leading/trailing triple-backtick fences from the response text before
calling `json.loads()`. Also confirm `CLASSIFY_SYSTEM_PROMPT` in
`common/patterns.py` is being sent as the system prompt, not folded into the
user message — that's what keeps the model from adding prose around the JSON.

## Throughput is below `target_tps`

- Check `DEFAULT_BATCH_SIZE` / `DEFAULT_MAX_WORKERS` in
  `engine/fraud_engine.py` — too few workers under-utilizes concurrency, too
  many can hit provider rate limits and start erroring/retrying.
- Confirm `process_in_batches` is actually using `ThreadPoolExecutor`
  concurrently and not accidentally processing batches one at a time in a
  `for` loop.
- Confirm `prefilter_candidates` is narrowing the field before
  `classify_with_claude` runs — see Experiment 5 in `EXPERIMENTS.md`.

## A stub still raises `NotImplementedError` after you implemented it

- Confirm you removed the `raise NotImplementedError(...)` line and the
  `TODO(P4)` comment above it — leaving either in place means Python still
  hits the stub before your code runs.
- Confirm `engine/fraud_engine.py` doesn't still call an unimplemented
  function further down the pipeline — a `# BUILD:` comment there just marks
  which activity wires that step; the underlying `common/*.py` function still
  has to be finished.
- `reports/benchmark_result.json` and `reports/DAILY_FRAUD_SUMMARY.md` only
  appear after `engine/fraud_engine.py` (or `run_fraud_detection()`) has run
  end to end — run it once after finishing Activity 5.

## Report shows 0 transactions in every tier

`generate_daily_summary` is probably reading the wrong shape from
`prioritize_queue`'s output — confirm it returns `"counts"` with keys
`"HIGH"`/`"MEDIUM"`/`"LOW"`, and that `prioritize_queue` was called with the
**scored** transaction list (post `detect_fraud_signals`), not the raw
generator output.
