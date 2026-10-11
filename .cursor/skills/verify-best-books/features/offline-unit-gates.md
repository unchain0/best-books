# Offline unit gates

Prove the repo's offline quality gates the same way CI does: unit tests that need no Libgen or best-books.dev, plus importability of the CLI entrypoints.

## Sub-features

- `pytest-offline` runs the default CI test selection.
- `import-entrypoints` loads `main` dependencies without executing a full scrape.

## How to get to it (user POV)

- Developer pushes a PR and GitHub Actions runs lint, offline pytest, and mypy.
- Local agent or human runs the same commands before push.

## Driving it with uv/pytest

Preconditions:

- `uv sync --locked --group dev` succeeded.
- Repo root is cwd.

- Action: run offline tests. Command: `uv run pytest -m "not network and not slow"`. Expect: exit 0, zero failed, network/slow tests deselected.
- Action: smoke-import scraper and libgen. Command: `uv run python -c "from scripts.scraper import run_scraper; from scripts.libgen import Libgen; print('ok')"`. Expect: prints `ok`, exit 0.

## Gotchas

- Tests that call Libgen without `@pytest.mark.network` will run under the offline filter and fail when the mirror resets connections.
- Do not run `uv run python main.py` here; that starts a full multi-hour download.
