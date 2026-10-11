---
name: verify-best-books
description: Verify the best-books downloader CLI (scrape best-books.dev, Libgen EPUB search/download). Use when proving offline gates, list scraping, or a single Libgen search without a full multi-hour download run.
---

# verify-best-books

## Interview summary (ground truth)

- **Surface.** Short-lived CLI. User entry is `uv run python main.py`, which calls `scripts.scraper.run_scraper()` and downloads every list and every book. No flags, no dry-run, no limit. Secondary surface is the library API (`Scraper`, `Libgen`) used by tests and this harness.
- **Run.** `uv sync --locked --group dev` then the commands below. Requires Python 3.13. Full product run creates `books/<slug>/…epub` and `logs/download_*.log` in the process cwd. `Scraper.books_dir` is hardcoded to `Path("books")`.
- **Drive.** Prefer this skill's helper (subprocess + production classes). Pytest is the offline gate matching CI (`.github/workflows/ci.yml` runs `pytest -m "not network and not slow"`). Do not drive a full `main.py` unless the task explicitly demands an end-to-end download proof and you have a disposable cwd.
- **Observe.** Helper writes under `.cursor/skills/verify-best-books/evidence/<run-id>/`. Capture exit codes, pytest summaries, JSON scrape/search payloads, and log paths when a full run is used.
- **Isolate.** Full `main.py` is not multi-instance safe against a shared `books/` tree. Refuse to run it in the user's real checkout cwd. For scrape-lists, the helper chdirs into a temp dir so accidental `books/`/`logs/` creation cannot touch the repo. Network mirrors (best-books.dev, Libgen) are shared globals and may flake.

## Launch

Prepare once per machine/session from the repo root:

```bash
uv sync --locked --group dev
```

Ready when doctor exits 0. There is no long-lived server to tear down. Each drive is one helper process.

Teardown is the Cleanup section. Never leave a full `main.py` run attached to the user's real `books/`.

## Doctor

```bash
uv run python .cursor/skills/verify-best-books/helpers/verify_best_books.py doctor
```

Require exit 0. Checks Python 3.13, imports of `scripts.scraper` / `scripts.libgen` / `scripts.utils`, `ruff check .`, and `mypy .`. Output and evidence path print to stdout; body is also at `evidence/<run-id>/doctor.txt`.

If doctor fails, stop. Fix the tree before any feature drive.

## Drive

Harness binary (always via uv):

```bash
uv run python .cursor/skills/verify-best-books/helpers/verify_best_books.py <command> [--run-id <id>]
```

Commands:

| Command | Network | What it proves |
| --- | --- | --- |
| `doctor` | no | toolchain + imports + lint/types |
| `offline` | no | CI test selection |
| `scrape-lists [--max-lists N]` | yes (best-books.dev) | production `Scraper._get_all_lists` + `_get_books_from_list` |
| `libgen-search [--title T] [--author A]` | yes (Libgen) | production `Libgen.search_title` |

Default offline proof path for agents:

```bash
uv run python .cursor/skills/verify-best-books/helpers/verify_best_books.py doctor --run-id <id>
uv run python .cursor/skills/verify-best-books/helpers/verify_best_books.py offline --run-id <id>
```

Live list scrape (one mapped feature, no downloads):

```bash
uv run python .cursor/skills/verify-best-books/helpers/verify_best_books.py scrape-lists --max-lists 1 --run-id <id>
```

Full user path (last resort only). Use a disposable directory as cwd, never the repo:

```bash
WORKDIR=$(mktemp -d /tmp/best-books-full-XXXX)
cd "$WORKDIR"
uv run --directory <repo-root> python <repo-root>/main.py
# expect books/ and logs/ under $WORKDIR; capture tree listing as evidence
```

Abort full runs with Ctrl+C; scraper handles KeyboardInterrupt and prints partial stats.

Feature recipes live in `features/`. Drive from that map. A proof that only runs offline tests does not cover live scrape or Libgen features listed there.

## Evidence

Directory: `.cursor/skills/verify-best-books/evidence/<run-id>/`

Typical artifacts:

- `doctor.txt`
- `pytest-offline.txt`
- `scrape-lists.json` / `scrape-lists.txt`
- `libgen-search.json` / `libgen-search.txt`

Proof standards:

- Exercise production classes (`Scraper`, `Libgen`) or the real CLI entry, not reimplemented parsers.
- Capture the command, exit code, and resulting artifact body.
- For mutations (downloads), list the created `.epub` paths and sizes after the action.
- Offline green does not prove Libgen or best-books.dev still work.
- Mocks belong only behind boundaries the product already isolates; this harness does not mock HTTP for live commands.

## Cleanup

- Helper temp dirs are removed automatically (`tempfile.TemporaryDirectory` in `scrape-lists`).
- Delete any disposable full-run workdir you created under `/tmp/best-books-full-*`.
- Do not delete `evidence/`.
- Do not delete the user's real repo `books/` or `logs/` unless this run created them and the user asked to reclaim space.
- No process-name kills. Only stop processes this run started (the helper exits on its own; a full `main.py` is stopped with Ctrl+C on that process).

## Helpers

Script: `.cursor/skills/verify-best-books/helpers/verify_best_books.py`

```bash
uv run python .cursor/skills/verify-best-books/helpers/verify_best_books.py doctor
uv run python .cursor/skills/verify-best-books/helpers/verify_best_books.py offline
uv run python .cursor/skills/verify-best-books/helpers/verify_best_books.py scrape-lists --max-lists 1
uv run python .cursor/skills/verify-best-books/helpers/verify_best_books.py libgen-search --title "Python Crash Course" --author "Eric Matthes"
```

Pass `--run-id <name>` to keep all artifacts for one proof in one folder.
