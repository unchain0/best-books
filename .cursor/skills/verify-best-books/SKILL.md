---
name: verify-best-books
description: Verify the best-books CLI (scrape best-books.dev, search/download via Libgen). Use when proving unit behavior, CI gates, or offline smoke of scripts without a full download run.
---

# verify-best-books

Primary surface is a short-lived CLI (`uv run python main.py`) that scrapes best-books.dev and downloads EPUBs from Libgen. A full run hits the live web and can take hours and gigabytes. Default verification is offline unit tests plus the same lint/type gates CI runs. Live network checks are opt-in only.

## Launch

There is no long-lived server. Prepare once per run:

```bash
uv sync --locked --group dev
```

Ready when `uv run python -c "from scripts.scraper import Scraper, run_scraper; from scripts.libgen import Libgen"` exits 0.

Full product launch (destructive, live network, long):

```bash
uv run python main.py
```

Do not run the full product path unless the task explicitly requires an end-to-end download proof. Prefer mapped offline features first.

## Doctor

```bash
uv run python -c "import sys; assert sys.version_info[:2]==(3,13); from scripts.scraper import Scraper; from scripts.libgen import Libgen; print('ok')"
uv run ruff check .
uv run mypy .
```

Require exit 0 on each. If any fail, stop and fix before driving features.

## Drive

Offline (default, matches CI test step):

```bash
uv run pytest -m "not network and not slow"
```

Live network (manual only, flaky if Libgen or best-books.dev is down):

```bash
uv run pytest -m network
```

Slow downloads:

```bash
uv run pytest -m slow
```

Drive feature recipes under `features/`. Capture command, stdout, stderr, and exit code for every step.

## Evidence

Store under `.cursor/skills/verify-best-books/evidence/<run-id>/`:

- `doctor.txt` (command output)
- `pytest-offline.txt` (full pytest -v output)
- `import-smoke.txt` (import check)

Proof standards:

- Offline unit tests must pass with the CI marker expression.
- Utils and pure helpers are proven by literal assertions in `tests/`.
- Network and download paths are proven only when intentionally opted in; a skipped or deselected network test is not a pass of live Libgen.
- Never claim a full-site download worked from unit tests alone.

## Cleanup

Remove any temporary download dirs the run created under `/tmp` or a disposable `books-verify-*` path. Do not delete `evidence/`. Do not delete the user's real `books/` or `logs/` trees unless this run created them inside a disposable path.

## Helpers

No extra helper binary. Use `uv run` for every command so the project venv is consistent with CI.
